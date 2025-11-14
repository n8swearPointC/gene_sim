#!/usr/bin/env python3
"""
Single-pass execution of run5 configuration with monitoring enabled.
Runs a single simulation with a fixed seed for quick testing.
"""

import sys
from pathlib import Path
import yaml
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gene_sim.simulation import Simulation
from gene_sim.config import load_config


def run_single_simulation(config_path: Path, run_name: str, seed: int = 42):
    """Run a single simulation with monitoring enabled."""
    
    print(f"\n{'='*80}")
    print(f"Running: {run_name}")
    print(f"Config: {config_path.name}")
    print(f"Seed: {seed}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Load config to modify seed and mode
    config = load_config(str(config_path))
    
    # Override seed and ensure monitoring is on
    config.seed = seed
    config.mode = 'monitor'
    
    # Create output filename
    output_dir = config_path.parent / "single_pass_results"
    output_dir.mkdir(exist_ok=True)
    
    db_filename = f"{run_name}_seed_{seed}.db"
    db_path = output_dir / db_filename
    
    # Save modified config to temporary file
    temp_config_dict = config.raw_config.copy()
    temp_config_dict['seed'] = seed
    temp_config_dict['mode'] = 'monitor'
    
    temp_config_path = output_dir / f"temp_config_{run_name}.yaml"
    with open(temp_config_path, 'w') as f:
        yaml.dump(temp_config_dict, f, default_flow_style=False)
    
    # Run simulation with temp config
    print(f"Output database: {db_path}\n")
    
    sim = Simulation(str(temp_config_path), str(db_path))
    sim.run()
    
    print(f"\n{'='*80}")
    print(f"Completed: {run_name}")
    print(f"Database: {db_path}")
    print(f"{'='*80}\n")
    
    return db_path


def main():
    """Run single configuration with monitoring enabled."""
    
    run5_dir = Path(__file__).parent
    config_path = run5_dir / "run5_config.yaml"
    
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("RUN5 SINGLE-PASS EXECUTION WITH MONITORING")
    print("="*80)
    print(f"\nConfiguration: 200 creatures, 6 years, 20 breeders (19 kennels, 1 mill)")
    print(f"Config file: {config_path}")
    
    try:
        db_path = run_single_simulation(config_path, "run5_single_pass", seed=7000)
        
        print("\n" + "="*80)
        print("EXECUTION COMPLETE")
        print("="*80)
        print(f"\nDatabase: {db_path}")
        print("\nNext steps:")
        print("  - Analyze results using analytics scripts")
        print("  - Run full batch with run5_execute.py")
        print()
        
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"ERROR: {str(e)}")
        print(f"{'!'*80}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
