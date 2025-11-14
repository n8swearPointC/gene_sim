"""
Unified batch analysis script for simulation analysis.

Supports two modes:
1. FULL ANALYSIS: Run all four analyses (individual + combined) on two directories
2. Individual modes: --individual, --combined, or --combined-desired (for specific needs)

Usage:
    # FULL ANALYSIS (recommended) - runs all 4 analyses automatically
    python batch_analysis_unified.py <dir1> <dir2> [--aggregate mean]
    
    # Individual analysis (single directory)
    python batch_analysis_unified.py --individual <directory> [--aggregate mean]
    
    # Combined total population comparison
    python batch_analysis_unified.py --combined <dir1> <dir2> <output_dir> [--aggregate mean]
    
    # Combined desired population comparison
    python batch_analysis_unified.py --combined-desired <dir1> <dir2> <output_dir> [--aggregate mean]
    
Examples:
    # Full analysis (all 4: individual dir1, individual dir2, combined, combined-desired)
    python batch_analysis_unified.py run5/run5a_kennels run5/run5b_mills
    
    # Full analysis with median aggregate
    python batch_analysis_unified.py run5/run5a_kennels run5/run5b_mills --aggregate median
    
    # Individual kennel analysis only
    python batch_analysis_unified.py --individual run4/run4a_kennels
"""

import sys
import argparse
from pathlib import Path

# Import functions from the existing batch_analysis module
from batch_analysis import (
    get_all_databases,
    run_comprehensive_analytics,
    create_comprehensive_charts,
    create_combined_charts,
    create_combined_charts_desired_only
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Unified batch analysis tool for simulation results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # FULL ANALYSIS (recommended) - automatically runs all 4 analyses
  python batch_analysis_unified.py run5/run5a_kennels run5/run5b_mills
  
  # Full analysis with median aggregate
  python batch_analysis_unified.py run5/run5a_kennels run5/run5b_mills --aggregate median
  
  # Individual analysis only
  python batch_analysis_unified.py --individual run4/run4a_kennels
  
  # Combined total population only
  python batch_analysis_unified.py --combined run4/run4a_kennels run4/run4b_mills run4/combined
  
  # Combined desired population only
  python batch_analysis_unified.py --combined-desired run4/run4a_kennels run4/run4b_mills run4/combined_desired
        """
    )
    
    # Create mutually exclusive group for operation mode
    mode_group = parser.add_mutually_exclusive_group(required=False)
    
    mode_group.add_argument(
        '--individual', '-i',
        metavar='DIR',
        help='Individual batch analysis on a single directory'
    )
    
    mode_group.add_argument(
        '--combined', '-c',
        nargs=3,
        metavar=('DIR1', 'DIR2', 'OUTPUT_DIR'),
        help='Combined comparison (total population only)'
    )
    
    mode_group.add_argument(
        '--combined-desired', '-cd',
        nargs=3,
        metavar=('DIR1', 'DIR2', 'OUTPUT_DIR'),
        help='Combined comparison (desired population only)'
    )
    
    # Positional arguments for full analysis mode
    parser.add_argument(
        'directories',
        nargs='*',
        help='Two directories for full analysis (individual + combined + combined-desired)'
    )
    
    parser.add_argument(
        '--aggregate', '-a',
        choices=['mean', 'median', 'mean_ci', 'moving_avg'],
        default='mean',
        help='Aggregate method for ensemble trends (default: mean)'
    )
    
    return parser.parse_args()


def run_individual_analysis(directory, aggregate_method):
    """Run individual batch analysis on a single directory."""
    
    print("="*80)
    print("BATCH ANALYSIS - Individual Directory")
    print("="*80)
    print(f"\nDirectory: {directory}")
    print(f"Aggregate method: {aggregate_method}")
    print()
    print("Aggregate options:")
    print("  mean       - Ensemble average of all runs (DEFAULT)")
    print("  median     - Median value (less affected by outliers)")
    print("  mean_ci    - Ensemble average with shaded ±1 standard deviation")
    print("  moving_avg - Smoothed 3-generation moving average")
    print()
    
    # Get all database files
    db_files = get_all_databases(directory)
    
    if not db_files:
        print("No simulation databases found!")
        print("Looking for files matching: simulation_run_*.db")
        return
    
    print(f"Found {len(db_files)} database files\n")
    
    # Create output directory for text analyses
    output_dir = Path(directory) / "batch_analysis"
    output_dir.mkdir(exist_ok=True)
    
    # Process each database
    print("Generating individual analysis reports...")
    for i, db_file in enumerate(db_files, 1):
        print(f"  [{i}/{len(db_files)}] {db_file.name}...", end=" ")
        try:
            output_path = run_comprehensive_analytics(db_file, output_dir)
            print(f"OK - Saved to {output_path.name}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\nText analyses saved to: {output_dir}")
    
    # Create comprehensive charts
    print("\nGenerating undesirable phenotype trend charts...")
    num_charts = create_comprehensive_charts(db_files, directory, aggregate_method)
    
    print("\n" + "="*80)
    print("BATCH ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  - Individual analyses: {output_dir}/")
    print(f"  - Trend charts: {num_charts} charts in {directory}/")
    print(f"    (undesirable_*_trends.png)")
    print()


def run_combined_analysis(kennel_dir, mill_dir, output_dir, aggregate_method):
    """Run combined analysis comparing kennels vs mills (total population)."""
    
    print("="*80)
    print("COMBINED BATCH ANALYSIS - Kennels vs Mills")
    print("TOTAL POPULATION")
    print("="*80)
    print(f"\nKennel directory: {kennel_dir}")
    print(f"Mill directory: {mill_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Aggregate method: {aggregate_method}")
    print()
    
    # Create combined charts
    num_charts = create_combined_charts(kennel_dir, mill_dir, output_dir, aggregate_method)
    
    print("\n" + "="*80)
    print("COMBINED ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  - Combined charts: {num_charts} charts in {output_dir}/")
    print(f"    (combined_*_trends.png)")
    print()


def run_combined_desired_analysis(kennel_dir, mill_dir, output_dir, aggregate_method):
    """Run combined analysis comparing kennels vs mills (desired population only)."""
    
    print("="*80)
    print("COMBINED BATCH ANALYSIS - Kennels vs Mills")
    print("DESIRED POPULATION ONLY")
    print("="*80)
    print(f"\nKennel directory: {kennel_dir}")
    print(f"Mill directory: {mill_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Aggregate method: {aggregate_method}")
    print()
    print("NOTE: Frequencies calculated ONLY among creatures with ALL desired phenotypes")
    print()
    
    # Create combined charts
    num_charts = create_combined_charts_desired_only(kennel_dir, mill_dir, output_dir, aggregate_method)
    
    print("\n" + "="*80)
    print("COMBINED ANALYSIS COMPLETE - Desired Population Only")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  - Combined charts: {num_charts} charts in {output_dir}/")
    print(f"    (combined_desired_*_trends.png)")
    print()


def run_full_analysis(dir1, dir2, aggregate_method):
    """Run complete analysis suite on two directories.
    
    Performs:
    1. Individual analysis on dir1
    2. Individual analysis on dir2
    3. Combined analysis (total population)
    4. Combined analysis (desired population only)
    """
    
    print("\n" + "="*80)
    print("FULL BATCH ANALYSIS SUITE")
    print("="*80)
    print(f"\nDirectory 1: {dir1}")
    print(f"Directory 2: {dir2}")
    print(f"Aggregate method: {aggregate_method}")
    print()
    print("This will run 4 analyses:")
    print("  1. Individual analysis on directory 1")
    print("  2. Individual analysis on directory 2")
    print("  3. Combined analysis (total population)")
    print("  4. Combined analysis (desired population only)")
    print()
    input("Press Enter to continue or Ctrl+C to cancel...")
    print()
    
    # Determine output directories from input paths
    # e.g., "run5/run5a_kennels" -> "run5" base directory
    path1 = Path(dir1)
    path2 = Path(dir2)
    
    # Use parent directory of dir1 as base (e.g., run5/)
    base_dir = path1.parent
    combined_dir = base_dir / "combined"
    combined_desired_dir = base_dir / "combined_desired"
    
    # Step 1: Individual analysis on dir1
    print("\n" + "#"*80)
    print("# STEP 1/4: Individual Analysis - Directory 1")
    print("#"*80 + "\n")
    run_individual_analysis(dir1, aggregate_method)
    
    # Step 2: Individual analysis on dir2
    print("\n" + "#"*80)
    print("# STEP 2/4: Individual Analysis - Directory 2")
    print("#"*80 + "\n")
    run_individual_analysis(dir2, aggregate_method)
    
    # Step 3: Combined analysis (total population)
    print("\n" + "#"*80)
    print("# STEP 3/4: Combined Analysis - Total Population")
    print("#"*80 + "\n")
    run_combined_analysis(dir1, dir2, str(combined_dir), aggregate_method)
    
    # Step 4: Combined analysis (desired population only)
    print("\n" + "#"*80)
    print("# STEP 4/4: Combined Analysis - Desired Population Only")
    print("#"*80 + "\n")
    run_combined_desired_analysis(dir1, dir2, str(combined_desired_dir), aggregate_method)
    
    # Final summary
    print("\n" + "="*80)
    print("FULL ANALYSIS SUITE COMPLETE")
    print("="*80)
    print(f"\nAll analyses completed successfully!")
    print(f"\nOutputs:")
    print(f"  - Individual dir1: {dir1}/ (9 charts + text reports)")
    print(f"  - Individual dir2: {dir2}/ (9 charts + text reports)")
    print(f"  - Combined total: {combined_dir}/ (9 charts)")
    print(f"  - Combined desired: {combined_desired_dir}/ (9 charts)")
    print(f"\nTotal: 36 charts generated")
    print()


def main():
    """Main function."""
    args = parse_arguments()
    
    # Check for full analysis mode (two positional arguments, no flags)
    if args.directories and not args.individual and not args.combined and not args.combined_desired:
        if len(args.directories) != 2:
            print("ERROR: Full analysis mode requires exactly 2 directories")
            print()
            print("Usage: python batch_analysis_unified.py <dir1> <dir2> [--aggregate method]")
            print()
            print("Example:")
            print("  python batch_analysis_unified.py run5/run5a_kennels run5/run5b_mills")
            sys.exit(1)
        
        dir1, dir2 = args.directories
        run_full_analysis(dir1, dir2, args.aggregate)
    
    elif args.individual:
        run_individual_analysis(args.individual, args.aggregate)
    
    elif args.combined:
        kennel_dir, mill_dir, output_dir = args.combined
        run_combined_analysis(kennel_dir, mill_dir, output_dir, args.aggregate)
    
    elif args.combined_desired:
        kennel_dir, mill_dir, output_dir = args.combined_desired
        run_combined_desired_analysis(kennel_dir, mill_dir, output_dir, args.aggregate)
    
    elif args.combined_desired:
        kennel_dir, mill_dir, output_dir = args.combined_desired
        run_combined_desired_analysis(kennel_dir, mill_dir, output_dir, args.aggregate)
    
    else:
        print("ERROR: No analysis mode specified")
        print()
        print("Usage:")
        print("  Full analysis:  python batch_analysis_unified.py <dir1> <dir2>")
        print("  Individual:     python batch_analysis_unified.py --individual <dir>")
        print("  Combined:       python batch_analysis_unified.py --combined <dir1> <dir2> <output>")
        print("  Combined-desired: python batch_analysis_unified.py --combined-desired <dir1> <dir2> <output>")
        print()
        print("Run with --help for more information")
        sys.exit(1)


if __name__ == "__main__":
    main()
