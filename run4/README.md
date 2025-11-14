# Run 4: Kennel vs Mill Breeding Comparison (Extended Timeframe)

## Overview
Run 4 extends Run 3 with a longer timeframe to observe long-term trait dynamics and breeding strategy effectiveness.

## Configuration
- **Population**: 200 creatures (same as Run 3)
- **Duration**: 20 years (extended from 6 years in Run 3)
- **Total Breeders**: 20 (same as Run 3)
- **Breeder Split**: 19/1 (95% kennels / 5% mills)

## Experimental Design

### Batch A: Kennel-Dominated
- **Kennel Club Breeders**: 19 (95%)
- **Mill Breeders**: 1 (5%)
- **Runs**: 15 simulations
- **Seeds**: 5000-5014

### Batch B: Mill-Dominated
- **Kennel Club Breeders**: 1 (5%)
- **Mill Breeders**: 19 (95%)
- **Runs**: 15 simulations
- **Seeds**: 6000-6014

## Traits
Same trait configuration as Run 3:
- **3 Desirable Traits**: Emerald Eyes (dominant), Silky Coat (recessive), Long Tail (recessive)
- **12 Undesirable Traits**: Mix of dominant and recessive undesirable phenotypes

## Execution

### Full Batch Execution
```bash
cd run4
python run4_execute.py
```

## Comparison to Run 3
| Parameter | Run 3 | Run 4 |
|-----------|-------|-------|
| Population | 200 | 200 |
| Years | 6 | 20 |
| Total Breeders | 20 | 20 |
| Breeder Split | 19/1 (95/5) | 19/1 (95/5) |
| Seeds (Kennels) | 3000-3014 | 5000-5014 |
| Seeds (Mills) | 4000-4014 | 6000-6014 |

## Research Questions
1. Do desirable traits continue to increase over 20 years in kennel-dominated populations?
2. Do mill-dominated populations stabilize or continue declining toward extinction?
3. What is the long-term equilibrium for undesirable traits under selective breeding?
4. How many generations are needed to see significant trait frequency changes?

## Expected Outcomes
- Longer timeframe allows observation of multi-generational trait dynamics
- Kennel populations should show continued improvement in desirable traits
- Mill populations may face extinction risk or stabilize at minimal viable population
- More complete picture of breeding strategy effectiveness

## Analysis
Results can be analyzed using the batch analysis tools:
```bash
cd ..
python batch_analysis.py run4/run4a_kennels
python batch_analysis.py run4/run4b_mills
```
