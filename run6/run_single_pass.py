#!/usr/bin/env python3
"""Single-pass execution for Run 6 with monitoring enabled."""

import sys
from pathlib import Path
import yaml

# Add parent directory to path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

from gene_sim.simulation import Simulation


def run_single_simulation(config_path, run_name, seed, script_dir):
    """Run one simulation for testing."""
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override seed and ensure monitor mode
    config['seed'] = seed
    config['mode'] = 'monitor'
    
    # Create output directory in script directory
    output_dir = script_dir / "single_pass_results"
    output_dir.mkdir(exist_ok=True)
    
    # Create database path
    db_path = output_dir / f"{run_name}_seed{seed}.db"
    
    print("="*80)
    print(f"RUN 6 SINGLE-PASS TEST")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  - Population: {config['initial_population_size']}")
    print(f"  - Years: {config['years']}")
    print(f"  - Kennels: {config['breeders']['kennel_club']}")
    print(f"  - Mills: {config['breeders']['mill']}")
    print(f"  - Seed: {seed}")
    print(f"  - Output: {db_path}")
    print(f"\n{'='*80}\n")
    
    # Run simulation
    sim = Simulation(config, db_path=str(db_path))
    sim.run()
    
    return db_path


def main():
    """Run single configuration with monitoring."""
    # Get the directory where this script is located
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "run6_config.yaml"
    
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Use first seed from Batch A
    seed = 9000
    run_name = "run6_test"
    
    db_path = run_single_simulation(config_path, run_name, seed, script_dir)
    
    print("\n" + "="*80)
    print("SINGLE-PASS TEST COMPLETE")
    print("="*80)
    print(f"\nDatabase: {db_path}")
    print("\nNext steps:")
    print("  1. Examine database with SQLite browser")
    print("  2. Run analytics:")
    print(f"     python ../analytics/comprehensive_analytics.py {db_path}")
    print("  3. If results look good, run full batch:")
    print("     python run6_execute.py")
    print()


if __name__ == "__main__":
    main()
