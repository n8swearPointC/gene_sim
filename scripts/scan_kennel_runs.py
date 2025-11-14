"""
Scan all kennel runs to find any that show high levels of undesirable traits
in the desired population.
"""

import sqlite3
import yaml
from pathlib import Path


def analyze_undesirable_in_desired_population(db_path, trait_id, target_phenotype, directory="."):
    """
    Analyze undesirable phenotype frequency only among creatures with ALL desired phenotypes.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    result = cursor.fetchone()
    if not result:
        conn.close()
        return [], [], []
    sim_id = result[0]
    
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
    
    # Get last generation
    cursor.execute("""
        SELECT MAX(generation)
        FROM creatures
        WHERE simulation_id = ?
    """, (sim_id,))
    
    last_gen = cursor.fetchone()[0]
    
    # Get all living creatures in last generation
    cursor.execute("""
        SELECT creature_id
        FROM creatures
        WHERE simulation_id = ? AND generation = ? AND is_alive = 1
    """, (sim_id, last_gen))
    
    creature_ids = [row[0] for row in cursor.fetchall()]
    
    if not creature_ids:
        conn.close()
        return [], [], []
    
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
    count_with_undesirable = 0
    frequency = 0.0
    
    if creatures_with_all_desired:
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
    
    conn.close()
    
    return len(creatures_with_all_desired), count_with_undesirable, frequency * 100


def main():
    """Scan all kennel runs."""
    kennel_dir = Path("run3/run3a_kennels")
    
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
    
    print("="*80)
    print("SCANNING KENNEL RUNS FOR HIGH UNDESIRABLE TRAIT FREQUENCIES")
    print("="*80)
    print()
    
    for db_file in sorted(kennel_dir.glob("*.db")):
        print(f"\n{db_file.name}")
        print("-" * 80)
        
        any_high = False
        
        for trait_id, phenotype in undesirable_traits:
            total_desired, count_undesirable, frequency = analyze_undesirable_in_desired_population(
                db_file, trait_id, phenotype, kennel_dir
            )
            
            if total_desired > 0:
                if frequency > 50:  # Flag any frequency over 50%
                    print(f"  {phenotype:20} (trait {trait_id:2d}): {count_undesirable:3d}/{total_desired:3d} = {frequency:5.1f}% ***")
                    any_high = True
                elif frequency > 0:
                    print(f"  {phenotype:20} (trait {trait_id:2d}): {count_undesirable:3d}/{total_desired:3d} = {frequency:5.1f}%")
        
        if not any_high:
            print("  (No undesirable traits above 50%)")


if __name__ == "__main__":
    main()
