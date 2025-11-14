# Genealogical Simulation - Implementation Plan

## Overview

Implement a complete Phase 1 genealogical simulation system in Python with SQLite persistence, supporting multiple breeding strategies, trait inheritance, and simulation execution. Reporting/export will be implemented in a later phase.

## Project Structure

```
gene_sim/
├── __init__.py              # Public API: Simulation, SimulationResults, load_config
├── simulation.py             # Simulation class and SimulationResults dataclass
├── config.py                # Configuration loading and validation
├── exceptions.py             # Custom exception classes
├── models/                   # Domain models
│   ├── __init__.py
│   ├── trait.py             # Trait and Genotype classes
│   ├── creature.py          # Creature class with genome and lineage
│   ├── breeder.py           # Breeder base class and implementations
│   ├── population.py       # Population working pool management
│   └── generation.py        # Generation cycle coordination
└── database/                # Database layer
    ├── __init__.py
    ├── schema.py            # Schema creation and migrations
    └── connection.py       # Database connection management

tests/
├── __init__.py
├── test_trait.py
├── test_creature.py
├── test_breeder.py
├── test_population.py
├── test_generation.py
├── test_simulation.py
├── test_config.py
└── test_database.py
```

## Implementation Phases

### Phase 1: Project Setup and Dependencies

**Files to create:**
- `setup.py` or `pyproject.toml` - Package configuration
- `requirements.txt` - Dependencies (numpy, pyyaml, pytest, sqlite3 (built-in))
- `.gitignore` - Python/git ignores
- `README.md` - Project overview and usage

**Dependencies:**
- Python 3.10+
- numpy (for arrays and random number generation)
- pyyaml (for config parsing)
- pytest (for testing)

### Phase 2: Core Infrastructure

**2.1 Exception Classes** (`exceptions.py`)
- `GeneSimError` (base)
- `ConfigurationError`
- `SimulationError`
- `DatabaseError`

**2.2 Database Layer** (`database/`)
- `schema.py`: Create all tables, indexes, foreign keys per database-schema.md
- `connection.py`: Database connection management, transaction handling
- Schema creation function that creates all tables in correct order
- Index creation for performance

**2.3 Configuration System** (`config.py`)
- `load_config()`: Load and parse YAML/JSON config files
- `validate_config()`: Validate all config fields:
  - Trait definitions (frequencies sum to 1.0, valid types)
  - Breeder counts (non-negative, sum validation)
  - Population parameters (positive values, valid ranges)
  - Target phenotypes (valid trait IDs)
- `SimulationConfig` dataclass for typed config access
- Normalize genotype frequencies if needed

### Phase 3: Domain Models

**3.1 Trait Model** (`models/trait.py`)
- `Trait` class: trait_id, name, trait_type enum
- `Genotype` class: genotype string, phenotype, sex (optional), initial_freq
- Trait type enum: SIMPLE_MENDELIAN, INCOMPLETE_DOMINANCE, CODOMINANCE, SEX_LINKED, POLYGENIC
- Methods: validate genotypes, get phenotype from genotype

**3.2 Creature Model** (`models/creature.py`)
- `Creature` class with attributes:
  - creature_id, simulation_id, birth_generation, sex
  - parent1_id, parent2_id, inbreeding_coefficient
  - litters_remaining, lifespan, is_alive
  - genome: `List[str]` indexed by trait_id (0-99), each element is genotype string
- Methods:
  - `calculate_age(current_generation)` - on-demand age calculation
  - `is_breeding_eligible(current_generation, config)` - age and litter checks
  - `produce_gamete(trait_id, rng)` - random allele selection for gamete
  - `calculate_inbreeding_coefficient(parent1, parent2)` - Wright's formula with r_parents
  - `calculate_relationship_coefficient(other)` - pedigree traversal (simplified for Phase 1)

**3.3 Breeder Model** (`models/breeder.py`)
- `Breeder` abstract base class with `select_pairs()` method
- `RandomBreeder`: Random pairing
- `InbreedingAvoidanceBreeder`: Avoids high inbreeding pairs
- `KennelClubBreeder`: Selects for target phenotypes with guidelines
- `UnrestrictedPhenotypeBreeder`: Selects for target phenotypes without restrictions
- All use seeded RNG for reproducibility

**3.4 Population Model** (`models/population.py`)
- `Population` class managing working pool:
  - List of creatures in memory
  - Aging-out list: `List[List[Creature]]` where index 0 = current generation
  - When creatures added: append to `age_out[birth_gen + lifespan - current_gen]`
  - When generation advances: slice off `age_out[0]` after processing
- Methods:
  - `get_eligible_males(current_generation, config)` - filter by age
  - `get_eligible_females(current_generation, config)` - filter by age and litters_remaining
  - `add_creatures(creatures, current_generation)` - add offspring, update aging-out list
  - `get_aged_out_creatures()` - retrieve `age_out[0]` (current generation's aged-out)
  - `remove_aged_out_creatures(db_conn)` - persist `age_out[0]`, then slice it off
  - `advance_generation()` - slice off `age_out[0]` after removal
  - `calculate_genotype_frequencies(trait_id)` - from working pool
  - `calculate_allele_frequencies(trait_id)` - from genotypes
  - `calculate_heterozygosity(trait_id)` - proportion heterozygous
  - `calculate_genotype_diversity(trait_id)` - count distinct genotypes

**3.5 Generation Model** (`models/generation.py`)
- `Generation` class:
  - `generation_number` (in-memory counter)
  - `execute_cycle(population, breeders, rng, db_conn, simulation_id, config)`:
    1. Filter eligible creatures
    2. Distribute breeders (by config counts)
    3. Select pairs via breeders
    4. Create offspring (gamete formation, inheritance)
    5. Add offspring to population (with current_generation for aging-out list)
    6. Get aged-out creatures (from `age_out[0]`)
    7. Calculate statistics (before removal)
    8. Persist generation stats to database
    9. Remove aged-out creatures (persists them first, then slices off `age_out[0]`)
  - `advance()` - increment generation number
- `GenerationStats` dataclass for statistics

### Phase 4: Simulation Engine

**4.1 Simulation Class** (`simulation.py`)
- `Simulation` class:
  - `from_config(config_path, db_path=None)` - factory method
  - `__init__(config_path, db_path=None)` - initialize from config
  - `initialize()` - create database, initial population, breeders
  - `run()` - execute all generations, return SimulationResults
  - `execute_generation(generation_number)` - single generation cycle
  - Database path logic: default to config directory with timestamp
- `SimulationResults` dataclass:
  - simulation_id, seed, status, generations_completed
  - final_population_size, database_path, config
  - start_time, end_time, duration_seconds

**4.2 Initial Population Creation**
- Sample founders from initial genotype frequencies
- Assign sexes according to initial_sex_ratio
- Set birth_generation=0, inbreeding_coefficient=0.0
- Sample individual lifespans from config range
- Initialize litters_remaining from config
- Initialize aging-out list: append founders to `age_out[lifespan]` (relative to generation 0)
- Ensure aging-out list is large enough to hold all possible aging-out generations

**4.3 Reproduction Logic**
- Gamete formation: for each trait, randomly select one allele from diploid pair
- Sex-linked handling: different logic for X-linked traits (males contribute single allele)
- Independent assortment: each trait independent
- Offspring creation: combine gametes, assign sex, calculate inbreeding coefficient
- Add offspring to population with current_generation for aging-out list calculation

### Phase 5: Database Persistence

**5.1 Creature Persistence**
- Batch insert creatures when removed from working pool
- Batch insert creature_genotypes (one row per trait, iterate through genome list)
- Handle `remove_ineligible_immediately` flag:
  - If true: persist when breeding age exceeded or litters_remaining <= 0
  - If false: persist when age >= lifespan (from aging-out list)
- When persisting from aging-out list: process `age_out[0]`, then slice it off

**5.2 Generation Statistics Persistence**
- Insert into `generation_stats` (demographics)
- Batch insert into `generation_genotype_frequencies` (one row per genotype)
- Batch insert into `generation_trait_stats` (allele freqs, heterozygosity, diversity)
- Use transactions for atomicity

**5.3 Simulation Metadata**
- Insert simulation record with seed, config (as TEXT), status
- Update status during execution (pending → running → completed)
- Update generations_completed after each generation
- Set end_time and final_population_size on completion

### Phase 6: Testing

**6.1 Unit Tests**
- Test each model class independently
- Test configuration validation
- Test database schema creation
- Test gamete formation and inheritance
- Test breeding eligibility logic
- Test inbreeding coefficient calculation
- Test aging-out list management

**6.2 Integration Tests**
- End-to-end simulation runs
- Mendelian ratio validation (3:1 ratio test)
- Hardy-Weinberg equilibrium test (random breeding)
- Data persistence verification
- Reproducibility test (same seed = same results)

**6.3 Test Fixtures**
- Sample config files for different scenarios
- Helper functions for creating test creatures
- Database fixtures (in-memory SQLite for tests)

## Key Implementation Details

**Random Number Generation:**
- Use `numpy.random.Generator` with explicit seed
- Store seed in database for reproducibility
- Pass RNG instance to all random operations

**Genome Representation:**
- In-memory: `List[str]` indexed by trait_id (0-99), each element is genotype string
- Database: normalized `creature_genotypes` table
- When persisting: iterate through genome list, insert row for each trait_id with non-None genotype

**Aging-Out List Structure:**
- `age_out: List[List[Creature]]` where index represents generations from current
- `age_out[0]` = creatures aging out in current generation
- `age_out[1]` = creatures aging out next generation
- When creature created: calculate `relative_generation = birth_gen + lifespan - current_gen`
- Append creature to `age_out[relative_generation]` (extend list if needed)
- When generation advances: process `age_out[0]`, then `age_out = age_out[1:]`

**Relationship Coefficient (Simplified Phase 1):**
- For unrelated parents: r = 0.0
- For siblings: r = 0.5 (check if share both parents)
- For parent-offspring: r = 0.5 (check if one is parent of other)
- For half-siblings: r = 0.25 (check if share one parent)
- For first cousins: r = 0.125 (traverse up 2 generations)
- Full pedigree traversal can be added later if needed

**Breeder Distribution:**
- Create list of breeder instances according to config counts
- Distribute pairs to breeders in round-robin or weighted fashion
- Each breeder selects pairs from eligible pools

**Performance Considerations:**
- Use batch inserts for database operations
- Maintain aging-out list for O(1) lookup (after initial setup)
- Calculate statistics before creature removal
- Use NumPy arrays where beneficial
- Index database queries appropriately

## Success Criteria

- Can run basic Mendelian simulation (single trait, 100 creatures, 50 generations)
- Random and selective breeding strategies work
- Test suite achieving >80% coverage
- Performance targets met for medium simulations
- Deterministic with same seed
- Database persists correctly with all relationships

## Implementation Order

1. Project setup and dependencies
2. Exception classes and database schema
3. Configuration system
4. Trait and Creature models
5. Breeder implementations
6. Population model (with aging-out list)
7. Generation model
8. Simulation engine
9. Database persistence
10. Comprehensive testing

## Notes

- Reporting/export functionality will be implemented in a later phase
- Focus on simulation engine correctness and performance
- Ensure all database relationships are properly maintained
- Aging-out list must be properly initialized and maintained throughout simulation

