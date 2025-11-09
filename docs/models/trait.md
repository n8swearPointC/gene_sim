# Trait Model - Genealogical Simulation

**Document Version:** 1.0  
**Date:** November 8, 2025  
**Status:** Complete

---

## 1. Overview

A **Trait** represents a heritable characteristic that can be passed from parents to offspring through genetic mechanisms. Traits are the observable or measurable features that result from an organism's genotype.

---

## 2. Core Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `trait_id` | Integer | Unique identifier for the trait (0-99, used as array index) |
| `name` | String | Human-readable name (e.g., "Eye Color", "Height") |
| `trait_type` | Enum | Type of inheritance pattern (SIMPLE_MENDELIAN, INCOMPLETE_DOMINANCE, CODOMINANCE, SEX_LINKED, POLYGENIC) |

**Design Note:** Trait IDs are integers (0-99) to enable efficient array-based storage of creature genotypes. Each creature's genome can be represented as an array where `genome[trait_id]` contains the genotype for that trait.

---

## 3. Trait Types

The system supports multiple inheritance patterns. The trait type determines how genotypes are inherited and expressed, but the actual genotype-to-phenotype mapping is stored explicitly in the genotypes table.

### 3.1 Simple Mendelian (Single Gene)
- Controlled by one gene with two or more alleles
- Clear dominance relationships
- Examples: ABO blood type, widow's peak, attached earlobes

**Example - Eye Color (Simple Dominant/Recessive):**
```yaml
trait_id: 0
name: "Eye Color"
trait_type: SIMPLE_MENDELIAN
genotypes:
  - genotype: "BB"
    phenotype: "Brown"
    initial_freq: 0.36
  - genotype: "Bb"
    phenotype: "Brown"
    initial_freq: 0.48
  - genotype: "bb"
    phenotype: "Blue"
    initial_freq: 0.16
```

### 3.2 Incomplete Dominance
- Neither allele is completely dominant
- Heterozygotes show intermediate phenotype
- Examples: Snapdragon flower color, human hair texture

**Example - Flower Color:**
```yaml
trait_id: 1
name: "Flower Color"
trait_type: INCOMPLETE_DOMINANCE
genotypes:
  - genotype: "RR"
    phenotype: "Red"
    initial_freq: 0.25
  - genotype: "RW"
    phenotype: "Pink"
    initial_freq: 0.50
  - genotype: "WW"
    phenotype: "White"
    initial_freq: 0.25
```

### 3.3 Codominance
- Both alleles fully expressed simultaneously
- Heterozygotes show both phenotypes
- Examples: ABO blood type, roan coat color in horses

**Example - Blood Type:**
```yaml
trait_id: 2
name: "ABO Blood Type"
trait_type: CODOMINANCE
genotypes:
  - genotype: "AA"
    phenotype: "Type A"
    initial_freq: 0.16
  - genotype: "AO"
    phenotype: "Type A"
    initial_freq: 0.32
  - genotype: "BB"
    phenotype: "Type B"
    initial_freq: 0.09
  - genotype: "BO"
    phenotype: "Type B"
    initial_freq: 0.18
  - genotype: "AB"
    phenotype: "Type AB"
    initial_freq: 0.08
  - genotype: "OO"
    phenotype: "Type O"
    initial_freq: 0.16
```

### 3.4 Sex-Linked
- Gene located on sex chromosome (X or Y)
- Different inheritance patterns for males vs females
- Examples: Color blindness, hemophilia

**Example - Color Blindness (X-linked Recessive):**
```yaml
trait_id: 3
name: "Red-Green Color Blindness"
trait_type: SEX_LINKED
genotypes:
  - genotype: "NN"
    phenotype: "Normal vision"
    sex: "female"
    initial_freq: 0.40
  - genotype: "Nc"
    phenotype: "Normal vision (carrier)"
    sex: "female"
    initial_freq: 0.10
  - genotype: "cc"
    phenotype: "Colorblind"
    sex: "female"
    initial_freq: 0.0025
  - genotype: "N"
    phenotype: "Normal vision"
    sex: "male"
    initial_freq: 0.47
  - genotype: "c"
    phenotype: "Colorblind"
    sex: "male"
    initial_freq: 0.0075
```

### 3.5 Polygenic
- Controlled by multiple genes
- Continuous variation in phenotype
- Examples: Height, skin color, intelligence

**Example - Height:**
```yaml
trait_id: 4
name: "Adult Height"
trait_type: POLYGENIC
genotypes:
  - genotype: "H1H1_H2H2_H3H3"
    phenotype: "180"  # cm
    initial_freq: 0.027
  - genotype: "H1H1_H2H2_H3h3"
    phenotype: "175"
    initial_freq: 0.054
  - genotype: "H1H1_H2H2_h3h3"
    phenotype: "170"
    initial_freq: 0.027
  # ... additional genotype combinations
  - genotype: "h1h1_h2h2_h3h3"
    phenotype: "150"  # cm
    initial_freq: 0.027
```

---

## 4. Trait Expression

The genotype-to-phenotype mapping is explicit in the configuration. Each genotype has a defined phenotype value.

---

## 5. Trait Configuration Format

Traits are defined in configuration files (YAML/JSON) for flexibility.

### 5.1 Configuration Structure

Each trait specifies:
- Basic metadata (id, name, type)
- All possible genotypes with their phenotypes
- Initial frequency distribution (normalized to sum to 1.0)

**Example Configuration:**

```yaml
traits:
  - trait_id: 0
    name: "Coat Color"
    trait_type: SIMPLE_MENDELIAN
    genotypes:
      - genotype: "BB"
        phenotype: "Black"
        initial_freq: 0.36
      - genotype: "Bb"
        phenotype: "Black"
        initial_freq: 0.48
      - genotype: "bb"
        phenotype: "Brown"
        initial_freq: 0.16
    
  - trait_id: 1
    name: "Body Size"
    trait_type: POLYGENIC
    genotypes:
      - genotype: "L1L1_L2L2_L3L3"
        phenotype: "70.0"
        initial_freq: 0.027
      - genotype: "L1L1_L2L2_L3s3"
        phenotype: "67.5"
        initial_freq: 0.054
      - genotype: "L1L1_L2L2_s3s3"
        phenotype: "65.0"
        initial_freq: 0.027
      # ... additional genotypes
      - genotype: "s1s1_s2s2_s3s3"
        phenotype: "50.0"
        initial_freq: 0.027
```

### 5.2 Frequency Normalization

The system will normalize frequencies if they don't sum to exactly 1.0:

```yaml
genotypes:
  - genotype: "BB"
    phenotype: "Black"
    initial_freq: 36  # Will be normalized to 0.36
  - genotype: "Bb"
    phenotype: "Black"
    initial_freq: 48  # Will be normalized to 0.48
  - genotype: "bb"
    phenotype: "Brown"
    initial_freq: 16  # Will be normalized to 0.16
# Total = 100, system normalizes each value by dividing by 100
```

---

## 6. Trait Validation Rules

When loading trait definitions, validate:

1. **Completeness**: All required fields present (trait_id, name, trait_type, genotypes list)
2. **Frequency sum**: Genotype frequencies sum to 1.0 (system will normalize if not)
3. **Type compatibility**: trait_type is valid enum value
4. **Unique IDs**: No duplicate trait_ids (each trait has unique integer 0-99)
5. **ID range**: Trait IDs must be in range 0-99
6. **Genotype uniqueness**: No duplicate genotype strings within a trait
7. **Sex-linked validation**: For SEX_LINKED traits, genotypes must specify sex field

---

## 7. Database Schema (SQLite)

```sql
-- Traits Table
-- Stores basic metadata for each trait
CREATE TABLE traits (
    trait_id INTEGER PRIMARY KEY CHECK(trait_id >= 0 AND trait_id < 100),
    name TEXT NOT NULL,
    trait_type TEXT NOT NULL CHECK(trait_type IN (
        'SIMPLE_MENDELIAN', 
        'INCOMPLETE_DOMINANCE', 
        'CODOMINANCE', 
        'SEX_LINKED', 
        'POLYGENIC'
    ))
);

-- Genotypes Table
-- Stores all possible genotypes for each trait with phenotype mapping and initial frequencies
CREATE TABLE genotypes (
    genotype_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trait_id INTEGER NOT NULL,
    genotype TEXT NOT NULL,    -- e.g., "BB", "Bb", "bb" or "L1L1_L2L2_L3L3"
    phenotype TEXT NOT NULL,   -- e.g., "Brown", "Blue", "70.0"
    sex TEXT,                  -- NULL for non-sex-linked, 'male'/'female' for sex-linked
    initial_freq REAL NOT NULL CHECK(initial_freq >= 0.0 AND initial_freq <= 1.0),
    FOREIGN KEY (trait_id) REFERENCES traits(trait_id) ON DELETE CASCADE,
    UNIQUE(trait_id, genotype, sex)
);

-- Indexes for efficient querying
CREATE INDEX idx_genotypes_trait ON genotypes(trait_id);
CREATE INDEX idx_genotypes_phenotype ON genotypes(trait_id, phenotype);
CREATE INDEX idx_traits_type ON traits(trait_type);

-- Validation: Ensure frequencies sum to 1.0 per trait
-- (This would be enforced in application logic during data loading)
```

**Design Notes:**
- Simple 2-table design: traits + genotypes
- `genotype` is a string that can represent single or multi-gene genotypes
- `phenotype` is a string (can be categorical like "Brown" or numeric like "70.0")
- `sex` column is NULL for non-sex-linked traits
- Initial frequencies are normalized during data loading to sum to 1.0 per trait_id
- All genotype-to-phenotype mappings are explicit in the database

**Example Data:**

```sql
-- Simple Mendelian trait (Eye Color)
INSERT INTO traits (trait_id, name, trait_type) 
VALUES (0, 'Eye Color', 'SIMPLE_MENDELIAN');

INSERT INTO genotypes (trait_id, genotype, phenotype, initial_freq) VALUES
(0, 'BB', 'Brown', 0.36),
(0, 'Bb', 'Brown', 0.48),
(0, 'bb', 'Blue', 0.16);

-- Sex-linked trait (Color Blindness)
INSERT INTO traits (trait_id, name, trait_type) 
VALUES (3, 'Color Blindness', 'SEX_LINKED');

INSERT INTO genotypes (trait_id, genotype, phenotype, sex, initial_freq) VALUES
(3, 'NN', 'Normal vision', 'female', 0.40),
(3, 'Nc', 'Normal vision (carrier)', 'female', 0.10),
(3, 'cc', 'Colorblind', 'female', 0.0025),
(3, 'N', 'Normal vision', 'male', 0.47),
(3, 'c', 'Colorblind', 'male', 0.0075);
```

---

## 8. Common Queries

**Querying traits by type:**
```sql
SELECT * FROM traits WHERE trait_type = 'SIMPLE_MENDELIAN';
```

**Finding all genotypes for a trait:**
```sql
SELECT genotype, phenotype, initial_freq 
FROM genotypes 
WHERE trait_id = 0
ORDER BY initial_freq DESC;
```

**Calculating genotype frequencies in actual population (not initial):**
```sql
-- This aggregates actual population data from creatures (defined in creature model)
SELECT 
    g.genotype,
    g.phenotype,
    COUNT(c.creature_id) * 1.0 / (SELECT COUNT(*) FROM creatures WHERE generation = ?) as frequency
FROM creatures c
JOIN genotypes g ON c.genotype_trait_0 = g.genotype AND g.trait_id = 0
WHERE c.generation = ?
GROUP BY g.genotype, g.phenotype
ORDER BY frequency DESC;
```

**Getting phenotype distribution for a trait:**
```sql
-- Aggregate by phenotype (multiple genotypes may map to same phenotype)
SELECT 
    g.phenotype,
    SUM(g.initial_freq) as total_freq
FROM genotypes g
WHERE g.trait_id = 0
GROUP BY g.phenotype
ORDER BY total_freq DESC;
```

---

## 9. Related Documents

- **Creature Model**: How traits are instantiated in individual organisms
- **Genetic System Architecture**: Detailed inheritance mechanics
- **Configuration System**: How trait definitions are loaded and validated
- **Requirements**: Overall system requirements

---

**Status:** Complete and ready for implementation.
