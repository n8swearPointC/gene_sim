# Breeder Model - Genealogical Simulation

**Document Version:** 1.0  
**Date:** November 8, 2025  
**Status:** Draft - In Progress

---

## 1. Overview

A **Breeder** selects mating pairs from pre-filtered pools of eligible creatures. Different breeder strategies implement different selection criteria (random, inbreeding avoidance, phenotype selection, etc.). Breeders do not handle eligibility filtering—they receive only eligible creatures and focus solely on pair selection.

Each breeder has a **maximum capacity** of creatures they can own (default: 7). When a breeder exceeds this capacity after offspring are produced, they must cull excess creatures to return to capacity.

---

## 2. Core Responsibilities

1. **Select mating pairs** from provided eligible creatures using strategy-specific criteria
2. **Return pairs** for reproduction (offspring created via gamete formation)
3. **Manage capacity** by culling excess creatures when breeder exceeds max_creatures limit

**Note:** Eligibility filtering (age limits, litters_remaining, is_alive) is handled by the simulation layer before creatures are passed to the breeder.

---

## 3. Breeder Types

### 3.1 Random Breeder
- Randomly pairs eligible males and females
- No selection bias
- Use case: Baseline, control simulations

### 3.2 Inbreeding Avoidance Breeder
- Calculates inbreeding coefficient for potential offspring using Wright's formula
- Uses parent inbreeding coefficients (from `creature.inbreeding_coefficient`) and relationship coefficient
- Avoids pairs that would produce offspring with high inbreeding coefficient
- Use case: Maintaining genetic diversity

### 3.3 Kennel Club Breeder
- Selects pairs based on target phenotypes from simulation configuration
- Follows guidelines from prestigious kennel clubs (e.g., breed standards, health requirements, lineage restrictions)
- **Intelligent pairing selection** (Added: November 2025):
  - **Genetic scoring system**: Evaluates all possible male-female pairings based on expected offspring quality
  - **Mendelian probability calculation**: Computes expected genotype distributions for offspring using Punnett square logic
  - **Weighted scoring**: Pairings scored based on probability of producing optimal (+100), acceptable (+10), or undesirable (-50) offspring genotypes
  - **Best pairing selection**: Selects highest-scoring pairings to maximize genetic improvement
  - **Performance caching**: Genotype pair scores cached in dual-indexed dictionary for O(1) lookups
  - **Strategic breeding**: Simulates real kennel club breeding decisions that consider genetic outcomes, not just parent quality
- **Always avoids undesirable genotypes**: Filters out creatures with configured undesirable genotypes when selecting breeding pairs
- **First dibs on own offspring**: Kennels get priority to keep their own offspring, retaining superior offspring while trading out inferior parents
  - **Offspring evaluation**: After breeding, compares each offspring's genotypes to both parents
  - **Retention decision**: Offspring with better genotype profile (fewer undesirable genotypes) are kept; inferior parents are marked for trading
  - **Capacity-aware**: Offspring retention respects capacity limits, keeping only the best improvements
  - **Trading**: Parents with worse genotypes are traded to other breeders to make room for superior offspring
- **Proactive genotype improvement**: Actively replaces sub-optimal parents (those with undesirable genotypes) with superior offspring (those without undesirable genotypes) as soon as they become available, not just at end of life
- **Prefers homozygous genotypes**: When selecting replacement creatures, prioritizes homozygous dominant (AA) or homozygous recessive (aa) genotypes over heterozygous (Aa) to stabilize desired traits
- May enforce rules such as: requiring specific phenotype ranges, limiting inbreeding within guidelines
- Uses same target_phenotypes as unrestricted phenotype breeder (defined at top-level config)
- Use case: Modeling formal breeding programs with established standards and genetic awareness

### 3.4 Mill Breeder
- Selects pairs based on target phenotypes from simulation configuration
- **Fallback selection strategy**: When all creatures have undesirable phenotypes, selects creatures with the LEAST number of undesirable phenotypes
  - **Phenotype scoring**: Counts undesirable phenotypes for each creature
  - **Best available selection**: Filters to creatures with minimum undesirable count
  - **Always produces offspring**: Ensures breeding always succeeds even when no perfect candidates exist
- Follows no other guidelines or restrictions
- Purely selects for desired phenotypes without concern for genetics or health beyond avoiding worst cases
- Uses same target_phenotypes as kennel club breeder (defined at top-level config)
- Use case: Modeling breeding programs focused solely on phenotype outcomes (puppy mills, kitten mills, etc.)

---

## 4. Capacity Management

### 4.1 Capacity Limits
- Each breeder has a `max_creatures` attribute (default: 7)
- Configurable per simulation, but typically set globally for all breeders
- Capacity includes all living, non-homed creatures owned by the breeder
- **Strictly enforced**: Breeders cannot keep offspring that would exceed their capacity

### 4.2 Offspring Assignment with Capacity Enforcement (FIXED: November 2025)
- **When triggered**: During offspring distribution phase after reproduction
- **Capacity enforcement**: System strictly enforces capacity limits at two points:
  1. **When breeders keep offspring from own litters**: Limited by available space (max_creatures - current_count)
  2. **When breeders claim offspring from other breeders**: Limited by remaining capacity
- **Proportional reduction**: If replacement needs exceed available capacity, needs are proportionally reduced
- **Capacity tracking**: Capacity info updated in real-time as offspring are kept/claimed and parents are removed

### 4.3 Offspring Distribution Process
1. **Group by breeder**: Offspring grouped by mother's breeder_id
2. **Calculate needs**: Each breeder calculates replacement needs (accounting for parents nearing end of life)
3. **Enforce capacity**: Replacement needs capped at available space (max_creatures - current_count)
4. **Keep best offspring**: Breeder selects best offspring up to capacity limit using `select_replacement()`
5. **Update capacity**: Capacity tracker updated as offspring kept and parents removed
6. **Cross-claims**: Other breeders can claim remaining offspring, subject to their own capacity limits
7. **Home excess**: Any unclaimed offspring are homed (marked `is_homed = True`, removed from breeding pool)

### 4.4 Capacity Tracking
- Tracked via `_get_breeder_capacity_info()` which returns (current_count, max_creatures, has_space)
- Current count includes all living, non-homed creatures owned by breeder
- Updated dynamically as offspring are kept and parents are removed/homed
- Prevents pool size explosion by capping total population at (num_breeders × max_creatures)

### 4.5 Database Tracking
- Capacity tracked via `breeders.max_creatures` column
- Ownership assignment respects capacity limits during offspring creation
- Transfers logged in `creature_ownership_history` table
- Homed status tracked via `creatures.is_homed` field

---

## 5. Ownership and Transfer Rules

### 5.1 Ownership Assignment
- **Initial ownership**: Founders may be assigned to breeders during population initialization
- **Offspring ownership**: Automatically assigned to the breeder who owns the **female parent**
- **Ownership persistence**: `breeder_id` field tracks current owner; `produced_by_breeder_id` tracks original breeding program (never changes)

### 5.2 Transfer Restrictions
- **No transfers until breeding**: Once assigned an owner, a creature will NOT be transferred until it produces offspring
- **Gestation/nursing protection**: Creatures that are gestating or nursing are NOT eligible for transfer
- **Transfer frequency**: Only ONE transfer event per cycle, occurring AFTER offspring are determined

### 5.3 Breeder-Specific Transfer Behavior

#### Kennel Club Breeders
- **Male transfers**: Regular transfers of males between kennels
- **Female transfers**: Females transferred approximately 3 times during lifetime (configurable via `kennel_female_transfer_count`)
- **Acquisition restrictions**: Will NOT accept creatures that originated from mill breeders (`produced_by_breeder_id` check)
- **Quality focus**: Maintains breeding stock quality through selective acquisition
- **Proactive replacements**: In addition to standard end-of-life replacements, kennels actively replace parents with undesirable genotypes when superior offspring become available
- **First dibs on offspring**: When multiple breeders need replacements, kennels get first opportunity to claim offspring from other kennels (before they are homed to pet families)

#### Mill Breeders
- **Low transfer probability**: Much less likely to transfer creatures out
- **Phenotype avoidance**: Always avoid breeding creatures with undesirable phenotypes (from configuration)
- **No genetic concerns**: Does not avoid undesirable genotypes (no concern for hidden genetics)
- **Female replacement**: May acquire offspring from own breeding program and transfer existing female out of breeding pool
- **Retirement transfers**: Transferred females go to homes (effectively retired - spayed/neutered, no longer in breeding pool)
- **No ethical restrictions**: Will accept creatures from any source

#### Random/Inbreeding Avoidance Breeders
- **Baseline behavior**: Follow standard transfer probabilities
- **No special restrictions**: Accept creatures from any source

### 5.4 Transfer Database Tracking
- **Current owner**: `creatures.breeder_id` (updated on transfer)
- **Transfer history**: `creature_ownership_history` table logs all transfers with `transfer_generation`
- **Original breeder**: `creatures.produced_by_breeder_id` (immutable - tracks origin for kennel club restrictions)

---

## 6. Interface

```python
class Breeder:
    def select_pairs(
        self, 
        eligible_males: List[Creature], 
        eligible_females: List[Creature],
        num_pairs: int,
        rng: np.random.Generator
    ) -> List[Tuple[Creature, Creature]]:
        """
        Selects mating pairs from eligible creatures.
        
        Args:
            eligible_males: Pre-filtered list of eligible male creatures
            eligible_females: Pre-filtered list of eligible female creatures
            num_pairs: Number of pairs to select
            rng: Seeded random number generator
            
        Returns:
            List of (male, female) tuples for reproduction
        """
        pass
```

**Note:** Breeders receive pre-filtered eligible creatures. The simulation layer handles eligibility filtering (age limits, litters_remaining, is_alive) before calling the breeder. Breeders focus solely on pair selection strategy.

---

## 7. Implementation Notes

- **Memory-only:** Breeders operate on in-memory working pool (no database queries)
- **Seeded randomness:** All random operations use provided `rng` for reproducibility
- **Pair validation:** Breeders may enforce additional constraints (e.g., no self-pairing, max inbreeding coefficient)
- **Strategy pattern:** Different breeders are interchangeable via configuration
- **Breeder distribution:** The number of breeders of each type is determined by simulation configuration (actual counts, not normalized percentages)
- **Ownership transfers:** Handled by generation cycle logic, not by individual breeder classes
- **Transfer timing**: Occurs once per cycle, after offspring determination but before aged-out removal
- **Capacity enforcement**: Checked during offspring assignment; excess offspring transferred or homed

---

## 8. Database Schema

No database schema required. Breeders are runtime strategy objects configured per simulation. The `max_creatures` attribute is stored in the `breeders` table for tracking purposes.

```sql
CREATE TABLE breeders (
    breeder_id INTEGER PRIMARY KEY,
    simulation_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    breeder_type TEXT NOT NULL,
    max_creatures INTEGER NOT NULL DEFAULT 7,
    -- other breeder attributes
    FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
);
```

---

**Status:** Draft - Ready for review. Next: Population Model specification.

