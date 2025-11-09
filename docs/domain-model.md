# Domain Model - Genealogical Simulation

**Document Version:** 1.0  
**Date:** November 8, 2025  
**Status:** Draft - In Progress

---

## 1. Overview

This document serves as an index to the core domain entities in the genealogical simulation system. Each entity has its own detailed specification document.

### 1.1 Key Entities

The simulation system is built around these core domain entities:

| Entity | Status | Document |
|--------|--------|----------|
| **Trait** | ✅ Complete | [models/trait.md](models/trait.md) |
| **Creature** | ✅ Complete | [models/creature.md](models/creature.md) |
| **Breeder** | 🔄 In Progress | [models/breeder.md](models/breeder.md) |
| **Population** | 📋 Planned | [models/population.md](models/population.md) |
| **Generation** | 📋 Planned | [models/generation.md](models/generation.md) |
| **Mutation** | 📋 Phase 2 | [models/mutation.md](models/mutation.md) |
| **Simulation** | 📋 Planned | [models/simulation.md](models/simulation.md) |

---

## 2. Entity Summaries

### 2.1 Trait
Genetic characteristics that can be inherited. Supports multiple inheritance patterns (Mendelian, sex-linked, polygenic, etc.). Defines how genotypes map to phenotypes.

**Key Concepts:** Alleles, dominance, trait types, expression rules

**See:** [models/trait.md](models/trait.md)

### 2.2 Creature
Individual organism with a genome and expressed traits. Contains genetic material (genotype) and observable characteristics (phenotype). Creatures persist across multiple generations.

**Key Concepts:** Genome, genotype, phenotype, lineage, birth_generation, litter_count, breeding eligibility

**See:** [models/creature.md](models/creature.md)

### 2.3 Breeder
Strategy for selecting mating pairs from a population. Different breeders implement different selection criteria. Must respect breeding eligibility (age and litter limits for females).

**Key Concepts:** Selection strategies, mate selection, breeding eligibility (fitness-based selection in Phase 2)

**See:** [models/breeder.md](models/breeder.md) _(next)_

### 2.4 Population
Collection of creatures alive at a given point in the simulation. Creatures persist across generations, so population includes creatures from multiple birth generations. Manages demographic data and genetic diversity metrics.

**Key Concepts:** Size, composition, diversity, statistics, age distribution

**See:** [models/population.md](models/population.md) _(planned)_

### 2.5 Generation
Single iteration in the simulation timeline. Represents the state of the population at a specific point. Generation number is stored in memory (not database); only creature birth_generation is persisted.

**Key Concepts:** Generation number (in-memory), timestamp, population snapshot

**See:** [models/generation.md](models/generation.md) _(planned)_

### 2.6 Mutation
Genetic change event. Tracks when and where mutations occur, and how they propagate through lineages.

**Key Concepts:** Mutation types, rates, tracking, inheritance

**See:** [models/mutation.md](models/mutation.md) _(Phase 2)_

### 2.7 Simulation
Complete experimental run with configuration. Orchestrates all entities and manages the overall simulation lifecycle.

**Key Concepts:** Configuration, execution, state management, results

**See:** [models/simulation.md](models/simulation.md) _(planned)_

---

## 3. Entity Relationships

High-level relationships between entities:

```
Simulation
  ├── Configuration
  │   ├── Trait Definitions
  │   ├── Breeder Strategy
  │   └── Initial Population Parameters
  │
  └── Generations (timeline)
      └── Generation[N]
          ├── Population
          │   └── Creatures[]
          │       ├── Genome (Genotype)
          │       ├── Phenotype (expressed traits)
          │       └── Parents (lineage)
          │
          └── Statistics
              ├── Trait Frequencies
              └── Diversity Metrics
```

**Detailed relationship diagrams** will be provided in each entity's document.

---

## 4. Data Flow

### 4.1 Simulation Initialization
1. Load configuration (traits, breeding strategy, parameters)
2. Create initial population 
3. Assign genotypes based on allele frequencies

### 4.2 Generation Cycle
1. Breeder selects mating pairs
2. Reproduce (genetic recombination)
3. Create offspring with new genotypes
4. Record generation data to database
5. Calculate and store statistics
6. Advance to next generation

### 4.3 Post-Simulation Analysis
1. Query historical data from SQLite
2. Generate reports and visualizations
3. Export data in requested formats
4. Compare across multiple simulation runs

---

## 5. Cross-Cutting Concerns

### 5.1 Randomness & Reproducibility
- All random operations use seeded pRNG (NumPy)
- Seed stored with simulation for exact reproduction
- Critical for: gamete formation, mate selection (mutations in Phase 2)

### 5.2 Data Persistence
- SQLite database for all simulation data
- Efficient querying for reporting
- Foreign key constraints for referential integrity
- Indexes optimized for time-series and lineage queries

### 5.3 Performance Optimization
- Batch database operations where possible
- Minimize memory footprint (don't load all generations)
- Use NumPy arrays for genetic operations
- Pre-calculate commonly queried statistics

---

## 6. Next Steps

### Phase 1 (Current)
1. ✅ **Trait Model** - Complete
2. ✅ **Creature Model** - Complete
3. 🔄 **Breeder Model** - Next priority
4. **Population/Generation Models** - Container entities
5. **Simulation Model** - Orchestration layer

### Phase 2 (Future)
- **Mutation Model** - Advanced genetic changes

---

## 7. Related Documents

- [Requirements](requirements.md) - Overall system requirements
- [Genetic System Architecture](genetic-architecture.md) - Detailed genetics mechanics _(planned)_
- [API Contracts](api.md) - Public interfaces _(planned)_
- [Database Schema](database-schema.md) - Complete SQLite schema _(planned)_

---

**Status:** Domain model index created. Entity models being developed individually.
