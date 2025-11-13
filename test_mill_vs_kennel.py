"""Test comparing Mill vs Kennel breeding behavior with recessive trait."""

import tempfile
import sqlite3
from pathlib import Path
from gene_sim import Simulation
from gene_sim.models.generation import Cycle
import numpy as np


def create_test_config(breeder_type: str, seed: int = 42) -> dict:
    """Create a config for testing with 3 creatures and specified breeder type."""
    return {
        'seed': seed,
        'years': 5,  # Long enough to allow breeding
        'mode': 'monitor',
        'initial_population_size': 3,
        'initial_sex_ratio': {'male': 0.34, 'female': 0.66},  # 1 male, 2 females
        'creature_archetype': {
            'lifespan': {'min': 15, 'max': 20},
            'sexual_maturity_months': 0.01,  # Mature immediately
            'max_fertility_age_years': {'male': 10.0, 'female': 8.0},
            'gestation_period_days': 10.0,
            'nursing_period_days': 10.0,
            'menstrual_cycle_days': 28.0,
            'nearing_end_cycles': 3,
            'remove_ineligible_immediately': False,
            'litter_size': {'min': 4, 'max': 6}
        },
        'breeders': {
            'random': 0,
            'inbreeding_avoidance': 0,
            'kennel_club': 1 if breeder_type == 'kennel' else 0,
            'mill': 1 if breeder_type == 'mill' else 0,
        },
        'target_phenotypes': [
            {'trait_id': 0, 'phenotype': 'Black'}
        ],
        'undesirable_phenotypes': [
            {'trait_id': 0, 'phenotype': 'Brown'}
        ],
        'undesirable_genotypes': [
            {'trait_id': 0, 'genotype': 'bb'}
        ],
        'traits': [
            {
                'trait_id': 0,
                'name': 'Coat Color',
                'trait_type': 'SIMPLE_MENDELIAN',
                'genotypes': [
                    {'genotype': 'BB', 'phenotype': 'Black', 'initial_freq': 0.0},
                    {'genotype': 'Bb', 'phenotype': 'Black', 'initial_freq': 0.67},  # ALL start as Bb
                    {'genotype': 'bb', 'phenotype': 'Brown', 'initial_freq': 0.33},
                ]
            }
        ]
    }


def analyze_population(db_path: str, breeder_type: str):
    """Analyze and display population statistics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n{'='*70}")
    print(f"RESULTS FOR {breeder_type.upper()} BREEDER")
    print(f"{'='*70}\n")
    
    # Get final cycle number
    cursor.execute("""
        SELECT MAX(generation) FROM generation_stats
    """)
    final_cycle = cursor.fetchone()[0] or 0
    
    # Analyze by sex
    for sex in ['male', 'female']:
        print(f"\n{sex.upper()}S:")
        print("-" * 50)
        
        # Get total population for this sex
        cursor.execute("""
            SELECT COUNT(*) FROM creatures WHERE sex = ?
        """, (sex,))
        total_pop = cursor.fetchone()[0]
        
        # Get genotype distribution for all creatures of this sex
        cursor.execute("""
            SELECT cg.genotype, COUNT(*) as count
            FROM creature_genotypes cg
            JOIN creatures c ON cg.creature_id = c.creature_id
            WHERE cg.trait_id = 0 AND c.sex = ?
            GROUP BY cg.genotype
            ORDER BY cg.genotype
        """, (sex,))
        all_genotypes = cursor.fetchall()
        
        # Get breeding pool size for this sex
        cursor.execute("""
            SELECT eligible_males, eligible_females
            FROM generation_stats
            WHERE generation = ?
        """, (final_cycle,))
        breeding_stats = cursor.fetchone()
        breeding_pool_size = breeding_stats[0] if sex == 'male' else breeding_stats[1] if breeding_stats else 0
        
        # Calculate genotype percentages for total population
        total_genotypes = {}
        for genotype, count in all_genotypes:
            total_genotypes[genotype] = count
        
        print(f"  Total Population: {total_pop} creatures")
        print(f"  Breeding Pool: {breeding_pool_size} creatures (at cycle {final_cycle})")
        print()
        
        print(f"  TOTAL POPULATION - Genotype Distribution:")
        for genotype in ['BB', 'Bb', 'bb']:
            count = total_genotypes.get(genotype, 0)
            percentage = (count / total_pop * 100) if total_pop > 0 else 0
            print(f"    {genotype}: {count:3d} ({percentage:5.1f}%)")
        
        print()
        
        # For offspring, show only creatures that were born
        cursor.execute("""
            SELECT cg.genotype, COUNT(*) as count
            FROM creatures c
            JOIN creature_genotypes cg ON c.creature_id = cg.creature_id
            WHERE cg.trait_id = 0
            AND c.birth_cycle > 0
            AND c.sex = ?
            GROUP BY cg.genotype
            ORDER BY cg.genotype
        """, (sex,))
        offspring_genotypes = cursor.fetchall()
        
        offspring_total = sum(count for _, count in offspring_genotypes)
        
        if offspring_total > 0:
            print(f"  OFFSPRING - Genotype Distribution:")
            offspring_counts = {g: c for g, c in offspring_genotypes}
            for genotype in ['BB', 'Bb', 'bb']:
                count = offspring_counts.get(genotype, 0)
                percentage = (count / offspring_total * 100) if offspring_total > 0 else 0
                print(f"    {genotype}: {count:3d} ({percentage:5.1f}%)")
        else:
            print(f"  OFFSPRING: No offspring produced")
        
        print()
        
        # Show founder genotypes for this sex
        cursor.execute("""
            SELECT cg.genotype, COUNT(*) as count
            FROM creatures c
            JOIN creature_genotypes cg ON c.creature_id = cg.creature_id
            WHERE cg.trait_id = 0
            AND c.birth_cycle = 0
            AND c.sex = ?
            GROUP BY cg.genotype
            ORDER BY cg.genotype
        """, (sex,))
        founder_genotypes = cursor.fetchall()
        
        print(f"  FOUNDERS:")
        for genotype, count in founder_genotypes:
            print(f"    {genotype}: {count}")
    
    # Show overall breeding events
    print(f"\n{'='*50}")
    cursor.execute("""
        SELECT COUNT(*) FROM creatures WHERE birth_cycle > 0
    """)
    offspring_count = cursor.fetchone()[0]
    print(f"Total Offspring Born: {offspring_count}")
    
    conn.close()


def check_for_bb_creatures(conn: sqlite3.Connection) -> tuple[bool, bool]:
    """Check if we have at least one BB male and one BB female.
    
    Returns:
        (has_bb_male, has_bb_female)
    """
    cursor = conn.cursor()
    
    # Check for BB male
    cursor.execute("""
        SELECT COUNT(*) FROM creatures c
        JOIN creature_genotypes cg ON c.creature_id = cg.creature_id
        WHERE c.sex = 'male' AND cg.trait_id = 0 AND cg.genotype = 'BB'
    """)
    has_bb_male = cursor.fetchone()[0] > 0
    
    # Check for BB female
    cursor.execute("""
        SELECT COUNT(*) FROM creatures c
        JOIN creature_genotypes cg ON c.creature_id = cg.creature_id
        WHERE c.sex = 'female' AND cg.trait_id = 0 AND cg.genotype = 'BB'
    """)
    has_bb_female = cursor.fetchone()[0] > 0
    
    return has_bb_male, has_bb_female


def check_initial_population(conn: sqlite3.Connection) -> tuple[int, int]:
    """Check the sex distribution of the initial population.
    
    Returns:
        (num_males, num_females)
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM creatures WHERE sex = 'male' AND birth_cycle = 0
    """)
    num_males = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM creatures WHERE sex = 'female' AND birth_cycle = 0
    """)
    num_females = cursor.fetchone()[0]
    
    return num_males, num_females


def run_test(breeder_type: str, max_init_attempts: int = 15):
    """Run test until we get 1 BB male and 1 BB female (max 15 cycles).
    
    Will retry initialization up to max_init_attempts times to get 1 male and 2 females.
    """
    import yaml
    
    print(f"\n{'='*70}")
    print(f"RUNNING {breeder_type.upper()} BREEDER TEST")
    print(f"{'='*70}")
    print(f"Goal: Create 1 BB male and 1 BB female (max 15 cycles)")
    print(f"Attempting to initialize with 1 male and 2 females (max {max_init_attempts} attempts)\n")
    
    # Try to get the right initial population
    for attempt in range(max_init_attempts):
        config = create_test_config(breeder_type, seed=42 + attempt)
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        
        # Create temporary database
        db_path = tempfile.mktemp(suffix='.db')
        
        try:
            # Run simulation
            sim = Simulation.from_config(config_path, db_path)
            sim.initialize()
            
            # Check initial population
            num_males, num_females = check_initial_population(sim.db_conn)
            
            print(f"Attempt {attempt + 1}: {num_males} male(s), {num_females} female(s)", end="")
            
            if num_males == 1 and num_females == 2:
                print(" ✓ Got 1 male and 2 females!\n")
                
                # Run cycles until we get BB creatures or hit max attempts
                cycle = Cycle(1)  # Start from cycle 1 (cycle 0 is for founders)
                max_cycles = 15
                
                for cycle_num in range(1, max_cycles + 1):  # Start from 1, not 0
                    cycle.cycle_number = cycle_num
                    
                    stats = cycle.execute_cycle(
                        population=sim.population,
                        breeders=sim.breeders,
                        traits=sim.traits,
                        rng=sim.rng,
                        db_conn=sim.db_conn,
                        simulation_id=sim.simulation_id,
                        config=sim.config
                    )
                    
                    # Check if we have our target creatures
                    has_bb_male, has_bb_female = check_for_bb_creatures(sim.db_conn)
                    
                    if has_bb_male and has_bb_female:
                        print(f"✓ Success at cycle {cycle_num}!")
                        print(f"  Found BB male and BB female")
                        break
                    else:
                        status = []
                        if has_bb_male:
                            status.append("BB male ✓")
                        else:
                            status.append("BB male ✗")
                        if has_bb_female:
                            status.append("BB female ✓")
                        else:
                            status.append("BB female ✗")
                        print(f"Cycle {cycle_num}: {', '.join(status)}")
                else:
                    print(f"\n✗ Did not achieve goal within {max_cycles} cycles")
                
                # Finalize simulation
                sim.db_conn.execute("""
                    UPDATE simulations
                    SET status = 'completed',
                        end_time = datetime('now'),
                        final_population_size = (SELECT COUNT(*) FROM creatures WHERE simulation_id = ?)
                    WHERE simulation_id = ?
                """, (sim.simulation_id, sim.simulation_id))
                sim.db_conn.commit()
                
                # Analyze results
                analyze_population(db_path, breeder_type)
                
                # Close database connection
                sim.db_conn.close()
                
                # Cleanup
                Path(config_path).unlink(missing_ok=True)
                Path(db_path).unlink(missing_ok=True)
                
                return  # Success, exit function
            else:
                print(" ✗ Retrying...")
                # Close and cleanup
                sim.db_conn.close()
                Path(config_path).unlink(missing_ok=True)
                Path(db_path).unlink(missing_ok=True)
                
        except Exception as e:
            print(f" ✗ Error: {e}")
            # Cleanup
            Path(config_path).unlink(missing_ok=True)
            Path(db_path).unlink(missing_ok=True)
    
    print(f"\n✗ Failed to get 1 male and 2 females after {max_init_attempts} attempts")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("TESTING MILL vs KENNEL BREEDING BEHAVIOR")
    print("="*70)
    print("\nSetup:")
    print("  - Target: 1 male and 2 females in initial population")
    print("  - Goal: Create 1 BB male and 1 BB female")
    print("  - Max initialization attempts: 15")
    print("  - Max breeding cycles: 15")
    print("  - bb genotype is UNDESIRABLE")
    print("  - Brown phenotype is UNDESIRABLE")
    print()
    
    # Run Mill test only
    run_test('mill', max_init_attempts=15)
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")
