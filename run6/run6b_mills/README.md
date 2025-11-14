# Batch Simulation Run

## Run Information

**Generated**: 2025-11-14 00:01:10

## Configuration

- **Initial Population Size**: 200 creatures
- **Simulation Duration**: 20 years
- **Number of Runs**: 15
- **Base Seed**: 10000
- **Seed Range**: 10000 to 10014

### Breeder Distribution

- Kennel Club Breeders: 1
- Mill Breeders: 19
- Random Breeders: 0
- Inbreeding Avoidance Breeders: 0
- **Total Breeders**: 20

### Traits

- **Eye Color** (trait_id: 0)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - EE -> Emerald Eyes (initial freq: 0.0)
    - Ee -> Emerald Eyes (initial freq: 0.1)
    - ee -> Brown Eyes (initial freq: 0.9)

- **Coat Texture** (trait_id: 1)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - SS -> Silky Coat (initial freq: 0.04)
    - Ss -> Normal Coat (initial freq: 0.32)
    - ss -> Normal Coat (initial freq: 0.64)

- **Tail Length** (trait_id: 2)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - LL -> Long Tail (initial freq: 0.01)
    - Ll -> Medium Tail (initial freq: 0.18)
    - ll -> Medium Tail (initial freq: 0.81)

- **Bone Strength** (trait_id: 3)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - WW -> Strong Bones (initial freq: 0.6)
    - Ww -> Normal Bones (initial freq: 0.2)
    - ww -> Weak Bones (initial freq: 0.2)

- **Vision** (trait_id: 4)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - VV -> Good Vision (initial freq: 0.25)
    - Vv -> Normal Vision (initial freq: 0.5)
    - vv -> Poor Vision (initial freq: 0.25)

- **Fur Density** (trait_id: 5)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - FF -> Thick Fur (initial freq: 0.2)
    - Ff -> Normal Fur (initial freq: 0.2)
    - ff -> Thin Fur (initial freq: 0.6)

- **Temperament** (trait_id: 6)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - AA -> Aggression (initial freq: 0.6)
    - Aa -> Aggression (initial freq: 0.2)
    - aa -> Calm (initial freq: 0.2)

- **Hip Health** (trait_id: 7)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - HH -> Hip Issues (initial freq: 0.6)
    - Hh -> Hip Issues (initial freq: 0.2)
    - hh -> Healthy Hips (initial freq: 0.2)

- **Skin Health** (trait_id: 8)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - KK -> Skin Problems (initial freq: 0.25)
    - Kk -> Skin Problems (initial freq: 0.5)
    - kk -> Healthy Skin (initial freq: 0.25)

- **Heart Health** (trait_id: 9)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - DD -> Heart Defect (initial freq: 0.25)
    - Dd -> Heart Defect (initial freq: 0.5)
    - dd -> Healthy Heart (initial freq: 0.25)

- **Neurological Health** (trait_id: 10)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - ZZ -> Seizures (initial freq: 0.2)
    - Zz -> Seizures (initial freq: 0.2)
    - zz -> Healthy (initial freq: 0.6)

- **Eye Health** (trait_id: 11)
  - Type: SIMPLE_MENDELIAN
  - Genotypes:
    - BB -> Blindness (initial freq: 0.2)
    - Bb -> Blindness (initial freq: 0.2)
    - bb -> Healthy Eyes (initial freq: 0.6)

### Target Phenotypes

- Trait 0: Emerald Eyes
- Trait 1: Silky Coat
- Trait 2: Long Tail

### Undesirable Phenotypes

- Trait 3: Weak Bones
- Trait 4: Poor Vision
- Trait 5: Thin Fur
- Trait 6: Aggression
- Trait 7: Hip Issues
- Trait 8: Skin Problems
- Trait 9: Heart Defect
- Trait 10: Seizures
- Trait 11: Blindness

### Genotype Preferences (Kennel Club)

- **Trait 0**:
  - Optimal: EE
  - Acceptable: Ee
  - Undesirable: ee
- **Trait 1**:
  - Optimal: SS
  - Acceptable: Ss
  - Undesirable: ss
- **Trait 2**:
  - Optimal: LL
  - Acceptable: Ll
  - Undesirable: ll
- **Trait 3**:
  - Optimal: WW
  - Acceptable: Ww
  - Undesirable: ww
- **Trait 4**:
  - Optimal: VV
  - Acceptable: Vv
  - Undesirable: vv
- **Trait 5**:
  - Optimal: FF
  - Acceptable: Ff
  - Undesirable: ff
- **Trait 6**:
  - Optimal: aa
  - Acceptable: Aa
  - Undesirable: AA
- **Trait 7**:
  - Optimal: hh
  - Acceptable: Hh
  - Undesirable: HH
- **Trait 8**:
  - Optimal: kk
  - Acceptable: Kk
  - Undesirable: KK
- **Trait 9**:
  - Optimal: dd
  - Acceptable: Dd
  - Undesirable: DD
- **Trait 10**:
  - Optimal: zz
  - Acceptable: Zz
  - Undesirable: ZZ
- **Trait 11**:
  - Optimal: bb
  - Acceptable: Bb
  - Undesirable: BB

## Results Summary

### Execution Statistics

- **Total Runs**: 15
- **Successful**: 15
- **Failed**: 0
- **Total Execution Time**: 522.0 seconds (8.70 minutes)

### Runtime Statistics (per run)

- **Average**: 34.8 seconds
- **Minimum**: 22.8 seconds
- **Maximum**: 58.7 seconds

### Population Statistics (averages across successful runs)

- **Average Final Generation/Cycle**: 303
- **Average Final Population Size**: 2 creatures
- **Average Total Creatures Created**: 1,390 creatures

## Files in This Directory

- `batch_config.yaml` - Configuration file used for this batch run
- `batch_results.json` - Detailed results metadata in JSON format
- `simulation_run_NNN_seed_SSSS.db` - SQLite database for each simulation run
  - NNN = run number (001, 002, etc.)
  - SSSS = random seed used for that run

## Analyzing Results

You can analyze individual runs using the analytics scripts in the parent directory:

```powershell
# Comprehensive analytics for a specific run
python ../analytics/comprehensive_analytics.py simulation_run_001_seed_10000.db

# Chart phenotype frequencies across generations
python ../analytics/chart_phenotype.py simulation_run_001_seed_10000.db

# Analyze genotype frequencies
python ../analytics/analyze_genotype_frequencies.py simulation_run_001_seed_10000.db
```

## Database Schema

Each SQLite database contains the following tables:

- `simulations` - Simulation metadata
- `traits` - Trait definitions
- `genotypes` - Genotype-phenotype mappings
- `breeders` - Breeder information
- `creatures` - All creatures created during simulation
- `creature_genotypes` - Genotypes for each creature
- `creature_ownership_history` - Ownership changes over time
- `generation_stats` - Population statistics per generation
- `generation_genotype_frequencies` - Genotype frequencies per generation per trait
- `generation_trait_stats` - Aggregate trait statistics per generation

## Notes

This batch run was designed to provide statistical confidence through multiple replications
with different random seeds. Each run represents an independent simulation of the same
breeding scenario, allowing analysis of variability and trends across runs.

For questions about the simulation methodology, see the main project documentation.
