# Run 6: Kennel vs Mill Breeding Comparison (Extended Timeframe - Replication)

## Overview
Run 6 replicates Run 4 with different random seeds to validate results and observe variance in long-term trait dynamics and breeding strategy effectiveness.

## Configuration
- **Population**: 200 creatures (same as Run 4)
- **Duration**: 20 years (same as Run 4)
- **Total Breeders**: 20 (same as Run 4)
- **Breeder Split**: 19/1 (95% kennels / 5% mills)

## Experimental Design

### Batch A: Kennel-Dominated
- **Kennel Club Breeders**: 19 (95%)
- **Mill Breeders**: 1 (5%)
- **Runs**: 15 simulations
- **Seeds**: 9000-9014

### Batch B: Mill-Dominated
- **Kennel Club Breeders**: 1 (5%)
- **Mill Breeders**: 19 (95%)
- **Runs**: 15 simulations
- **Seeds**: 10000-10014

## Traits
Same trait configuration as Run 4:
- **3 Desirable Traits**: Emerald Eyes (dominant), Silky Coat (recessive), Long Tail (recessive)
- **12 Undesirable Traits**: Mix of dominant and recessive undesirable phenotypes

## Execution

### Quick Test (Single Simulation)
```bash
cd run6
python run_single_pass.py
```

### Full Batch Execution
```bash
cd run6
python run6_execute.py
```

## Comparison to Previous Runs
| Parameter | Run 3 | Run 4 | Run 6 |
|-----------|-------|-------|-------|
| Population | 200 | 200 | 200 |
| Years | 6 | 20 | 20 |
| Total Breeders | 20 | 20 | 20 |
| Breeder Split | 19/1 (95/5) | 19/1 (95/5) | 19/1 (95/5) |
| Seeds (Kennels) | 3000-3014 | 5000-5014 | 9000-9014 |
| Seeds (Mills) | 4000-4014 | 6000-6014 | 10000-10014 |

## Research Questions
1. Do Run 4 results replicate with different random seeds?
2. What is the variance in trait frequency outcomes across different seeds?
3. Do kennel-dominated populations consistently outperform mill-dominated populations?
4. What is the range of extinction risk in mill-dominated populations?

## Expected Outcomes
- Results should be qualitatively similar to Run 4 (kennel populations improving, mill populations struggling)
- Some variance expected due to stochastic effects, but trends should be consistent
- Provides validation of Run 4 findings and quantifies result variance
- Combined analysis of Run 4 + Run 6 will show robustness of breeding strategy effects

## Analysis
Results can be analyzed using the batch analysis tools:
```bash
cd ..
python scripts/batch_analysis.py run6/run6a_kennels
python scripts/batch_analysis.py run6/run6b_mills

# Combined analysis
python scripts/batch_analysis_combined.py run6/run6a_kennels run6/run6b_mills

# Desired traits only
python scripts/batch_analysis_combined_desired.py run6/run6a_kennels run6/run6b_mills

# Compare Run 4 vs Run 6
# (Manually compare charts from run4/combined and run6/combined directories)
```
