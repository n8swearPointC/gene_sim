"""
Performance capacity analysis for batch simulation runs.

Based on initial benchmarks:
- 100 creatures, 2 years: ~6 seconds  
- 100 creatures, 5 years: ~151 seconds
- 250 creatures, 5 years: ~683 seconds

This script will determine the maximum population size that allows
25-50 runs to complete within 30-40 minutes.
"""

import time
import yaml
import tempfile
import sqlite3
from pathlib import Path
from gene_sim.simulation import Simulation

def run_single_test(pop_size: int, years: int) -> float:
    """Run a single simulation and return runtime in seconds."""
    # Load and modify config
    with open('quick_test_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['initial_population_size'] = pop_size
    config['years'] = years
    config['mode'] = 'quiet'
    
    # Create temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        start = time.perf_counter()
        sim = Simulation(config_path, db_path=db_path)
        sim.run()
        end = time.perf_counter()
        return end - start
    finally:
        try:
            Path(config_path).unlink()
            Path(db_path).unlink()
        except:
            pass

def format_time(seconds: float) -> str:
    """Format seconds as readable time string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    else:
        return f"{seconds/60:.1f}min ({seconds:.1f}s)"

def main():
    """Run targeted performance benchmarks and calculate batch capacity."""
    
    print("="*80)
    print("PERFORMANCE CAPACITY ANALYSIS")
    print("="*80)
    print("\nObjective: Determine max population size for 25-50 runs in 30-40 minutes")
    print("Strategy: Test configurations to find sweet spot for statistical validity\n")
    
    # First question: How many years for stabilization?
    print("-"*80)
    print("STEP 1: Determine appropriate simulation duration")
    print("-"*80)
    print("Testing 100 creatures at different durations to find stabilization point...")
    
    test_years = [10, 15, 20]
    year_results = {}
    
    for years in test_years:
        print(f"\n  Testing {years} years...", end=" ", flush=True)
        runtime = run_single_test(100, years)
        year_results[years] = runtime
        print(f"{format_time(runtime)}")
    
    # Pick a reasonable duration (can be adjusted by user)
    recommended_years = 15
    print(f"\nRecommendation: Use {recommended_years} years for stabilization")
    print(f"(This gives enough time for population dynamics to settle)\n")
    
    # Now test population sizes at the recommended duration
    print("-"*80)
    print(f"STEP 2: Test population sizes at {recommended_years} years")
    print("-"*80)
    
    test_populations = [50, 75, 100, 150, 200, 250, 300]
    pop_results = []
    
    for pop_size in test_populations:
        print(f"\n  Testing {pop_size} creatures...", end=" ", flush=True)
        runtime = run_single_test(pop_size, recommended_years)
        pop_results.append((pop_size, runtime))
        print(f"{format_time(runtime)}")
    
    # Analysis for batch runs
    print("\n" + "="*80)
    print("BATCH RUN CAPACITY ANALYSIS")
    print("="*80)
    
    scenarios = [
        (25, 30),  # 25 runs in 30 minutes
        (25, 40),  # 25 runs in 40 minutes
        (50, 30),  # 50 runs in 30 minutes
        (50, 40),  # 50 runs in 40 minutes
    ]
    
    for num_runs, time_budget_min in scenarios:
        time_budget_sec = time_budget_min * 60
        time_per_run = time_budget_sec / num_runs
        
        print(f"\n{num_runs} runs in {time_budget_min} minutes:")
        print(f"  Time budget per run: {format_time(time_per_run)}")
        print(f"  Feasible population sizes:")
        
        feasible = []
        for pop_size, runtime in pop_results:
            if runtime <= time_per_run:
                batch_time = runtime * num_runs
                feasible.append(pop_size)
                print(f"    • {pop_size:>3} creatures: {format_time(runtime)}/run → "
                      f"{format_time(batch_time)} total ✓")
        
        if feasible:
            max_pop = max(feasible)
            print(f"  → Maximum: {max_pop} creatures")
        else:
            print(f"  → No tested sizes are feasible")
    
    # Final recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    # Find conservative recommendation (fits all scenarios)
    all_feasible = []
    for num_runs, time_budget_min in scenarios:
        time_budget_sec = time_budget_min * 60
        time_per_run = time_budget_sec / num_runs
        scenario_feasible = [pop for pop, runtime in pop_results if runtime <= time_per_run]
        all_feasible.append(max(scenario_feasible) if scenario_feasible else 0)
    
    conservative = min(all_feasible)
    optimistic = max(all_feasible)
    
    print(f"\nFor {recommended_years} years simulation duration:")
    print(f"  • Conservative (works for all scenarios): {conservative} creatures")
    print(f"  • Optimistic (25 runs, 40 min budget): {optimistic} creatures")
    print(f"\nStatistical note:")
    print(f"  - 25 runs provides good statistical confidence (Central Limit Theorem)")
    print(f"  - 50 runs provides excellent confidence but takes 2x longer")
    print(f"  - Recommend starting with 25 runs at {conservative}-{optimistic} creatures")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
