"""
Check all mill runs to see if any achieve creatures with desired phenotypes
and what undesirable traits they have.
"""

import sqlite3
import yaml
from pathlib import Path


def check_run(db_path, config_path):
    """Check a single run for desired population stats."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    target_phenotypes = config.get('target_phenotypes', [])
    undesirable_phenotypes = config.get('undesirable_phenotypes', [])
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    sim_id = cursor.fetchone()[0]
    
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
    
    # Check last generation
    cursor.execute("""
        SELECT creature_id
        FROM creatures
        WHERE simulation_id = ? AND generation = ? AND is_alive = 1
    """, (sim_id, last_gen))
    
    all_creature_ids = [row[0] for row in cursor.fetchall()]
    
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
    
    conn.close()
    
    return {
        'db': db_path.name,
        'last_gen': last_gen,
        'total': len(all_creature_ids),
        'with_desired': len(creatures_with_all_desired),
        'percent': 100 * len(creatures_with_all_desired) / len(all_creature_ids) if all_creature_ids else 0
    }


def main():
    """Check all mill runs."""
    mill_dir = Path("run3/run3b_mills")
    config_path = mill_dir / "batch_config.yaml"
    
    results = []
    
    for db_file in sorted(mill_dir.glob("*.db")):
        result = check_run(db_file, config_path)
        results.append(result)
    
    print("="*80)
    print("MILL RUNS - Creatures with ALL desired phenotypes")
    print("="*80)
    print()
    
    for r in results:
        if r['with_desired'] > 0:
            print(f"{r['db']:40} Gen {r['last_gen']:2d}: {r['with_desired']:3d}/{r['total']:3d} ({r['percent']:5.1f}%)")
        else:
            print(f"{r['db']:40} Gen {r['last_gen']:2d}: None")
    
    total_with_any = sum(1 for r in results if r['with_desired'] > 0)
    print()
    print(f"Total runs with at least one desired creature: {total_with_any}/{len(results)}")


if __name__ == "__main__":
    main()
