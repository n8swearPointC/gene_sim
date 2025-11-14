# Extinction Prevention Fixes - Implementation Summary

## Problem
Analysis of run2 showed that all 15 mill-heavy runs (1 kennel + 9 mills) went extinct, with males dying out between generations 30-103. Investigation revealed:

1. **Kennel overwhelmed**: The single kennel gave away 89% of offspring in generation 1, keeping only those needed for immediate replacement
2. **Mills rejected kennel offspring**: Mills filtered out ALL creatures with ANY undesirable phenotype, and kennel-produced offspring had multiple undesirable traits (Aggression, Hip Issues, Heart Defects, etc.)
3. **Population collapse**: With no breeding happening, population shrank to 8-10 creatures with only 1-2 males

## Solution Overview
Two complementary fixes were implemented:

### 1. Kennel Offspring Retention ("First Dibs")
**File**: `gene_sim/models/breeder.py` (KennelClubBreeder class)
**File**: `gene_sim/models/generation.py` (execute_cycle method)

Kennels now evaluate their own offspring against current parents BEFORE releasing offspring for trading:
- Compare each offspring's genotype quality to parents using tier scoring (0=optimal, 1=acceptable, 2=undesirable, 3=not configured)
- Keep offspring that are superior to parents
- Trade inferior parents to make room for superior offspring
- Respect capacity limits

**Implementation**:
- New method: `KennelClubBreeder._score_creature_genotypes()` - Counts genotypes by tier (optimal, acceptable, undesirable, not_configured)
- New method: `KennelClubBreeder.evaluate_offspring_vs_parents()` - Compares offspring to parents, returns keep/trade/release decisions
- Integration in `generation.py execute_cycle()` - Calls evaluation before normal replacement logic

**Example**:
- Parent1: 1 acceptable genotype (Ss)
- Parent2: 1 undesirable genotype (ss)
- Offspring1: 1 optimal genotype (SS) ← KEPT, Parent2 traded
- Offspring2: 1 acceptable genotype (Ss) ← Released (no better than Parent1)
- Offspring3: 1 undesirable genotype (ss) ← Released (no better than parents)

### 2. Mill Fallback Selection
**File**: `gene_sim/models/breeder.py` (MillBreeder class)

Mills now use fallback selection when ALL creatures have undesirable phenotypes:
- Count undesirable phenotypes per creature
- Filter to creatures with MINIMUM count
- Select pairs from this filtered pool
- Still prefer creatures with zero undesirable phenotypes when available

**Implementation**:
- New method: `MillBreeder._count_undesirable_phenotypes()` - Counts how many undesirable phenotypes a creature has
- Modified method: `MillBreeder.select_pairs()` - Uses fallback when strict filtering would remove everyone

**Example**:
- Creature A: 3 undesirable phenotypes (Small, White, Sick)
- Creature B: 2 undesirable phenotypes (Small, Sick)
- Creature C: 1 undesirable phenotype (Small)
- Creature D: 1 undesirable phenotype (White)

Without fallback: No pairs (all have undesirable) ← EXTINCTION
With fallback: Selects from C and D (minimum = 1 undesirable) ← SURVIVAL

## Testing
Created comprehensive test suites:

### Kennel Tests (`tests/test_kennel_offspring_retention.py`)
- ✅ `test_kennel_retains_superior_offspring` - Verifies kennels keep better offspring and trade worse parents
- ✅ `test_kennel_respects_capacity` - Ensures capacity limits are honored
- ✅ `test_kennel_no_offspring` - Handles empty offspring list
- ✅ `test_kennel_no_parents` - Handles empty parent list

### Mill Tests (`tests/test_mill_fallback_selection.py`)
- ✅ `test_mill_fallback_selects_minimum_undesirable` - Verifies fallback selects creatures with minimum undesirable count
- ✅ `test_mill_fallback_when_all_filtered` - Ensures fallback activates when all filtered out
- ✅ `test_mill_prefers_no_undesirable_when_available` - Confirms normal behavior unchanged when clean creatures exist
- ✅ `test_mill_count_undesirable_phenotypes` - Tests helper method accuracy

All 8 tests pass.

## Expected Impact
These fixes should prevent extinction in mill-heavy scenarios by:

1. **Increasing genetic diversity in mills**: Fallback ensures mills can still breed even when all creatures have some undesirable traits
2. **Improving kennel efficiency**: Kennels retain their best offspring instead of giving them all away, building superior breeding stock faster
3. **Reducing dependency on trading**: Each breeder type can maintain viable populations more independently

## Files Modified
- `gene_sim/models/breeder.py` - Added kennel offspring evaluation and mill fallback selection
- `gene_sim/models/generation.py` - Integrated kennel offspring retention into offspring distribution logic
- `docs/models/breeder.md` - Updated documentation with new behaviors
- `tests/test_kennel_offspring_retention.py` - New test file (4 tests)
- `tests/test_mill_fallback_selection.py` - New test file (4 tests)

## Next Steps
1. Run extinction-prone scenarios (1 kennel + 9 mills) to verify fixes work
2. Compare population dynamics to previous runs
3. Monitor for unintended side effects (e.g., too much retention causing other issues)
4. Consider adjusting kennel retention aggressiveness if needed (currently keeps ANY offspring better than worst parent)
