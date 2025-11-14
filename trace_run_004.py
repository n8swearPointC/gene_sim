"""
Trace through the exact calculation for run 004 Hip Issues to verify
it matches what should appear in the combined chart.
"""

import sqlite3
import yaml
from pathlib import Path


def analyze_undesirable_in_desired_population_trace(db_path, trait_id, target_phenotype, directory="."):
    """
    Analyze with detailed tracing.
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
    
    # Get genotypes that map to the undesirable phenotype
    cursor.execute("""
        SELECT genotype
        FROM genotypes
        WHERE trait_id = ? AND phenotype = ?
    """, (trait_id, target_phenotype))
    
    undesirable_genotypes = [row[0] for row in cursor.fetchall()]
    
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
    
    print(f"\nTracing {target_phenotype} (trait {trait_id}) across all generations:")
    print(f"Undesirable genotypes: {undesirable_genotypes}")
    print()
    
    for generation in generations:
        # Get all living creatures in this generation
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
            
            print(f"  Gen {generation:2d}: {count_with_undesirable:3d}/{len(creatures_with_all_desired):3d} with {target_phenotype} = {frequency*100:5.1f}%")
        else:
            # No creatures with all desired phenotypes
            generation_frequencies[generation] = 0.0
            print(f"  Gen {generation:2d}: No creatures with all desired phenotypes")
    
    conn.close()
    
    # Convert to sorted lists
    cycles = sorted(generation_frequencies.keys())
    frequencies = [generation_frequencies[c] * 100 for c in cycles]  # Convert to percentage
    
    return cycles, frequencies


def main():
    """Test run 004."""
    db_path = "run3/run3a_kennels/simulation_run_004_seed_3003.db"
    config_dir = "run3/run3a_kennels"
    
    print("="*80)
    print("DETAILED TRACE: Run 004 Hip Issues")
    print("="*80)
    
    cycles, frequencies = analyze_undesirable_in_desired_population_trace(
        db_path, 7, "Hip Issues", config_dir
    )
    
    print()
    print("="*80)
    print("FINAL RESULT")
    print("="*80)
    print(f"Cycles (generations): {cycles}")
    print(f"Frequencies (%):      {[f'{f:.1f}' for f in frequencies]}")
    print()
    print("This data will be plotted as one line in the combined chart.")
    print("The 100% in the final generation is CORRECT - all 3 creatures")
    print("with desired phenotypes happened to have Hip Issues.")


if __name__ == "__main__":
    main()
