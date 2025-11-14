# Genealogical Simulation Project - GitHub Copilot Instructions

## Project Overview
A genealogical simulation system that models populations of creatures with genetic traits across multiple generations. The system simulates breeding strategies, genetic inheritance, mutations, and provides comprehensive post-simulation reporting and analysis.

## Core Domain Entities
- **Creatures**: Entities with diploid genomes, genotypes, and phenotypes
- **Traits**: Genetic characteristics supporting multiple inheritance patterns (simple Mendelian, incomplete dominance, codominance, sex-linked, polygenic)
- **Breeders**: Pluggable breeding strategies (random, selective, inbreeding avoidance; fitness-based in Phase 2)
- **Mutations**: Point mutations with configurable rates, tracked through generations with complete history (Phase 2)
- **Populations**: Groups of creatures evolving over generations with demographic tracking
- **Generations**: Time-series snapshots of population state
- **Simulations**: Complete experimental runs with configuration and results
- **Reporting**: Post-simulation charts, graphs, and data exports (CSV/JSON)

## Key Design Principles

### 1. Genetic Accuracy
- Implement Mendelian inheritance with expected ratios (3:1, 9:3:3:1, etc.)
- Maintain Hardy-Weinberg equilibrium under random mating with no selection
- Support sex-linked traits with correct inheritance patterns
- Validate mutation rates match configured parameters (Phase 2)

### 2. Extensibility
- Use strategy pattern for breeding algorithms (pluggable and testable)
- Define traits as data (YAML/JSON configuration), not code
- Support custom trait types through configuration
- Clear interfaces for extending functionality

### 3. Reproducibility
- All randomness must use seeded pRNG (NumPy random with explicit seed)
- Store pRNG seed with each simulation run for exact reproduction
- Same seed + configuration = identical results
- Deterministic behavior is critical for scientific validity

### Performance Requirements
- Small sim (100 creatures, 50 gen): < 5 seconds
- Medium sim (1,000 creatures, 100 gen): < 60 seconds
- Large sim (10,000 creatures, 100 gen): < 10 minutes
- Memory usage (1,000 creatures): < 500 MB
- Use NumPy arrays for genetic operations
- Batch database operations where possible
- Pre-aggregate statistics during simulation

### Quick Test Configuration
- For development testing, instead of truncating output of a full run, reduce the run size (presumably by reducing the number of years to simulate)
- Use `quick_test_config.yaml` for development tests

### 5. Data Integrity
- Complete lineage tracking (forward and backward traversal)
- All mutation events individually traceable (Phase 2)
- SQLite foreign keys enforce referential integrity
- ACID compliance ensures data consistency
- No data loss across generations

### 6. Reporting-First Architecture
- Design for post-simulation analysis, not real-time visualization
- Store all data in SQLite for efficient querying
- Support time-series queries (trait frequencies by generation)
- Enable lineage queries without loading entire simulation
- Optimize indexes for common reporting patterns

## Technology Stack
- **Language**: Python 3.10+
- **Database**: SQLite (built-in, no external server)
- **Numerical**: NumPy for efficient arrays and seeded random number generation
- **Visualization**: Matplotlib/Plotly (optional, for reporting)
- **Data Export**: Pandas for CSV/JSON and SQLite querying
- **Configuration**: YAML/JSON parsing
- **Testing**: pytest with >80% coverage target

## Code Style & Conventions

### Python Standards
- Follow PEP 8 style guidelines
- Use type hints for all function signatures and class attributes
- Prefer dataclasses or Pydantic models for data structures
- Use enums for trait types and other fixed sets of values
- Document all public APIs with docstrings (Google style)

### File Organization
- Main package: `gene_sim/` containing core simulation logic
- Domain models in `gene_sim/models/` package (creature, trait, breeder, population, generation)
- Simulation engine: `gene_sim/simulation.py` (main orchestration)
- Database layer in `gene_sim/database/` package (schema, connection)
- Configuration loading: `gene_sim/config.py`
- Post-simulation analytics in `analytics/` directory (root level, separate from main package)
- Tests mirror source structure in `tests/`

### Naming Conventions
- Classes: PascalCase (e.g., `Creature`, `Trait`, `RandomBreeder`)
- Functions/methods: snake_case (e.g., `select_mates`, `is_eligible_for_breeding`; `calculate_fitness` in Phase 2)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_TRAIT_ID`, `DEFAULT_MUTATION_RATE`)
- Database tables: plural snake_case (e.g., `creatures`, `traits`, `genotypes`)

### Error Handling
- Use custom exception classes for domain-specific errors
- Validate inputs at boundaries (configuration loading, API entry points)
- Fail fast with clear error messages
- Log errors with sufficient context for debugging

## Database Design

### SQLite Schema Principles
- Use foreign keys with ON DELETE CASCADE where appropriate
- Create indexes for common query patterns (birth_generation, trait_id, lineage)
- Store pRNG seed with each simulation for reproducibility
- Normalize where it improves query performance
- Use CHECK constraints for data validation (trait_id range 0-99, etc.)

### Query Optimization
- Prefer indexed columns in WHERE clauses
- Use batch inserts for generation data
- Aggregate statistics during simulation, not during reporting
- Support efficient time-series queries (generation-based filtering)

## Testing Requirements

### Test Coverage
- Target >80% code coverage
- Unit tests for all domain logic
- Integration tests for simulation workflows
- Validation tests for genetic accuracy (Mendelian ratios, Hardy-Weinberg)

### Test Organization
- One test file per source module
- Use fixtures for common test data (sample creatures, traits, populations)
- Test deterministic behavior with fixed seeds
- Validate performance targets in integration tests

## Configuration System

### Trait Definitions
- YAML/JSON format for trait configuration
- Validate trait definitions on load (frequencies sum to 1.0, unique IDs, etc.)
- Support trait_id range 0-99 (used as array indices)
- Explicit genotype-to-phenotype mappings (no implicit rules)

### Simulation Configuration
- Include initial population parameters
- Specify breeding strategy and parameters
- Set mutation rates and types (Phase 2)
- Define number of generations
- Include pRNG seed for reproducibility

## Documentation Standards

### Code Documentation
- Module-level docstrings explaining purpose and key concepts
- Class docstrings describing responsibilities and key attributes
- Function docstrings with parameters, return values, and examples
- Inline comments for complex genetic algorithms or non-obvious logic

### Architecture Documentation
- Keep `docs/requirements.md` updated with current scope
- Document domain models in `docs/models/` (one file per entity)
- Update `docs/domain-model.md` as entities are completed
- Document API contracts before implementation

## Current Development Phase
**Phase 1 Complete - Active Development**: Core simulation system is implemented and functional. Focus on:
- Enhancing analytics and reporting capabilities
- Improving test coverage (target >80%)
- Performance optimization for large populations
- Bug fixes and refinements
- **Phase 2 (Future)**: Mutations with complete tracking and history
- **Phase 2 (Future)**: Fitness-based breeding strategies

## When Writing Code

### Documentation-First Development
**CRITICAL**: When creating, modifying, or removing features or functionality:
1. **Update documentation FIRST** before writing any code or tests
   - Update `docs/requirements.md` with new/changed requirements
   - Update relevant domain model docs in `docs/models/`
   - Update database schema in `docs/database-schema.md` if database changes are needed
   - Document API contracts and interfaces before implementation
2. **Create an implementation plan** outlining the approach
   - Break down the work into logical steps
   - Identify affected components and dependencies
   - Consider edge cases and error handling
   - Define acceptance criteria
3. **Then write tests** based on the documented requirements and plan
4. **Then implement code** to satisfy the tests and documentation

This ensures:
- Requirements are clearly understood before implementation
- Implementation approach is thought through before coding
- API contracts are defined before code is written
- Documentation stays current and accurate
- Design decisions are explicit and reviewable
- Future maintainers understand the intent

### Before Implementing
1. Check existing domain model docs in `docs/models/`
2. Review requirements in `docs/requirements.md`
3. Check database schema in `docs/database-schema.md`
4. Ensure design aligns with SQLite-first reporting architecture
5. Consider performance implications for large populations
6. Review existing tests to understand current behavior

### During Implementation
1. Write tests alongside code (TDD approach)
2. Use type hints throughout
3. Validate inputs at module boundaries
4. Use seeded random number generation (never global random)
5. Batch database operations for performance

### After Implementation
1. Ensure tests pass and coverage meets target
2. Verify documentation accurately reflects implementation
3. Verify performance targets are met
4. Check that deterministic behavior works (same seed = same results)

## Common Patterns

### Random Number Generation
```python
import numpy as np

# Always use explicit generator with seed
rng = np.random.default_rng(seed=simulation.seed)

# Never use global random
# BAD: np.random.choice(...)
# GOOD: rng.choice(...)
```

### Trait ID Usage
- Trait IDs are integers 0-99, used as array indices
- Creature genomes stored as arrays: `genome[trait_id] = genotype`
- Validate trait_id range in all functions accepting trait_id

### Database Transactions
- Use transactions for generation-level operations
- Commit after each generation for data safety
- Use batch inserts for performance (creatures, genotypes)

## Setting Up Experimental Runs

The project uses a structured approach for organizing experimental runs with batch analysis capabilities. Each run is a complete experimental setup with consistent directory structure and scripts.

### Run Directory Structure

Each run (e.g., `run3/`, `run4/`, `run5/`) follows this standard structure:

```
runX/
├── README.md                  # Run documentation and research questions
├── runX_config.yaml           # Base configuration file
├── runX_execute.py            # Batch execution script
├── run_single_pass.py         # Quick test script (single simulation)
├── runXa_kennels/             # Output directory for kennel-dominated batch
│   ├── batch_config.yaml      # Modified config for this batch
│   ├── batch_results.json     # Aggregated results
│   └── *.db                   # Individual simulation databases
└── runXb_mills/               # Output directory for mill-dominated batch
    ├── batch_config.yaml      # Modified config for this batch
    ├── batch_results.json     # Aggregated results
    └── *.db                   # Individual simulation databases
```

### Creating a New Run

When setting up a new experimental run (e.g., run5, run6, etc.), follow these steps:

#### 1. Create Directory Structure
```python
# Create main run directory and subdirectories
run_dir/
  runXa_kennels/    # First experimental condition
  runXb_mills/      # Second experimental condition
```

#### 2. Create Configuration File (`runX_config.yaml`)

**Key elements to define:**
- `seed`: Base seed for reproducibility (use unique range per run)
- `years`: Simulation duration
- `mode`: Set to `monitor` for detailed tracking
- `initial_population_size`: Starting population
- `creature_archetype`: Lifespan, maturity, breeding parameters
- `target_phenotypes`: List of desirable traits to breed toward
- `undesirable_phenotypes`: List of traits to avoid
- `genotype_preferences`: Kennel club breeding preferences
- `breeders`: Initial breeder configuration (will be modified per batch)
- `traits`: Complete trait definitions with genotypes and frequencies

**Seed Range Convention:**
- Each run uses a unique 1000-seed range
- Run 2: 1000-2999
- Run 3: 3000-4999
- Run 4: 5000-6999
- Run 5: 7000-8999
- Batch A (kennels): base_seed + 0-14 (e.g., 7000-7014)
- Batch B (mills): base_seed + 1000-1014 (e.g., 8000-8014)

#### 3. Create Execution Script (`runX_execute.py`)

The execution script orchestrates batch runs with different breeder configurations:

```python
#!/usr/bin/env python
"""
Run X Execution Script - [Brief description of experiment]

Executes two batches:
- Batch A: [Configuration A, e.g., 19 kennels, 1 mill]
- Batch B: [Configuration B, e.g., 1 kennel, 19 mills]
"""

def run_batch(config_path, output_dir, num_runs, kennels, mills, base_seed):
    """Execute a batch with specified breeder configuration."""
    # Load base config
    # Modify breeder counts
    # Save modified config to output_dir/batch_config.yaml
    # Call batch_run.py with parameters
    
def main():
    """Execute both batches for Run X."""
    # Run Batch A (e.g., kennel-dominated)
    # Run Batch B (e.g., mill-dominated)
    # Display summary and next steps
```

**Key execution script features:**
- Modifies base config per batch (breeder counts)
- Calls `batch_run.py` with appropriate parameters
- Creates batch-specific config files
- Provides clear progress output and next steps

#### 4. Create Single-Pass Test Script (`run_single_pass.py`)

Quick test script for validation before full batch execution:

```python
#!/usr/bin/env python3
"""Single-pass execution with monitoring enabled."""

def run_single_simulation(config_path, run_name, seed):
    """Run one simulation for testing."""
    # Load config
    # Override seed and mode
    # Create output in single_pass_results/
    # Run simulation
    # Return database path

def main():
    """Run single configuration with monitoring."""
    # Use first seed from range
    # Create temp config
    # Execute simulation
    # Display results location
```

**Benefits:**
- Fast validation (one simulation vs. 30)
- Tests configuration correctness
- Verifies database creation
- Enables quick debugging

#### 5. Create Documentation (`README.md`)

Document the run's purpose and parameters:

**Required sections:**
- **Overview**: Brief description of experiment
- **Configuration**: Population size, duration, breeders
- **Experimental Design**: Batch details (seeds, conditions)
- **Traits**: Summary of trait configuration
- **Execution**: Commands to run single test and full batches
- **Comparison**: Table comparing to previous runs
- **Research Questions**: What this run aims to discover
- **Analysis**: Commands for post-run analysis
- **Expected Outcomes**: Hypotheses based on previous results

#### 6. Seed Selection Guidelines

**Choose unique seed ranges that:**
- Don't overlap with existing runs
- Use round numbers (multiples of 1000) for easy tracking
- Reserve 1000 seeds per run (even if only using 30)
- Follow the pattern: runX uses X000-X999 range

**Example:**
```yaml
# Run 5 configuration
seed: 7000  # Base seed for config file

# Batch A (kennels): seeds 7000-7014
# Batch B (mills): seeds 8000-8014
```

### Common Run Patterns

#### Standard Kennel vs Mill Comparison
Most runs compare selective (kennel) vs. volume (mill) breeding:
- **Batch A**: 19 kennels, 1 mill (95% selective breeding)
- **Batch B**: 1 kennel, 19 mills (95% volume breeding)
- **Runs**: 15 simulations per batch
- **Total**: 30 simulations per run

#### Run Evolution Pattern
- **Run 2**: Baseline (50 creatures, 15 years, 10 breeders)
- **Run 3**: Scale up population (200 creatures, 6 years, 20 breeders)
- **Run 4**: Extend timeframe (200 creatures, 20 years, 20 breeders)
- **Run 5**: Replicate run 3 (validation with different seeds)

### Execution Workflow

**Quick Test (Development):**
```bash
cd runX
python run_single_pass.py  # Test with one simulation
```

**Full Batch Execution:**
```bash
cd runX
python runX_execute.py     # Run all 30 simulations
```

**Analysis:**
```bash
# Individual batch analysis
python batch_analysis.py runX/runXa_kennels
python batch_analysis.py runX/runXb_mills

# Combined comparison
python batch_analysis_combined.py runX/runXa_kennels runX/runXb_mills

# Desired traits only
python batch_analysis_combined_desired.py runX/runXa_kennels runX/runXb_mills
```

### Best Practices

1. **Always test first**: Run `run_single_pass.py` before full batch
2. **Document research questions**: Clear hypotheses in README.md
3. **Use consistent naming**: Follow runX_* pattern for all files
4. **Unique seeds**: Never reuse seed ranges across runs
5. **Copy existing runs**: Use previous run as template (copy and modify)
6. **Version control**: Commit run setup before execution
7. **Compare parameters**: Include comparison table in README.md
8. **Plan analysis**: Define analysis approach before running

### Troubleshooting Run Setup

**Config validation errors:**
- Check trait frequencies sum to 1.0
- Verify trait_id values are 0-99
- Ensure genotype strings match trait definitions

**Import errors in scripts:**
- Verify parent directory added to sys.path
- Check from gene_sim.simulation import Simulation

**Execution failures:**
- Test with run_single_pass.py first
- Check batch_run.py exists in parent directory
- Verify YAML config is valid (use yaml.safe_load test)

**Database issues:**
- Ensure output directories exist (scripts create them)
- Check disk space for database files
- Verify SQLite installation

## References
- Full requirements: `docs/requirements.md`
- Domain model index: `docs/domain-model.md`
- Database schema overview: `docs/database-schema.md`
- Implementation plan: `IMPLEMENTATION_PLAN.md`
- Trait model specification: `docs/models/trait.md`
- Additional model docs: `docs/models/*.md`
- Analytics scripts: `analytics/` (comprehensive_analytics.py, chart_phenotype.py, etc.)
- Batch analysis tools: `BATCH_ANALYSIS_DOCUMENTATION.md` (batch_analysis.py, batch_analysis_combined.py, batch_analysis_combined_desired.py)
- Existing runs: `run2/`, `run3/`, `run4/`, `run5/` (use as templates)
