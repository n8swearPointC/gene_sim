# Python API Interface Specification - Genealogical Simulation

**Document Version:** 1.0  
**Date:** November 8, 2025  
**Status:** Complete

---

## 1. Overview

The genealogical simulation system provides a **Python API-first interface**. The API is designed for programmatic use, enabling researchers and developers to run simulations, analyze results, and integrate with the scientific Python ecosystem.

### 1.1 Design Philosophy

- **Python API is primary** - No CLI required, though optional CLI wrappers may be added later
- **Database persistence** - SQLite databases persist after simulation completion for post-analysis
- **Direct database access** - Users can query SQLite databases directly with SQL or pandas
- **Simple and flexible** - Minimal API surface with maximum power

### 1.2 Key Features

- Run simulations from configuration files
- Access simulation results and metadata
- Query persisted databases for analysis
- Generate reports and visualizations
- Export data in multiple formats

---

## 2. Core API Structure

### 2.1 Main Classes

#### `gene_sim.Simulation`

Main simulation class that orchestrates the entire simulation lifecycle.

**Location:** `gene_sim/simulation.py`

#### `gene_sim.SimulationResults`

Dataclass containing simulation results and metadata.

**Location:** `gene_sim/simulation.py`

#### `gene_sim.load_config()`

Helper function for loading and validating configuration files.

**Location:** `gene_sim/config.py`

---

## 3. Database Path Strategy

### 3.1 Default Behavior

By default, the database is created in the **same directory as the configuration file**.

**Naming Convention:**
- Format: `simulation_YYYYMMDD_HHMMSS.db`
- Example: `simulation_20251108_143022.db`
- Timestamp is generated when simulation is initialized

**Example:**
```python
# Config file: /projects/my_sim/config.yaml
# Database: /projects/my_sim/simulation_20251108_143022.db

sim = Simulation.from_config('/projects/my_sim/config.yaml')
results = sim.run()
# results.database_path = '/projects/my_sim/simulation_20251108_143022.db'
```

### 3.2 Custom Database Location

Users can specify a custom database path:

```python
# Specify full path
sim = Simulation.from_config('config.yaml', db_path='/data/simulations/my_sim.db')

# Or use relative path (relative to current working directory)
sim = Simulation.from_config('config.yaml', db_path='output/my_sim.db')
```

### 3.3 Database Persistence

- **Databases persist** after simulation completion
- Designed for post-simulation analysis and reporting
- Can be queried directly with SQLite tools or pandas
- Multiple simulations can share the same database (each has unique `simulation_id`)

---

## 4. Usage Examples

### 4.1 Basic Simulation Run

```python
from gene_sim import Simulation

# Load config and create simulation
sim = Simulation.from_config('config.yaml')

# Run simulation
results = sim.run()

# Access results
print(f"Simulation ID: {results.simulation_id}")
print(f"Generations completed: {results.generations_completed}")
print(f"Database path: {results.database_path}")
print(f"Duration: {results.duration_seconds:.2f} seconds")
```

### 4.2 Custom Database Location

```python
from gene_sim import Simulation

# Specify custom database location
sim = Simulation.from_config(
    'config.yaml',
    db_path='/data/simulations/experiment_1.db'
)

results = sim.run()
# Database is at /data/simulations/experiment_1.db
```

### 4.3 Accessing Simulation Database

```python
from gene_sim import Simulation
import sqlite3
import pandas as pd

# Run simulation
sim = Simulation.from_config('config.yaml')
results = sim.run()

# Query database directly with SQLite
conn = sqlite3.connect(results.database_path)
cursor = conn.cursor()
cursor.execute("""
    SELECT generation, population_size 
    FROM generation_stats 
    WHERE simulation_id = ?
    ORDER BY generation
""", (results.simulation_id,))
data = cursor.fetchall()
conn.close()

# Or use pandas for easier analysis
df = pd.read_sql("""
    SELECT generation, population_size, births, deaths
    FROM generation_stats
    WHERE simulation_id = ?
    ORDER BY generation
""", sqlite3.connect(results.database_path), params=(results.simulation_id,))
```

### 4.4 Querying Trait Frequencies

```python
from gene_sim import Simulation
import pandas as pd
import sqlite3

sim = Simulation.from_config('config.yaml')
results = sim.run()

# Get genotype frequencies over time for trait 0
df = pd.read_sql("""
    SELECT g.generation, ggf.genotype, ggf.frequency
    FROM generation_genotype_frequencies ggf
    JOIN generation_stats g ON 
        ggf.simulation_id = g.simulation_id AND 
        ggf.generation = g.generation
    WHERE ggf.simulation_id = ? AND ggf.trait_id = 0
    ORDER BY g.generation, ggf.frequency DESC
""", sqlite3.connect(results.database_path), params=(results.simulation_id,))

# Plot trait frequency over time
import matplotlib.pyplot as plt
for genotype in df['genotype'].unique():
    subset = df[df['genotype'] == genotype]
    plt.plot(subset['generation'], subset['frequency'], label=genotype)
plt.xlabel('Generation')
plt.ylabel('Frequency')
plt.legend()
plt.show()
```

### 4.5 Multiple Simulations in Same Database

```python
from gene_sim import Simulation

# Run multiple simulations, storing in same database
db_path = 'comparison_study.db'

# Simulation 1: Random breeding
sim1 = Simulation.from_config('config_random.yaml', db_path=db_path)
results1 = sim1.run()

# Simulation 2: Selective breeding
sim2 = Simulation.from_config('config_selective.yaml', db_path=db_path)
results2 = sim2.run()

# Compare results using simulation_id
# results1.simulation_id and results2.simulation_id are different
```

---

## 5. Module Structure

### 5.1 Package Organization

```
gene_sim/
├── __init__.py          # Public API exports
├── simulation.py         # Simulation class and SimulationResults
├── config.py            # Configuration loading and validation
├── models/              # Domain models
│   ├── creature.py
│   ├── trait.py
│   ├── breeder.py
│   ├── population.py
│   └── generation.py
├── database/            # Database layer
│   ├── __init__.py
│   ├── schema.py        # Schema creation
│   └── queries.py       # Common query helpers (optional)
└── reporting/           # Reporting and visualization (optional)
    ├── __init__.py
    ├── charts.py
    └── export.py
```

### 5.2 Public API Exports (`gene_sim/__init__.py`)

```python
"""
Genealogical Simulation System

Main API:
    Simulation - Main simulation class
    SimulationResults - Simulation results dataclass
    load_config - Configuration loading helper
"""

from .simulation import Simulation, SimulationResults
from .config import load_config

__all__ = ['Simulation', 'SimulationResults', 'load_config']
```

### 5.3 Internal Modules

Internal modules are not part of the public API but may be accessed if needed:
- `gene_sim.models.*` - Domain model classes
- `gene_sim.database.*` - Database utilities
- `gene_sim.reporting.*` - Reporting utilities

---

## 6. API Reference

### 6.1 `Simulation.from_config()`

**Class Method** - Convenience factory method for creating simulations from config files.

```python
@classmethod
def from_config(
    config_path: str,
    db_path: str | None = None
) -> Simulation:
    """
    Create a Simulation instance from a configuration file.
    
    Args:
        config_path: Path to YAML/JSON configuration file
        db_path: Optional path for SQLite database. If None, database is
                 created in the same directory as config_path with name
                 'simulation_YYYYMMDD_HHMMSS.db'
    
    Returns:
        Initialized Simulation instance
    
    Raises:
        FileNotFoundError: If config_path doesn't exist
        ValidationError: If configuration is invalid
    """
```

**Example:**
```python
sim = Simulation.from_config('config.yaml')
# Database will be: <config_dir>/simulation_20251108_143022.db
```

### 6.2 `Simulation.__init__()`

**Constructor** - Direct initialization (less common than `from_config()`).

```python
def __init__(
    self,
    config_path: str,
    db_path: str | None = None
) -> None:
    """
    Initialize simulation from configuration file.
    
    Args:
        config_path: Path to YAML/JSON configuration file
        db_path: Optional path for SQLite database. If None, database is
                 created in the same directory as config_path with name
                 'simulation_YYYYMMDD_HHMMSS.db'
    """
```

### 6.3 `Simulation.run()`

**Method** - Execute the complete simulation.

```python
def run(self) -> SimulationResults:
    """
    Execute complete simulation from initialization through all generations.
    
    Returns:
        SimulationResults object with metadata, database path, and summary
    
    Raises:
        SimulationError: If simulation fails during execution
    """
```

### 6.4 `SimulationResults`

**Dataclass** - Simulation results and metadata.

```python
@dataclass
class SimulationResults:
    """Results from a completed simulation."""
    
    simulation_id: int              # Database ID
    seed: int                      # pRNG seed used
    status: str                    # 'completed', 'failed', or 'cancelled'
    generations_completed: int     # Actual generations run
    final_population_size: int     # Population at end (None if not completed)
    database_path: str             # Path to SQLite database
    config: dict                   # Configuration used (parsed from stored config text)
    start_time: datetime           # Simulation start timestamp
    end_time: datetime             # Simulation end timestamp
    duration_seconds: float        # Execution time (end_time - start_time)
```

---

## 7. Error Handling

### 7.1 Exception Hierarchy

```python
class GeneSimError(Exception):
    """Base exception for gene_sim package."""
    pass

class ConfigurationError(GeneSimError):
    """Configuration validation or loading error."""
    pass

class SimulationError(GeneSimError):
    """Simulation execution error."""
    pass

class DatabaseError(GeneSimError):
    """Database operation error."""
    pass
```

### 7.2 Common Error Scenarios

**Invalid Configuration:**
```python
try:
    sim = Simulation.from_config('invalid_config.yaml')
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

**Simulation Failure:**
```python
try:
    results = sim.run()
except SimulationError as e:
    print(f"Simulation failed: {e}")
    # Check results.status for details
```

---

## 8. Integration with Scientific Python Stack

### 8.1 Pandas Integration

```python
import pandas as pd
import sqlite3

results = sim.run()
conn = sqlite3.connect(results.database_path)

# Load generation statistics
df_stats = pd.read_sql("""
    SELECT * FROM generation_stats 
    WHERE simulation_id = ?
""", conn, params=(results.simulation_id,))

# Load genotype frequencies
df_genotypes = pd.read_sql("""
    SELECT * FROM generation_genotype_frequencies 
    WHERE simulation_id = ?
""", conn, params=(results.simulation_id,))
```

### 8.2 Matplotlib/Plotly Integration

```python
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3

results = sim.run()
df = pd.read_sql("""
    SELECT generation, population_size 
    FROM generation_stats 
    WHERE simulation_id = ?
    ORDER BY generation
""", sqlite3.connect(results.database_path), params=(results.simulation_id,))

plt.plot(df['generation'], df['population_size'])
plt.xlabel('Generation')
plt.ylabel('Population Size')
plt.title('Population Size Over Time')
plt.show()
```

### 8.3 Jupyter Notebook Usage

The API is designed to work seamlessly in Jupyter notebooks:

```python
# In a Jupyter notebook cell
from gene_sim import Simulation
import pandas as pd
import matplotlib.pyplot as plt

# Run simulation
sim = Simulation.from_config('config.yaml')
results = sim.run()

# Quick analysis
df = pd.read_sql("SELECT * FROM generation_stats WHERE simulation_id = ?",
                 sqlite3.connect(results.database_path),
                 params=(results.simulation_id,))
df.plot(x='generation', y='population_size')
```

---

## 9. Best Practices

### 9.1 Database Management

- **Use descriptive database names** when running multiple experiments
- **Keep config files with databases** for reproducibility
- **Use same database** for related experiments (different `simulation_id` values)

### 9.2 Configuration Management

- **Store config files** with descriptive names
- **Version control configs** to track experiment parameters
- **Use relative paths** in configs when possible

### 9.3 Performance

- **Close database connections** when done querying
- **Use batch queries** for large datasets
- **Index queries** leverage database indexes (see [Database Schema](database-schema.md))

---

## 10. References

- **Simulation Model**: [models/simulation.md](models/simulation.md)
- **Database Schema**: [database-schema.md](database-schema.md)
- **Configuration Format**: [config-example.yaml](config-example.yaml)
- **Domain Models**: [domain-model.md](domain-model.md)

---

**Status:** Complete - Ready for implementation

