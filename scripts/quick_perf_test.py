"""Quick performance test to determine appropriate benchmark parameters."""

import time
from gene_sim.simulation import Simulation

def quick_test(pop_size: int, years: int):
    """Run a quick test with given parameters."""
    import yaml
    import tempfile
    from pathlib import Path
    
    # Load base config
    with open('quick_test_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Modify for test
    config['initial_population_size'] = pop_size
    config['years'] = years
    config['mode'] = 'quiet'
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    # Use temp database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        print(f"\nTesting {pop_size} creatures for {years} years...")
        start = time.perf_counter()
        sim = Simulation(config_path, db_path=db_path)
        sim.run()
        end = time.perf_counter()
        
        runtime = end - start
        print(f"Runtime: {runtime:.2f} seconds ({runtime/60:.2f} minutes)")
        
        # Open connection to get stats (run() closes the connection)
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(generation) FROM generation_stats")
        final_gen = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM creatures")
        total_creatures = cursor.fetchone()[0]
        conn.close()
        
        print(f"Final generation/cycle: {final_gen}")
        print(f"Total creatures: {total_creatures:,}")
        
        return runtime
        
    finally:
        try:
            Path(config_path).unlink()
            Path(db_path).unlink()
        except:
            pass

# Test with small pop first
print("Quick performance baseline tests...")
print("="*60)

# Start with documented targets
print("\n1. Very small test (100 creatures, 2 years) - like quick_test_config")
quick_test(100, 2)

print("\n2. Small test (100 creatures, 5 years)")
quick_test(100, 5)

print("\n3. Medium test (250 creatures, 5 years)")
quick_test(250, 5)

print("\n" + "="*60)
print("Quick tests complete. Use these results to design full benchmark.")
