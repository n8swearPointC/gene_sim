# Genealogical Simulation System

A Python-based simulation system for modeling genetic inheritance, breeding strategies, and population dynamics across multiple generations.

## Features

- **Genetic Modeling**: Supports multiple inheritance patterns (Mendelian, sex-linked, polygenic, etc.)
- **Breeding Strategies**: Multiple breeder types (random, inbreeding avoidance, phenotype selection)
- **Multi-Generational Tracking**: Complete lineage and pedigree tracking
- **SQLite Persistence**: Efficient data storage and querying
- **Reproducible**: Seeded random number generation for deterministic results
- **Batch Analysis**: Comprehensive analytics and visualization tools for comparing breeding strategies

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Running a Simulation

```python
from gene_sim import Simulation

# Run simulation from config file
sim = Simulation.from_config('config.yaml')
results = sim.run()

# Access results
print(f"Simulation ID: {results.simulation_id}")
print(f"Database: {results.database_path}")
```

### Analyzing Results

The project includes a unified batch analysis tool for analyzing simulation results:

```bash
# Individual batch analysis (e.g., kennels-only)
python batch_analysis_unified.py --individual run4/run4a_kennels

# Compare kennels vs mills (total population)
python batch_analysis_unified.py --combined run4/run4a_kennels run4/run4b_mills run4/combined

# Compare kennels vs mills (show-quality animals only)
python batch_analysis_unified.py --combined-desired run4/run4a_kennels run4/run4b_mills run4/combined_desired
```

**For complete batch analysis documentation**, see `BATCH_ANALYSIS_DOCUMENTATION.md`.

## Documentation

See `docs/` directory for complete documentation:
- API Interface: `docs/api-interface.md`
- Database Schema: `docs/database-schema.md`
- Domain Models: `docs/domain-model.md`
- Configuration: `docs/config-example.yaml`
- Batch Analysis: `BATCH_ANALYSIS_DOCUMENTATION.md`

## Requirements

- Python 3.10+
- NumPy
- PyYAML
- Matplotlib (for charts)
- SQLite3 (built-in)

## License

[To be determined]

