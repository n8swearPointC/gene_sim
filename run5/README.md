# Run 5: Kennel vs Mill Breeding Comparison

## Overview
Run 5 is a copy of Run 3, testing kennel vs mill breeding strategies with a larger population.

## Configuration
- **Population**: 200 creatures
- **Duration**: 6 years
- **Total Breeders**: 20
- **Breeder Split**: 19/1 (95% kennels / 5% mills)

## Experimental Design

### Batch A: Kennel-Dominated
- **Kennel Club Breeders**: 19 (95%)
- **Mill Breeders**: 1 (5%)
- **Runs**: 15 simulations
- **Seeds**: 7000-7014

### Batch B: Mill-Dominated
- **Kennel Club Breeders**: 1 (5%)
- **Mill Breeders**: 19 (95%)
- **Runs**: 15 simulations
- **Seeds**: 8000-8014

## Traits
Same trait configuration as Run 3:
- **3 Desirable Traits**: Emerald Eyes (dominant), Silky Coat (recessive), Long Tail (recessive)
- **12 Undesirable Traits**: Mix of dominant and recessive undesirable phenotypes

## Execution

### Quick Test (Single Run)
```bash
cd run5
python run_single_pass.py
```

### Full Batch Execution
```bash
cd run5
python run5_execute.py
```

## Comparison to Previous Runs
| Parameter | Run 2 | Run 3 | Run 4 | Run 5 |
|-----------|-------|-------|-------|-------|
| Population | 50 | 200 | 200 | 200 |
| Years | 15 | 6 | 20 | 6 |
| Total Breeders | 10 | 20 | 20 | 20 |
| Breeder Split | 9/1 (90/10) | 19/1 (95/5) | 19/1 (95/5) | 19/1 (95/5) |
| Seeds (Kennels) | 1000-1014 | 3000-3014 | 5000-5014 | 7000-7014 |
| Seeds (Mills) | 2000-2014 | 4000-4014 | 6000-6014 | 8000-8014 |

## Research Questions
1. Do desirable traits increase over 6 years in kennel-dominated populations?
2. How do mill-dominated populations handle trait diversity?
3. What is the impact of inbreeding with 200 creatures over 6 years?
4. How do results compare to Run 3 (same parameters, different seeds)?

## Analysis

After running both batches, use the batch analysis scripts:

```bash
# Analyze kennel-dominated batch
cd ..
python batch_analysis.py run5/run5a_kennels

# Analyze mill-dominated batch  
python batch_analysis.py run5/run5b_mills

# Compare combined results across both batches
python batch_analysis_combined.py run5/run5a_kennels run5/run5b_mills

# Focus on desired traits only
python batch_analysis_combined_desired.py run5/run5a_kennels run5/run5b_mills
```

## Expected Outcomes
Based on Run 3 results:
- **Kennel-dominated**: Gradual increase in desirable traits, reduction in undesirable traits
- **Mill-dominated**: Faster breeding, potential for trait fixation or loss
- **Population**: Should remain stable with 200 creatures and proper capacity management
