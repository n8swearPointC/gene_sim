"""
Unified batch analysis script for simulation analysis.

Supports three modes:
1. Individual batch analysis (single directory)
2. Combined comparison (kennels vs mills, total population)
3. Combined comparison (kennels vs mills, desired population only)

Usage:
    # Individual analysis
    python batch_analysis_unified.py --individual <directory> [--aggregate mean]
    
    # Combined total population comparison
    python batch_analysis_unified.py --combined <kennel_dir> <mill_dir> <output_dir> [--aggregate mean]
    
    # Combined desired population comparison
    python batch_analysis_unified.py --combined-desired <kennel_dir> <mill_dir> <output_dir> [--aggregate mean]
    
Examples:
    # Individual kennel analysis
    python batch_analysis_unified.py --individual run4/run4a_kennels
    
    # Combined comparison (total population)
    python batch_analysis_unified.py --combined run4/run4a_kennels run4/run4b_mills run4/combined
    
    # Combined comparison (desired population only)
    python batch_analysis_unified.py --combined-desired run4/run4a_kennels run4/run4b_mills run4/combined_desired
    
    # With specific aggregate method
    python batch_analysis_unified.py --individual run4/run4a_kennels --aggregate median
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
  # Individual analysis
  python batch_analysis_unified.py --individual run4/run4a_kennels
  
  # Combined total population
  python batch_analysis_unified.py --combined run4/run4a_kennels run4/run4b_mills run4/combined
  
  # Combined desired population
  python batch_analysis_unified.py --combined-desired run4/run4a_kennels run4/run4b_mills run4/combined_desired
  
  # With median aggregate
  python batch_analysis_unified.py --individual run4/run4a_kennels --aggregate median
        """
    )
    
    # Create mutually exclusive group for operation mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    mode_group.add_argument(
        '--individual', '-i',
        metavar='DIR',
        help='Individual batch analysis on a single directory'
    )
    
    mode_group.add_argument(
        '--combined', '-c',
        nargs=3,
        metavar=('KENNEL_DIR', 'MILL_DIR', 'OUTPUT_DIR'),
        help='Combined comparison (kennels vs mills, total population)'
    )
    
    mode_group.add_argument(
        '--combined-desired', '-cd',
        nargs=3,
        metavar=('KENNEL_DIR', 'MILL_DIR', 'OUTPUT_DIR'),
        help='Combined comparison (kennels vs mills, desired population only)'
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


def main():
    """Main function."""
    args = parse_arguments()
    
    if args.individual:
        run_individual_analysis(args.individual, args.aggregate)
    
    elif args.combined:
        kennel_dir, mill_dir, output_dir = args.combined
        run_combined_analysis(kennel_dir, mill_dir, output_dir, args.aggregate)
    
    elif args.combined_desired:
        kennel_dir, mill_dir, output_dir = args.combined_desired
        run_combined_desired_analysis(kennel_dir, mill_dir, output_dir, args.aggregate)


if __name__ == "__main__":
    main()
