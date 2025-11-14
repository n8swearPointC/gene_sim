#!/usr/bin/env python
"""
Run 6 Execution Script - Kennel vs Mill Breeding Comparison (Extended Timeframe)

This script executes two batches:
- Batch A: 15 runs with 19 kennels, 1 mill (95% kennels)
- Batch B: 15 runs with 1 kennel, 19 mills (95% mills)

Configuration:
- 200 creatures, 20 years (same as run4)
- TOTAL BREEDERS: 20 (95/5 split)
- 3 desirable traits (1 dominant, 2 recessive) - all rare in founders
- 12 undesirable traits (3 recessive, 6 dominant) with various frequencies
"""

import subprocess
import sys
from pathlib import Path


def run_batch(config_path, output_dir, num_runs, kennels, mills, base_seed):
    """
    Execute a batch of simulations with specified breeder configuration.
    
    Args:
        config_path: Path to configuration file
        output_dir: Output directory for results
        num_runs: Number of simulation runs
        kennels: Number of kennel club breeders
        mills: Number of mill breeders
        base_seed: Starting seed value
    """
    print(f"\n{'='*80}")
    print(f"BATCH: {output_dir}")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  - Kennel Club Breeders: {kennels}")
    print(f"  - Mill Breeders: {mills}")
    print(f"  - Runs: {num_runs}")
    print(f"  - Base Seed: {base_seed}")
    print(f"  - Output: {output_dir}")
    print(f"{'='*80}\n")
    
    # Modify config to set breeder counts
    import yaml
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update breeder configuration
    config['breeders']['kennel_club'] = kennels
    config['breeders']['mill'] = mills
    
    # Save modified config
    modified_config_path = Path(output_dir) / "batch_config.yaml"
    Path(output_dir).mkdir(exist_ok=True)
    
    with open(modified_config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Run batch_run.py with the modified config
    cmd = [
        sys.executable,
        "../scripts/batch_run.py",
        "-c", str(modified_config_path),
        "-n", str(num_runs),
        "-s", str(base_seed),
        "-o", output_dir
    ]
    
    print(f"Executing: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n⚠️  WARNING: Batch exited with code {result.returncode}")
        return False
    
    print(f"\n✓ Batch complete: {output_dir}\n")
    return True


def main():
    """Execute both batches for Run 6."""
    config_path = "run6_config.yaml"
    
    if not Path(config_path).exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("RUN 6: KENNEL VS MILL BREEDING COMPARISON (EXTENDED TIMEFRAME)")
    print("="*80)
    print("\nThis will execute 30 total simulations (2 batches of 15 runs each)")
    print("Configuration: 200 creatures, 20 years, 20 total breeders")
    print("(Same as Run 4 with different random seeds for validation)")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    
    # Batch A: Kennel-dominated (19 kennels, 1 mill = 95% kennels)
    success_a = run_batch(
        config_path=config_path,
        output_dir="run6a_kennels",
        num_runs=15,
        kennels=19,
        mills=1,
        base_seed=9000
    )
    
    if not success_a:
        print("\n⚠️  Batch A had issues, but continuing to Batch B...")
    
    # Batch B: Mill-dominated (1 kennel, 19 mills = 95% mills)
    success_b = run_batch(
        config_path=config_path,
        output_dir="run6b_mills",
        num_runs=15,
        kennels=1,
        mills=19,
        base_seed=10000
    )
    
    # Summary
    print("\n" + "="*80)
    print("RUN 6 COMPLETE")
    print("="*80)
    
    if success_a and success_b:
        print("\n✓ All batches completed successfully!")
    else:
        print("\n⚠️  Some batches had issues. Check output above.")
    
    print("\nResults:")
    print("  - Batch A (Kennel-dominated): run6a_kennels/")
    print("  - Batch B (Mill-dominated):   run6b_mills/")
    print("\nNext steps:")
    print("  1. Analyze individual batches:")
    print("     cd ..")
    print("     python scripts/batch_analysis.py run6/run6a_kennels")
    print("     python scripts/batch_analysis.py run6/run6b_mills")
    print("  2. Compare kennel vs mill results across batches")
    print()


if __name__ == "__main__":
    main()
