"""Quick test script to run a simulation."""

from gene_sim import Simulation
import sqlite3

print("=" * 60)
print("Running Quick Simulation Test")
print("=" * 60)
print("\nConfiguration:")
print("  - Initial population: 100 creatures")
print("  - Years: 2 (~30 cycles)")
print("  - Traits: 5 (all Simple Mendelian)")
print("  - Breeders: 15 (5 kennel club, 10 mill)")
print()

# Run simulation
sim = Simulation.from_config('quick_test_config.yaml')
print(f"Database will be created at: {sim.db_path}")
print("\nRunning simulation...\n")

results = sim.run()

print("=" * 60)
print("Simulation Complete!")
print("=" * 60)
print(f"\nResults:")
print(f"  Simulation ID: {results.simulation_id}")
print(f"  Status: {results.status}")
print(f"  Generations completed: {results.generations_completed}")
print(f"  Final population size: {results.final_population_size}")
print(f"  Duration: {results.duration_seconds:.2f} seconds")
print(f"  Database: {results.database_path}")
print()

# Query some statistics
conn = sqlite3.connect(results.database_path)

# Combined statistics table - Population + All Genotypes
print("Generation Statistics (All Traits - Genotype Frequencies %):")
print("=" * 200)
cursor = conn.cursor()

# Get all generations with population stats
cursor.execute("""
    SELECT generation, population_size, births, deaths, eligible_males, eligible_females
    FROM generation_stats
    WHERE simulation_id = ?
    ORDER BY generation
""", (results.simulation_id,))
gen_stats = {row[0]: row[1:] for row in cursor.fetchall()}

# Get all genotype frequencies for all traits
cursor.execute("""
    SELECT generation, trait_id, genotype, frequency
    FROM generation_genotype_frequencies
    WHERE simulation_id = ?
    ORDER BY generation, trait_id, genotype
""", (results.simulation_id,))

# Organize genotypes by generation and trait
genotypes_by_gen = {}
for gen, trait_id, genotype, freq in cursor.fetchall():
    if gen not in genotypes_by_gen:
        genotypes_by_gen[gen] = {}
    if trait_id not in genotypes_by_gen[gen]:
        genotypes_by_gen[gen][trait_id] = {}
    genotypes_by_gen[gen][trait_id][genotype] = freq

# Print combined table header
print(f"{'Gen':<4} {'Pop':<5} {'Brth':<5} {'Dth':<4} {'M':<4} {'F':<4} "
      f"{'BB':<6} {'Bb':<6} {'bb':<6} "
      f"{'LL':<6} {'Ll':<6} {'ll':<6} "
      f"{'EE':<6} {'Ee':<6} {'ee':<6} "
      f"{'TT':<6} {'Tt':<6} {'tt':<6} "
      f"{'PP':<6} {'Pp':<6} {'pp':<6}")
print("-" * 200)

for gen in sorted(gen_stats.keys()):
    pop, births, deaths, males, females = gen_stats[gen]
    genos = genotypes_by_gen.get(gen, {})
    
    # Trait 0 (Coat Color)
    t0 = genos.get(0, {})
    BB = t0.get('BB', 0.0) * 100
    Bb = t0.get('Bb', 0.0) * 100
    bb = t0.get('bb', 0.0) * 100
    
    # Trait 1 (Body Size)
    t1 = genos.get(1, {})
    LL = t1.get('LL', 0.0) * 100
    Ll = t1.get('Ll', 0.0) * 100
    ll = t1.get('ll', 0.0) * 100
    
    # Trait 2 (Eye Color)
    t2 = genos.get(2, {})
    EE = t2.get('EE', 0.0) * 100
    Ee = t2.get('Ee', 0.0) * 100
    ee = t2.get('ee', 0.0) * 100
    
    # Trait 3 (Tail Type)
    t3 = genos.get(3, {})
    TT = t3.get('TT', 0.0) * 100
    Tt = t3.get('Tt', 0.0) * 100
    tt = t3.get('tt', 0.0) * 100
    
    # Trait 4 (Ear Shape)
    t4 = genos.get(4, {})
    PP = t4.get('PP', 0.0) * 100
    Pp = t4.get('Pp', 0.0) * 100
    pp = t4.get('pp', 0.0) * 100
    
    print(f"{gen:<4} {pop:<5} {births:<5} {deaths:<4} {males:<4} {females:<4} "
          f"{BB:>5.1f}% {Bb:>5.1f}% {bb:>5.1f}% "
          f"{LL:>5.1f}% {Ll:>5.1f}% {ll:>5.1f}% "
          f"{EE:>5.1f}% {Ee:>5.1f}% {ee:>5.1f}% "
          f"{TT:>5.1f}% {Tt:>5.1f}% {tt:>5.1f}% "
          f"{PP:>5.1f}% {Pp:>5.1f}% {pp:>5.1f}%")

print("=" * 200)
print()

conn.close()

print("=" * 60)
print("Done! Check the database for more detailed analysis.")
print("=" * 60)

