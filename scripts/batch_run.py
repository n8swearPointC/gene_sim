"""
Batch simulation runner for statistical analysis.

Runs the same simulation multiple times with different random seeds
to enable statistical analysis of results.
"""

import argparse
import time
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import tempfile
import sqlite3

from gene_sim.simulation import Simulation


def run_batch_simulations(
    config_path: str,
    num_runs: int,
    base_seed: int = None,
    output_dir: str = None,
    pop_size: int = None,
    years: int = None,
    save_config_copy: bool = True
) -> List[Dict]:
    """
    Run multiple simulations with different seeds.
    
    Args:
        config_path: Path to base configuration file
        num_runs: Number of simulation runs to execute
        base_seed: Starting seed value (will increment for each run)
        output_dir: Directory to save simulation databases (default: batch_results_TIMESTAMP)
        pop_size: Override population size from config (optional)
        years: Override years from config (optional)
        save_config_copy: Save a copy of the config used for this batch (default: True)
        
    Returns:
        List of result dictionaries with metadata for each run
    """
    # Setup output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"batch_results_{timestamp}"
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load base config
    with open(config_path, 'r') as f:
        base_config = yaml.safe_load(f)
    
    # Override if specified
    if pop_size is not None:
        base_config['initial_population_size'] = pop_size
    if years is not None:
        base_config['years'] = years
    
    # Determine base seed
    if base_seed is None:
        base_seed = base_config.get('seed', 42)
    
    # Save a copy of the config used for this batch
    if save_config_copy:
        config_copy_path = output_path / "batch_config.yaml"
        with open(config_copy_path, 'w') as f:
            yaml.dump(base_config, f)
    
    # Results tracking
    results = []
    start_time = time.time()
    
    print("="*80)
    print(f"BATCH SIMULATION RUN")
    print("="*80)
    print(f"Configuration: {config_path}")
    print(f"Population size: {base_config['initial_population_size']}")
    print(f"Duration: {base_config['years']} years")
    print(f"Number of runs: {num_runs}")
    print(f"Base seed: {base_seed}")
    print(f"Output directory: {output_dir}")
    print("="*80)
    print()
    
    for run_num in range(1, num_runs + 1):
        run_seed = base_seed + run_num - 1
        
        print(f"Run {run_num}/{num_runs} (seed={run_seed})...", end=" ", flush=True)
        
        # Modify config for this run
        run_config = base_config.copy()
        run_config['seed'] = run_seed
        run_config['mode'] = 'quiet'  # Suppress output during batch
        
        # Save modified config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(run_config, f)
            tmp_config_path = f.name
        
        # Create database path
        db_path = output_path / f"simulation_run_{run_num:03d}_seed_{run_seed}.db"
        
        try:
            # Run simulation
            run_start = time.perf_counter()
            sim = Simulation(tmp_config_path, db_path=str(db_path))
            sim.run()
            run_end = time.perf_counter()
            run_time = run_end - run_start
            
            # Collect statistics
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT MAX(generation) FROM generation_stats")
            final_generation = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM creatures")
            total_creatures = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT population_size 
                FROM generation_stats 
                WHERE generation = ?
            """, (final_generation,))
            final_pop_size = cursor.fetchone()[0]
            
            conn.close()
            
            # Record results
            result = {
                'run_number': run_num,
                'seed': run_seed,
                'runtime_seconds': run_time,
                'final_generation': final_generation,
                'final_population_size': final_pop_size,
                'total_creatures_created': total_creatures,
                'database_path': str(db_path)
            }
            results.append(result)
            
            print(f"{run_time:.1f}s | Gen: {final_generation} | Pop: {final_pop_size:,} | Total: {total_creatures:,}")
            
        except Exception as e:
            print(f"FAILED: {e}")
            result = {
                'run_number': run_num,
                'seed': run_seed,
                'error': str(e)
            }
            results.append(result)
        
        finally:
            # Cleanup temp config
            try:
                Path(tmp_config_path).unlink()
            except:
                pass
    
    total_time = time.time() - start_time
    
    # Summary statistics
    print()
    print("="*80)
    print("BATCH RUN SUMMARY")
    print("="*80)
    
    successful_runs = [r for r in results if 'error' not in r]
    failed_runs = [r for r in results if 'error' in r]
    
    print(f"Total runs: {num_runs}")
    print(f"Successful: {len(successful_runs)}")
    print(f"Failed: {len(failed_runs)}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    
    if successful_runs:
        avg_runtime = sum(r['runtime_seconds'] for r in successful_runs) / len(successful_runs)
        min_runtime = min(r['runtime_seconds'] for r in successful_runs)
        max_runtime = max(r['runtime_seconds'] for r in successful_runs)
        
        avg_total_creatures = sum(r['total_creatures_created'] for r in successful_runs) / len(successful_runs)
        avg_final_pop = sum(r['final_population_size'] for r in successful_runs) / len(successful_runs)
        
        print()
        print("Runtime statistics:")
        print(f"  Average: {avg_runtime:.1f}s")
        print(f"  Min: {min_runtime:.1f}s")
        print(f"  Max: {max_runtime:.1f}s")
        print()
        print("Population statistics:")
        print(f"  Average final population: {avg_final_pop:,.0f}")
        print(f"  Average total creatures: {avg_total_creatures:,.0f}")
    
    # Save results metadata
    metadata_path = output_path / "batch_results.json"
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'config_path': config_path,
        'base_config': base_config,
        'num_runs': num_runs,
        'base_seed': base_seed,
        'total_time_seconds': total_time,
        'results': results
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Create README
    readme_path = output_path / "README.md"
    create_batch_readme(
        readme_path=readme_path,
        config=base_config,
        num_runs=num_runs,
        base_seed=base_seed,
        results=results,
        total_time=total_time
    )
    
    print()
    print(f"Results metadata saved to: {metadata_path}")
    print(f"README saved to: {readme_path}")
    print(f"Database files saved in: {output_dir}")
    print("="*80)
    
    return results


def create_batch_readme(
    readme_path: Path,
    config: dict,
    num_runs: int,
    base_seed: int,
    results: List[Dict],
    total_time: float
):
    """Create a README file describing the batch run."""
    
    successful_runs = [r for r in results if 'error' not in r]
    failed_runs = [r for r in results if 'error' in r]
    
    # Calculate statistics
    if successful_runs:
        avg_runtime = sum(r['runtime_seconds'] for r in successful_runs) / len(successful_runs)
        min_runtime = min(r['runtime_seconds'] for r in successful_runs)
        max_runtime = max(r['runtime_seconds'] for r in successful_runs)
        avg_total_creatures = sum(r['total_creatures_created'] for r in successful_runs) / len(successful_runs)
        avg_final_pop = sum(r['final_population_size'] for r in successful_runs) / len(successful_runs)
        avg_final_gen = sum(r['final_generation'] for r in successful_runs) / len(successful_runs)
    else:
        avg_runtime = min_runtime = max_runtime = 0
        avg_total_creatures = avg_final_pop = avg_final_gen = 0
    
    # Get breeder info
    breeders = config.get('breeders', {})
    kennel_count = breeders.get('kennel_club', 0)
    mill_count = breeders.get('mill', 0)
    random_count = breeders.get('random', 0)
    inbreeding_avoid = breeders.get('inbreeding_avoidance', 0)
    
    readme_content = f"""# Batch Simulation Run

## Run Information

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Configuration

- **Initial Population Size**: {config.get('initial_population_size')} creatures
- **Simulation Duration**: {config.get('years')} years
- **Number of Runs**: {num_runs}
- **Base Seed**: {base_seed}
- **Seed Range**: {base_seed} to {base_seed + num_runs - 1}

### Breeder Distribution

- Kennel Club Breeders: {kennel_count}
- Mill Breeders: {mill_count}
- Random Breeders: {random_count}
- Inbreeding Avoidance Breeders: {inbreeding_avoid}
- **Total Breeders**: {kennel_count + mill_count + random_count + inbreeding_avoid}

### Traits

"""
    
    # Add trait information
    for trait in config.get('traits', []):
        readme_content += f"- **{trait['name']}** (trait_id: {trait['trait_id']})\n"
        readme_content += f"  - Type: {trait['trait_type']}\n"
        readme_content += f"  - Genotypes:\n"
        for genotype in trait.get('genotypes', []):
            readme_content += f"    - {genotype['genotype']} -> {genotype['phenotype']} (initial freq: {genotype['initial_freq']})\n"
        readme_content += "\n"
    
    # Add target/undesirable phenotypes if present
    if config.get('target_phenotypes'):
        readme_content += "### Target Phenotypes\n\n"
        for target in config['target_phenotypes']:
            readme_content += f"- Trait {target['trait_id']}: {target['phenotype']}\n"
        readme_content += "\n"
    
    if config.get('undesirable_phenotypes'):
        readme_content += "### Undesirable Phenotypes\n\n"
        for undesirable in config['undesirable_phenotypes']:
            readme_content += f"- Trait {undesirable['trait_id']}: {undesirable['phenotype']}\n"
        readme_content += "\n"
    
    if config.get('genotype_preferences'):
        readme_content += "### Genotype Preferences (Kennel Club)\n\n"
        for pref in config['genotype_preferences']:
            readme_content += f"- **Trait {pref['trait_id']}**:\n"
            readme_content += f"  - Optimal: {', '.join(pref.get('optimal', []))}\n"
            readme_content += f"  - Acceptable: {', '.join(pref.get('acceptable', []))}\n"
            readme_content += f"  - Undesirable: {', '.join(pref.get('undesirable', []))}\n"
        readme_content += "\n"
    
    readme_content += f"""## Results Summary

### Execution Statistics

- **Total Runs**: {num_runs}
- **Successful**: {len(successful_runs)}
- **Failed**: {len(failed_runs)}
- **Total Execution Time**: {total_time:.1f} seconds ({total_time/60:.2f} minutes)

### Runtime Statistics (per run)

- **Average**: {avg_runtime:.1f} seconds
- **Minimum**: {min_runtime:.1f} seconds
- **Maximum**: {max_runtime:.1f} seconds

### Population Statistics (averages across successful runs)

- **Average Final Generation/Cycle**: {avg_final_gen:.0f}
- **Average Final Population Size**: {avg_final_pop:,.0f} creatures
- **Average Total Creatures Created**: {avg_total_creatures:,.0f} creatures

## Files in This Directory

- `batch_config.yaml` - Configuration file used for this batch run
- `batch_results.json` - Detailed results metadata in JSON format
- `simulation_run_NNN_seed_SSSS.db` - SQLite database for each simulation run
  - NNN = run number (001, 002, etc.)
  - SSSS = random seed used for that run

## Analyzing Results

You can analyze individual runs using the analytics scripts in the parent directory:

```powershell
# Comprehensive analytics for a specific run
python ../analytics/comprehensive_analytics.py simulation_run_001_seed_{base_seed}.db

# Chart phenotype frequencies across generations
python ../analytics/chart_phenotype.py simulation_run_001_seed_{base_seed}.db

# Analyze genotype frequencies
python ../analytics/analyze_genotype_frequencies.py simulation_run_001_seed_{base_seed}.db
```

## Database Schema

Each SQLite database contains the following tables:

- `simulations` - Simulation metadata
- `traits` - Trait definitions
- `genotypes` - Genotype-phenotype mappings
- `breeders` - Breeder information
- `creatures` - All creatures created during simulation
- `creature_genotypes` - Genotypes for each creature
- `creature_ownership_history` - Ownership changes over time
- `generation_stats` - Population statistics per generation
- `generation_genotype_frequencies` - Genotype frequencies per generation per trait
- `generation_trait_stats` - Aggregate trait statistics per generation

## Notes

This batch run was designed to provide statistical confidence through multiple replications
with different random seeds. Each run represents an independent simulation of the same
breeding scenario, allowing analysis of variability and trends across runs.

For questions about the simulation methodology, see the main project documentation.
"""
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)


def main():
    """Command-line interface for batch simulation runner."""
    parser = argparse.ArgumentParser(
        description="Run multiple simulations for statistical analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 30 simulations with default config
  python batch_run.py -n 30
  
  # Run 50 simulations with custom population and duration
  python batch_run.py -n 50 -p 100 -y 3
  
  # Run with specific base seed and output directory
  python batch_run.py -n 25 -s 12345 -o my_batch_results
  
  # Quick test with recommended config
  python batch_run.py -n 30 -p 100 -y 3
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='quick_test_config.yaml',
        help='Path to configuration file (default: quick_test_config.yaml)'
    )
    parser.add_argument(
        '-n', '--num-runs',
        type=int,
        required=True,
        help='Number of simulation runs to execute'
    )
    parser.add_argument(
        '-s', '--seed',
        type=int,
        help='Base seed value (default: from config or 42)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory for results (default: batch_results_TIMESTAMP)'
    )
    parser.add_argument(
        '-p', '--population',
        type=int,
        help='Override initial population size'
    )
    parser.add_argument(
        '-y', '--years',
        type=int,
        help='Override simulation duration in years'
    )
    
    args = parser.parse_args()
    
    run_batch_simulations(
        config_path=args.config,
        num_runs=args.num_runs,
        base_seed=args.seed,
        output_dir=args.output,
        pop_size=args.population,
        years=args.years
    )


if __name__ == "__main__":
    # Quick test mode when run directly
    import sys
    if len(sys.argv) == 1:
        print("Quick test mode - running 3 simulations with 10 creatures for 2 years")
        run_batch_simulations(
            config_path='quick_test_config.yaml',
            num_runs=3,
            base_seed=100,
            pop_size=10,
            years=2
        )
    else:
        main()
