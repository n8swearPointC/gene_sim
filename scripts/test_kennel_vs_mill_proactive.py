"""
Test script to compare kennel club vs mill breeder behavior.
Kennels should proactively replace Ll parents with LL offspring.
Mills should not, as they don't care about genotypes.
"""

import sqlite3
from pathlib import Path
import yaml

# Run two simulations with different breeder mixes
configs = {
    "kennels_only": {
        "seed": 42,
        "years": 2,
        "mode": "quiet",
        "initial_population_size": 100,
        "initial_sex_ratio": {"male": 0.5, "female": 0.5},
        "creature_archetype": {
            "lifespan": {"min": 3.25, "max": 5},
            "sexual_maturity_months": 6,
            "max_fertility_age_years": {"male": 4.5, "female": 4.25},
            "gestation_period_days": 65,
            "nursing_period_days": 28,
            "menstrual_cycle_days": 24,
            "nearing_end_cycles": 12,
            "remove_ineligible_immediately": False,
            "litter_size": {"min": 3, "max": 6}
        },
        "target_phenotypes": [{"trait_id": 0, "phenotype": "Brown"}],
        "undesirable_phenotypes": [{"trait_id": 1, "phenotype": "Small"}],
        "genotype_preferences": [
            {
                "trait_id": 1,
                "optimal": ["LL"],
                "acceptable": ["Ll"],
                "undesirable": ["ll"]
            }
        ],
        "breeders": {
            "random": 0,
            "inbreeding_avoidance": 0,
            "kennel_club": 15,
            "mill": 0
        },
        "traits": [
            {
                "trait_id": 0,
                "name": "Coat Color",
                "trait_type": "SIMPLE_MENDELIAN",
                "genotypes": [
                    {"genotype": "BB", "phenotype": "Black", "initial_freq": 0.25},
                    {"genotype": "Bb", "phenotype": "Black", "initial_freq": 0.50},
                    {"genotype": "bb", "phenotype": "Brown", "initial_freq": 0.25}
                ]
            },
            {
                "trait_id": 1,
                "name": "Body Size",
                "trait_type": "SIMPLE_MENDELIAN",
                "genotypes": [
                    {"genotype": "LL", "phenotype": "Large", "initial_freq": 0.0},
                    {"genotype": "Ll", "phenotype": "Large", "initial_freq": 0.25},
                    {"genotype": "ll", "phenotype": "Small", "initial_freq": 0.75}
                ]
            }
        ]
    },
    "mills_only": {
        "seed": 42,
        "years": 2,
        "mode": "quiet",
        "initial_population_size": 100,
        "initial_sex_ratio": {"male": 0.5, "female": 0.5},
        "creature_archetype": {
            "lifespan": {"min": 3.25, "max": 5},
            "sexual_maturity_months": 6,
            "max_fertility_age_years": {"male": 4.5, "female": 4.25},
            "gestation_period_days": 65,
            "nursing_period_days": 28,
            "menstrual_cycle_days": 24,
            "nearing_end_cycles": 12,
            "remove_ineligible_immediately": False,
            "litter_size": {"min": 3, "max": 6}
        },
        "target_phenotypes": [{"trait_id": 0, "phenotype": "Brown"}],
        "undesirable_phenotypes": [{"trait_id": 1, "phenotype": "Small"}],
        "genotype_preferences": [],  # Mills don't use genotype preferences
        "breeders": {
            "random": 0,
            "inbreeding_avoidance": 0,
            "kennel_club": 0,
            "mill": 15
        },
        "traits": [
            {
                "trait_id": 0,
                "name": "Coat Color",
                "trait_type": "SIMPLE_MENDELIAN",
                "genotypes": [
                    {"genotype": "BB", "phenotype": "Black", "initial_freq": 0.25},
                    {"genotype": "Bb", "phenotype": "Black", "initial_freq": 0.50},
                    {"genotype": "bb", "phenotype": "Brown", "initial_freq": 0.25}
                ]
            },
            {
                "trait_id": 1,
                "name": "Body Size",
                "trait_type": "SIMPLE_MENDELIAN",
                "genotypes": [
                    {"genotype": "LL", "phenotype": "Large", "initial_freq": 0.0},
                    {"genotype": "Ll", "phenotype": "Large", "initial_freq": 0.25},
                    {"genotype": "ll", "phenotype": "Small", "initial_freq": 0.75}
                ]
            }
        ]
    }
}

def run_comparison():
    from gene_sim.simulation import Simulation
    import tempfile
    
    results = {}
    
    for name, config in configs.items():
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}")
        
        # Create temp config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        
        # Create temp db file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Run simulation
            sim = Simulation(config_path, db_path)
            sim.initialize()
            sim.run()
            
            # Query final genotype frequencies
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get final generation stats for trait_id 1 (Body Size)
            cursor.execute("""
                SELECT generation, genotype, frequency
                FROM generation_genotype_frequencies
                WHERE simulation_id = 1 AND trait_id = 1
                ORDER BY generation DESC, genotype
                LIMIT 3
            """)
            
            final_stats = {}
            for gen, genotype, freq in cursor.fetchall():
                if gen not in final_stats:
                    final_stats[gen] = {}
                final_stats[gen][genotype] = freq
            
            results[name] = final_stats
            conn.close()
            
        finally:
            # Cleanup
            Path(config_path).unlink(missing_ok=True)
            Path(db_path).unlink(missing_ok=True)
    
    # Display comparison
    print(f"\n{'='*60}")
    print("COMPARISON RESULTS - Body Size (trait_id 1)")
    print(f"{'='*60}")
    print(f"{'Breeder Type':<20} {'LL %':>10} {'Ll %':>10} {'ll %':>10}")
    print(f"{'-'*60}")
    
    for name, stats in results.items():
        if stats:
            gen = max(stats.keys())
            ll_freq = stats[gen].get('LL', 0) * 100
            Ll_freq = stats[gen].get('Ll', 0) * 100
            ll_freq_lower = stats[gen].get('ll', 0) * 100
            print(f"{name:<20} {ll_freq:>9.1f}% {Ll_freq:>9.1f}% {ll_freq_lower:>9.1f}%")
    
    print(f"\n{'='*60}")
    print("INTERPRETATION:")
    print("- Kennels should have HIGHER LL% (proactive replacement)")
    print("- Mills should have LOWER LL% (only end-of-life replacement)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_comparison()
