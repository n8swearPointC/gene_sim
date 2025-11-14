"""
Combined batch analysis script - creates comparison charts for kennels vs mills.

Usage:
    python batch_analysis_combined.py <kennel_dir> <mill_dir> <output_dir> [aggregate_method]
    
Example:
    python batch_analysis_combined.py run3/run3a_kennels run3/run3b_mills run3/combined_analysis mean
"""

import sys
from pathlib import Path

# Import from batch_analysis
from batch_analysis import create_combined_charts


def main():
    """Main function for combined analysis."""
    
    if len(sys.argv) < 4:
        print("Usage: python batch_analysis_combined.py <kennel_dir> <mill_dir> <output_dir> [aggregate_method]")
        print()
        print("Example:")
        print("  python batch_analysis_combined.py run3/run3a_kennels run3/run3b_mills run3/combined mean")
        print()
        print("Aggregate methods: mean (default), median, mean_ci, moving_avg")
        return
    
    kennel_dir = sys.argv[1]
    mill_dir = sys.argv[2]
    output_dir = sys.argv[3]
    aggregate_method = sys.argv[4] if len(sys.argv) > 4 else "mean"
    
    if aggregate_method not in ['mean', 'median', 'mean_ci', 'moving_avg']:
        print(f"Invalid aggregate method: {aggregate_method}")
        print("Valid options: mean, median, mean_ci, moving_avg")
        return
    
    print("="*80)
    print("COMBINED BATCH ANALYSIS - Kennels vs Mills")
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


if __name__ == "__main__":
    main()
