"""
Verify that database statistics are being stored and retrieved correctly.
This script will manually query a database and calculate frequencies to verify
the batch_analysis.py logic.
"""

import sqlite3
import yaml
from pathlib import Path


def verify_desired_population_stats(db_path, config_path):
    """
    Manually verify the statistics for desired population analysis.
    
    This will check:
    1. Which creatures have all desired phenotypes
    2. Among those, how many have each undesirable trait
    3. Compare with what the batch analysis would calculate
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Load config to get desired and undesired traits
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    target_phenotypes = config.get('target_phenotypes', [])
    undesirable_phenotypes = config.get('undesirable_phenotypes', [])
    
    print("="*80)
    print("DATABASE VERIFICATION")
    print("="*80)
    print(f"\nDatabase: {db_path}")
    print(f"Config: {config_path}")
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    sim_id = cursor.fetchone()[0]
    print(f"\nSimulation ID: {sim_id}")
    
    # Print desired phenotypes
    print(f"\nDesired phenotypes (creatures must have ALL):")
    for tp in target_phenotypes:
        print(f"  - {tp['phenotype']} (trait {tp['trait_id']})")
    
    # Print undesirable phenotypes
    print(f"\nUndesirable phenotypes to track:")
    for up in undesirable_phenotypes:
        print(f"  - {up['phenotype']} (trait {up['trait_id']})")
    
    # Build map of desired genotypes
    target_genotype_map = {}
    for target in target_phenotypes:
        target_trait_id = target['trait_id']
        target_pheno = target['phenotype']
        
        cursor.execute("""
            SELECT genotype
            FROM genotypes
            WHERE trait_id = ? AND phenotype = ?
        """, (target_trait_id, target_pheno))
        
        target_genotype_map[target_trait_id] = [row[0] for row in cursor.fetchall()]
        print(f"  Trait {target_trait_id} ({target_pheno}): genotypes {target_genotype_map[target_trait_id]}")
    
    # Build map of undesirable genotypes
    undesirable_genotype_map = {}
    for undesirable in undesirable_phenotypes:
        trait_id = undesirable['trait_id']
        phenotype = undesirable['phenotype']
        
        cursor.execute("""
            SELECT genotype
            FROM genotypes
            WHERE trait_id = ? AND phenotype = ?
        """, (trait_id, phenotype))
        
        undesirable_genotype_map[trait_id] = {
            'phenotype': phenotype,
            'genotypes': [row[0] for row in cursor.fetchall()]
        }
    
    # Get last generation
    cursor.execute("""
        SELECT MAX(generation)
        FROM creatures
        WHERE simulation_id = ?
    """, (sim_id,))
    last_gen = cursor.fetchone()[0]
    
    # Analyze a few key generations
    test_generations = [0, last_gen // 4, last_gen // 2, 3 * last_gen // 4, last_gen]
    
    for generation in test_generations:
        print(f"\n" + "="*80)
        print(f"Generation {generation}")
        print("="*80)
        
        # Get all living creatures
        cursor.execute("""
            SELECT creature_id
            FROM creatures
            WHERE simulation_id = ? AND generation = ? AND is_alive = 1
        """, (sim_id, generation))
        
        all_creature_ids = [row[0] for row in cursor.fetchall()]
        print(f"\nTotal living creatures: {len(all_creature_ids)}")
        
        # Find creatures with all desired phenotypes
        creatures_with_all_desired = []
        
        for creature_id in all_creature_ids:
            has_all_desired = True
            
            for target_trait_id, desired_genotypes in target_genotype_map.items():
                cursor.execute("""
                    SELECT genotype
                    FROM creature_genotypes
                    WHERE creature_id = ? AND trait_id = ?
                """, (creature_id, target_trait_id))
                
                result = cursor.fetchone()
                if not result or result[0] not in desired_genotypes:
                    has_all_desired = False
                    break
            
            if has_all_desired:
                creatures_with_all_desired.append(creature_id)
        
        print(f"Creatures with ALL desired phenotypes: {len(creatures_with_all_desired)}")
        
        if len(creatures_with_all_desired) > 0:
            print(f"Percentage: {100 * len(creatures_with_all_desired) / len(all_creature_ids):.1f}%")
            
            # For each undesirable trait, count presence in desired population
            print(f"\nUndesirable traits in desired population:")
            
            for trait_id, info in undesirable_genotype_map.items():
                phenotype = info['phenotype']
                undesirable_genotypes = info['genotypes']
                
                count_with_undesirable = 0
                
                for creature_id in creatures_with_all_desired:
                    cursor.execute("""
                        SELECT genotype
                        FROM creature_genotypes
                        WHERE creature_id = ? AND trait_id = ?
                    """, (creature_id, trait_id))
                    
                    result = cursor.fetchone()
                    if result and result[0] in undesirable_genotypes:
                        count_with_undesirable += 1
                
                frequency = 100 * count_with_undesirable / len(creatures_with_all_desired)
                print(f"  {phenotype} (trait {trait_id}): {count_with_undesirable}/{len(creatures_with_all_desired)} = {frequency:.1f}%")
                
                # Sample a few creatures to show their genotypes
                if count_with_undesirable > 0 and count_with_undesirable <= 5:
                    print(f"    Sample creatures with {phenotype}:")
                    sample_count = 0
                    for creature_id in creatures_with_all_desired:
                        cursor.execute("""
                            SELECT genotype
                            FROM creature_genotypes
                            WHERE creature_id = ? AND trait_id = ?
                        """, (creature_id, trait_id))
                        
                        result = cursor.fetchone()
                        if result and result[0] in undesirable_genotypes:
                            # Get all genotypes for this creature
                            cursor.execute("""
                                SELECT cg.trait_id, cg.genotype, g.phenotype
                                FROM creature_genotypes cg
                                JOIN genotypes g ON cg.trait_id = g.trait_id AND cg.genotype = g.genotype
                                WHERE cg.creature_id = ?
                                ORDER BY cg.trait_id
                            """, (creature_id,))
                            
                            genotypes = cursor.fetchall()
                            print(f"      Creature {creature_id}:")
                            for gt in genotypes:
                                marker = " <--" if gt[0] == trait_id else ""
                                print(f"        Trait {gt[0]}: {gt[1]} -> {gt[2]}{marker}")
                            
                            sample_count += 1
                            if sample_count >= 3:
                                break
        else:
            print("  (No creatures with all desired phenotypes)")
    
    conn.close()


if __name__ == "__main__":
    import sys
    
    # Allow passing db and config paths as arguments
    if len(sys.argv) > 2:
        db_path = sys.argv[1]
        config_path = sys.argv[2]
    else:
        # Test with a kennel database
        db_path = "run3/run3a_kennels/simulation_run_001_seed_3000.db"
        config_path = "run3/run3a_kennels/batch_config.yaml"
    
    verify_desired_population_stats(db_path, config_path)
