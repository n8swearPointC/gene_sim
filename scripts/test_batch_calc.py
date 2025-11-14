"""
Trace what batch_analysis.py is calculating for a specific database.
"""

import sqlite3
import yaml
from pathlib import Path


def analyze_undesirable_in_desired_population(db_path, trait_id, target_phenotype, directory="."):
    """
    Replicate the batch_analysis.py function to verify what it calculates.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    sim_id = cursor.fetchone()[0]
    
    # Get target (desired) phenotypes
    config_path = Path(directory) / "batch_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    target_pheno_list = config.get('target_phenotypes', [])
    
    if not target_pheno_list:
        conn.close()
        return [], [], []
    
    # Get genotypes that map to the undesirable phenotype
    cursor.execute("""
        SELECT genotype
        FROM genotypes
        WHERE trait_id = ? AND phenotype = ?
    """, (trait_id, target_phenotype))
    
    undesirable_genotypes = [row[0] for row in cursor.fetchall()]
    
    if not undesirable_genotypes:
        conn.close()
        return [], [], []
    
    # For each target phenotype, get the genotypes that express it
    target_genotype_map = {}
    for target in target_pheno_list:
        target_trait_id = target['trait_id']
        target_pheno = target['phenotype']
        
        cursor.execute("""
            SELECT genotype
            FROM genotypes
            WHERE trait_id = ? AND phenotype = ?
        """, (target_trait_id, target_pheno))
        
        target_genotype_map[target_trait_id] = [row[0] for row in cursor.fetchall()]
    
    # Get all creatures by generation and check their phenotypes
    cursor.execute("""
        SELECT DISTINCT generation
        FROM creatures
        WHERE simulation_id = ?
        ORDER BY generation
    """, (sim_id,))
    
    generations = [row[0] for row in cursor.fetchall()]
    generation_frequencies = {}
    
    for generation in generations:
        # Get all living creatures in this generation (homed or not)
        cursor.execute("""
            SELECT creature_id
            FROM creatures
            WHERE simulation_id = ? AND generation = ? AND is_alive = 1
        """, (sim_id, generation))
        
        creature_ids = [row[0] for row in cursor.fetchall()]
        
        if not creature_ids:
            continue
        
        # Count creatures with all desired phenotypes
        creatures_with_all_desired = []
        
        for creature_id in creature_ids:
            # Check if this creature has all desired phenotypes
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
        
        # Among creatures with all desired phenotypes, count those with the undesirable trait
        if creatures_with_all_desired:
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
            
            frequency = count_with_undesirable / len(creatures_with_all_desired)
            generation_frequencies[generation] = frequency
        else:
            # No creatures with all desired phenotypes
            generation_frequencies[generation] = 0.0
    
    conn.close()
    
    # Convert to sorted lists
    cycles = sorted(generation_frequencies.keys())
    frequencies = [generation_frequencies[c] * 100 for c in cycles]  # Convert to percentage
    
    return cycles, frequencies, undesirable_genotypes


def main():
    """Test with run 015."""
    db_path = "run3/run3b_mills/simulation_run_015_seed_4014.db"
    config_dir = "run3/run3b_mills"
    
    print("="*80)
    print("TESTING BATCH_ANALYSIS CALCULATION")
    print("="*80)
    print(f"\nDatabase: {db_path}")
    print()
    
    # Test aggression
    print("Analyzing Aggression (trait 6)...")
    cycles, frequencies, genotypes = analyze_undesirable_in_desired_population(
        db_path, 6, "Aggression", config_dir
    )
    
    print(f"  Undesirable genotypes: {genotypes}")
    print(f"  Cycles: {cycles}")
    print(f"  Frequencies (%): {[f'{f:.1f}' for f in frequencies]}")
    print()
    
    # Test all undesirable traits
    undesirable_traits = [
        (3, "Weak Bones"),
        (4, "Poor Vision"),
        (5, "Thin Fur"),
        (6, "Aggression"),
        (7, "Hip Issues"),
        (8, "Skin Problems"),
        (9, "Heart Defect"),
        (10, "Seizures"),
        (11, "Blindness")
    ]
    
    print("Summary for all undesirable traits (last generation only):")
    for trait_id, phenotype in undesirable_traits:
        cycles, frequencies, genotypes = analyze_undesirable_in_desired_population(
            db_path, trait_id, phenotype, config_dir
        )
        if frequencies:
            last_freq = frequencies[-1]
            print(f"  {phenotype:20} (trait {trait_id:2d}): {last_freq:5.1f}%")
        else:
            print(f"  {phenotype:20} (trait {trait_id:2d}): No data")


if __name__ == "__main__":
    main()
