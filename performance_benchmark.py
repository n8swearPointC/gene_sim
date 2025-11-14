"""Performance benchmark script to determine maximum population size for batch runs.

This script tests different population sizes to help determine how many creatures
can be simulated within a time budget when running 25-50 simulations.

Target: Complete 25-50 runs in 30-40 minutes total
Goal: Find maximum population size that meets this constraint
"""

import time
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile
import shutil

from gene_sim.simulation import Simulation
from gene_sim.config import load_config


def benchmark_single_run(config_path: str, population_size: int, num_years: int) -> Dict:
    """Run a single simulation and measure its performance.
    
    Args:
        config_path: Path to the base configuration file
        population_size: Initial population size to test
        num_years: Number of years to simulate
        
    Returns:
        Dictionary with timing and population statistics
    """
    # Load base config
    import yaml
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f)
    
    # Modify parameters in raw config before loading
    raw_config['initial_population_size'] = population_size
    raw_config['years'] = num_years
    raw_config['mode'] = 'quiet'  # Suppress output for benchmarking
    
    # Save modified config to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_cfg:
        yaml.dump(raw_config, tmp_cfg)
        tmp_config_path = tmp_cfg.name
    
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Run simulation and measure time
        start_time = time.perf_counter()
        sim = Simulation(tmp_config_path, db_path=db_path)
        sim.run()
        end_time = time.perf_counter()
        
        runtime = end_time - start_time
        
        # Get final statistics
        conn = sim.db_conn.conn
        cursor = conn.cursor()
        
        # Get final generation number
        cursor.execute("SELECT MAX(generation_number) FROM generations")
        final_gen = cursor.fetchone()[0]
        
        # Get final population size
        cursor.execute("""
            SELECT COUNT(*) 
            FROM creatures 
            WHERE birth_generation <= ? AND death_generation IS NULL
        """, (final_gen,))
        final_pop = cursor.fetchone()[0]
        
        # Get total creatures created
        cursor.execute("SELECT COUNT(*) FROM creatures")
        total_creatures = cursor.fetchone()[0]
        
        return {
            'population_size': population_size,
            'num_years': num_years,
            'runtime_seconds': runtime,
            'final_generation': final_gen,
            'final_population': final_pop,
            'total_creatures_created': total_creatures
        }
        
    finally:
        # Clean up temporary files
        try:
            Path(db_path).unlink()
        except:
            pass
        try:
            Path(tmp_config_path).unlink()
        except:
            pass


def run_benchmark_suite(config_path: str, 
                       population_sizes: List[int],
                       num_years: int,
                       runs_per_size: int = 3) -> List[Dict]:
    """Run benchmarks for multiple population sizes.
    
    Args:
        config_path: Path to the base configuration file
        population_sizes: List of population sizes to test
        num_years: Number of years to simulate
        runs_per_size: Number of runs to average for each population size
        
    Returns:
        List of benchmark results
    """
    results = []
    
    print(f"\n{'='*80}")
    print(f"PERFORMANCE BENCHMARK - {num_years} Years Simulation")
    print(f"{'='*80}\n")
    
    for pop_size in population_sizes:
        print(f"Testing population size: {pop_size:,} creatures...")
        
        run_times = []
        run_results = []
        
        for run_num in range(runs_per_size):
            print(f"  Run {run_num + 1}/{runs_per_size}...", end=" ", flush=True)
            
            result = benchmark_single_run(config_path, pop_size, num_years)
            run_times.append(result['runtime_seconds'])
            run_results.append(result)
            
            print(f"{result['runtime_seconds']:.2f}s")
        
        # Calculate average runtime
        avg_runtime = sum(run_times) / len(run_times)
        min_runtime = min(run_times)
        max_runtime = max(run_times)
        
        # Use the last run's stats (they should be similar across runs)
        last_result = run_results[-1]
        
        summary = {
            'population_size': pop_size,
            'num_years': num_years,
            'avg_runtime_seconds': avg_runtime,
            'min_runtime_seconds': min_runtime,
            'max_runtime_seconds': max_runtime,
            'runs_tested': runs_per_size,
            'final_generation': last_result['final_generation'],
            'final_population': last_result['final_population'],
            'total_creatures_created': last_result['total_creatures_created']
        }
        
        results.append(summary)
        
        print(f"  Average: {avg_runtime:.2f}s (min: {min_runtime:.2f}s, max: {max_runtime:.2f}s)")
        print(f"  Final generation: {last_result['final_generation']}, Final population: {last_result['final_population']:,}")
        print()
    
    return results


def analyze_batch_capacity(results: List[Dict], 
                           num_runs: List[int] = [25, 50],
                           time_budgets_minutes: List[int] = [30, 40]):
    """Analyze benchmark results to determine maximum population sizes for batch runs.
    
    Args:
        results: List of benchmark results from run_benchmark_suite
        num_runs: List of batch run counts to analyze
        time_budgets_minutes: List of time budgets in minutes
    """
    print(f"\n{'='*80}")
    print(f"BATCH RUN CAPACITY ANALYSIS")
    print(f"{'='*80}\n")
    
    for num_batch_runs in num_runs:
        for time_budget_min in time_budgets_minutes:
            time_budget_sec = time_budget_min * 60
            
            print(f"\nTarget: {num_batch_runs} runs in {time_budget_min} minutes ({time_budget_sec:,} seconds)")
            print(f"{'-'*80}")
            
            # Time per run
            time_per_run = time_budget_sec / num_batch_runs
            print(f"Time budget per run: {time_per_run:.2f} seconds\n")
            
            print(f"{'Population':>12} | {'Avg Runtime':>12} | {'Est. Batch Time':>16} | {'Feasible?':>10}")
            print(f"{'-'*12}-+-{'-'*12}-+-{'-'*16}-+-{'-'*10}")
            
            feasible_populations = []
            
            for result in results:
                pop_size = result['population_size']
                avg_runtime = result['avg_runtime_seconds']
                batch_time = avg_runtime * num_batch_runs
                batch_time_min = batch_time / 60
                
                is_feasible = batch_time <= time_budget_sec
                feasibility = "✓ YES" if is_feasible else "✗ NO"
                
                if is_feasible:
                    feasible_populations.append(pop_size)
                
                print(f"{pop_size:>12,} | {avg_runtime:>10.2f}s | {batch_time_min:>13.2f} min | {feasibility:>10}")
            
            if feasible_populations:
                max_feasible = max(feasible_populations)
                print(f"\n*** Maximum feasible population: {max_feasible:,} creatures ***")
            else:
                print(f"\n*** No tested population sizes are feasible for this configuration ***")


def save_results(results: List[Dict], output_path: str = "benchmark_results.json"):
    """Save benchmark results to a JSON file.
    
    Args:
        results: List of benchmark results
        output_path: Path to save the results file
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")


def main():
    """Run the performance benchmark suite."""
    # Configuration
    config_path = "quick_test_config.yaml"
    
    # How many years to simulate for stabilization?
    # Let's start with a reasonable value - can be adjusted
    num_years = 50
    
    # Population sizes to test - start small and work up
    # Based on doc targets: 100 (5s/50gen), 1000 (60s/100gen), 10000 (600s/100gen)
    # Let's test a range to find the sweet spot
    population_sizes = [100, 250, 500, 750, 1000, 1500, 2000]
    
    # How many runs per population size for averaging
    runs_per_size = 3
    
    print("Starting performance benchmark...")
    print(f"Config file: {config_path}")
    print(f"Simulation duration: {num_years} years")
    print(f"Population sizes: {population_sizes}")
    print(f"Runs per size: {runs_per_size}")
    
    # Run benchmarks
    results = run_benchmark_suite(
        config_path=config_path,
        population_sizes=population_sizes,
        num_years=num_years,
        runs_per_size=runs_per_size
    )
    
    # Analyze for batch run capacity
    analyze_batch_capacity(
        results=results,
        num_runs=[25, 50],
        time_budgets_minutes=[30, 40]
    )
    
    # Save results
    save_results(results)
    
    print(f"\n{'='*80}")
    print("Benchmark complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
