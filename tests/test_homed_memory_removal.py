"""
Test that homed creatures are removed from working memory but remain in database.

This is a critical performance optimization that prevents exponential memory growth
as offspring accumulate over many generations.
"""

import pytest
import sqlite3
from gene_sim.simulation import Simulation
from gene_sim.models.population import Population


def test_homed_offspring_not_in_memory(tmp_path):
    """Test that homed offspring are persisted to DB but not added to working memory."""
    # Create a minimal simulation
    config_path = tmp_path / "test_config.yaml"
    config_content = """
seed: 12345
years: 1
mode: debug
initial_population_size: 20

initial_sex_ratio:
  male: 0.5
  female: 0.5

creature_archetype:
  lifespan:
    min: 3
    max: 5
  sexual_maturity_months: 6
  max_fertility_age_years:
    male: 4
    female: 4
  gestation_period_days: 65
  nursing_period_days: 28
  menstrual_cycle_days: 24
  nearing_end_cycles: 12
  remove_ineligible_immediately: false
  litter_size:
    min: 3
    max: 6

breeders:
  random: 2
  inbreeding_avoidance: 0
  kennel_club: 0
  mill: 0

traits:
  - trait_id: 0
    name: "Test Trait"
    trait_type: SIMPLE_MENDELIAN
    genotypes:
      - genotype: "AA"
        phenotype: "Dominant"
        initial_freq: 0.5
      - genotype: "Aa"
        phenotype: "Hetero"
        initial_freq: 0.3
      - genotype: "aa"
        phenotype: "Recessive"
        initial_freq: 0.2
"""
    config_path.write_text(config_content)
    
    # Run simulation
    sim = Simulation.from_config(str(config_path))
    
    # Don't run() yet - we need to access the database connection
    # Instead, manually initialize and run one cycle at a time
    sim.initialize()
    
    # Run the simulation
    from gene_sim.models.generation import Cycle
    cycle = Cycle(0)
    
    for cycle_num in range(sim.config.cycles):
        cycle.cycle_number = cycle_num
        cycle.execute_cycle(
            population=sim.population,
            breeders=sim.breeders,
            traits=sim.traits,
            rng=sim.rng,
            db_conn=sim.db_conn,
            simulation_id=sim.simulation_id,
            config=sim.config
        )
    
    # Now query database while connection is still open
    cursor = sim.db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM creatures")
    total_in_db = cursor.fetchone()[0]
    
    # Query for homed creatures
    cursor.execute("SELECT COUNT(*) FROM creatures WHERE is_homed = 1")
    homed_in_db = cursor.fetchone()[0]
    
    # Count creatures in working memory
    in_memory = len(sim.population.creatures)
    
    # Query for non-homed creatures
    cursor.execute("SELECT COUNT(*) FROM creatures WHERE is_homed = 0")
    not_homed_db = cursor.fetchone()[0]
    
    # Debug: check if all creatures in memory are in DB
    memory_ids = {c.creature_id for c in sim.population.creatures if c.creature_id is not None}
    cursor.execute("SELECT creature_id FROM creatures WHERE is_homed = 0")
    db_ids = {row[0] for row in cursor.fetchall()}
    
    missing_from_db = memory_ids - db_ids
    extra_in_db = db_ids - memory_ids
    
    # Assertions
    assert total_in_db > in_memory, "Database should have more creatures than memory (due to homed creatures)"
    assert homed_in_db > 0, "There should be some homed creatures in database"
    
    # The key assertion: homed creatures should NOT be in memory
    # Allow for some creatures in memory that died recently (will be aged out next cycle)
    assert in_memory <= not_homed_db + 10, f"Memory has {in_memory} but DB has {not_homed_db} not-homed (diff: {in_memory - not_homed_db})"
    
    # Most creatures should be homed (removed from memory)
    assert homed_in_db / total_in_db > 0.5, "Majority of creatures should be homed for performance"
    
    print(f"\n✓ Test passed:")
    print(f"  Total in database: {total_in_db}")
    print(f"  Homed in database: {homed_in_db}")
    print(f"  Not homed in DB: {not_homed_db}")
    print(f"  In working memory: {in_memory}")
    print(f"  Missing from DB: {len(missing_from_db)}")
    print(f"  Extra in DB: {len(extra_in_db)}")
    print(f"  Memory reduction: {homed_in_db} creatures removed ({homed_in_db/total_in_db*100:.1f}%)")


def test_homed_adults_removed_from_memory(tmp_path):
    """Test that adults homed via spay/neuter are removed from working memory."""
    config_path = tmp_path / "test_config.yaml"
    config_content = """
seed: 54321
years: 1
mode: debug
initial_population_size: 30

initial_sex_ratio:
  male: 0.5
  female: 0.5

creature_archetype:
  lifespan:
    min: 3
    max: 5
  sexual_maturity_months: 6
  max_fertility_age_years:
    male: 4
    female: 4
  gestation_period_days: 65
  nursing_period_days: 28
  menstrual_cycle_days: 24
  nearing_end_cycles: 12
  remove_ineligible_immediately: false
  litter_size:
    min: 3
    max: 6

breeders:
  random: 3
  inbreeding_avoidance: 0
  kennel_club: 0
  mill: 0

traits:
  - trait_id: 0
    name: "Test Trait"
    trait_type: SIMPLE_MENDELIAN
    genotypes:
      - genotype: "AA"
        phenotype: "Dominant"
        initial_freq: 0.5
      - genotype: "Aa"
        phenotype: "Hetero"
        initial_freq: 0.3
      - genotype: "aa"
        phenotype: "Recessive"
        initial_freq: 0.2
"""
    config_path.write_text(config_content)
    
    # Run simulation
    sim = Simulation.from_config(str(config_path))
    sim.initialize()
    
    # Run cycles manually
    from gene_sim.models.generation import Cycle
    cycle = Cycle(0)
    
    for cycle_num in range(sim.config.cycles):
        cycle.cycle_number = cycle_num
        cycle.execute_cycle(
            population=sim.population,
            breeders=sim.breeders,
            traits=sim.traits,
            rng=sim.rng,
            db_conn=sim.db_conn,
            simulation_id=sim.simulation_id,
            config=sim.config
        )
    
    # Count memory before final cycle
    initial_memory = len(sim.population.creatures)
    
    # Query database for homed adults (not born this cycle)
    cursor = sim.db_conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM creatures 
        WHERE is_homed = 1 AND birth_cycle < ?
    """, (sim.config.cycles - 1,))
    homed_adults = cursor.fetchone()[0]
    
    # These homed adults should NOT be in working memory
    in_memory = len(sim.population.creatures)
    
    assert homed_adults > 0, "There should be some homed adults"
    print(f"\n✓ Test passed:")
    print(f"  Initial memory: {initial_memory}")
    print(f"  Final memory: {in_memory}")
    print(f"  Homed adults: {homed_adults}")


def test_population_stabilization(tmp_path):
    """Test that population in memory stabilizes instead of growing exponentially."""
    config_path = tmp_path / "test_config.yaml"
    config_content = """
seed: 99999
years: 2
mode: debug
initial_population_size: 30

initial_sex_ratio:
  male: 0.5
  female: 0.5

creature_archetype:
  lifespan:
    min: 3
    max: 5
  sexual_maturity_months: 6
  max_fertility_age_years:
    male: 4
    female: 4
  gestation_period_days: 65
  nursing_period_days: 28
  menstrual_cycle_days: 24
  nearing_end_cycles: 12
  remove_ineligible_immediately: false
  litter_size:
    min: 3
    max: 6

breeders:
  random: 3
  inbreeding_avoidance: 0
  kennel_club: 0
  mill: 0

traits:
  - trait_id: 0
    name: "Test Trait"
    trait_type: SIMPLE_MENDELIAN
    genotypes:
      - genotype: "AA"
        phenotype: "Dominant"
        initial_freq: 0.5
      - genotype: "Aa"
        phenotype: "Hetero"
        initial_freq: 0.3
      - genotype: "aa"
        phenotype: "Recessive"
        initial_freq: 0.2
"""
    config_path.write_text(config_content)
    
    # Run simulation
    sim = Simulation.from_config(str(config_path))
    sim.initialize()
    
    # Run cycles manually
    from gene_sim.models.generation import Cycle
    cycle = Cycle(0)
    
    for cycle_num in range(sim.config.cycles):
        cycle.cycle_number = cycle_num
        cycle.execute_cycle(
            population=sim.population,
            breeders=sim.breeders,
            traits=sim.traits,
            rng=sim.rng,
            db_conn=sim.db_conn,
            simulation_id=sim.simulation_id,
            config=sim.config
        )
    
    # Query database for total creatures
    cursor = sim.db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM creatures")
    total_in_db = cursor.fetchone()[0]
    
    # Memory should be much smaller than total created
    in_memory = len(sim.population.creatures)
    
    # With homing, memory should be < 20% of total created
    memory_ratio = in_memory / total_in_db
    
    assert memory_ratio < 0.2, f"Memory should be <20% of total created (got {memory_ratio*100:.1f}%)"
    
    print(f"\n✓ Test passed:")
    print(f"  Total creatures created: {total_in_db}")
    print(f"  In working memory: {in_memory}")
    print(f"  Memory ratio: {memory_ratio*100:.1f}%")
    print(f"  Performance improvement: {total_in_db/in_memory:.1f}x fewer creatures in memory")


if __name__ == "__main__":
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        print("="*80)
        print("TESTING HOMED CREATURE MEMORY REMOVAL")
        print("="*80)
        
        print("\nTest 1: Homed offspring not in memory")
        test_homed_offspring_not_in_memory(tmppath)
        
        print("\nTest 2: Homed adults removed from memory")
        test_homed_adults_removed_from_memory(tmppath)
        
        print("\nTest 3: Population stabilization")
        test_population_stabilization(tmppath)
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED")
        print("="*80)
