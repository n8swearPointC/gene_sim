# Batch Analysis Documentation

## Overview

This project includes three complementary batch analysis tools for analyzing simulation runs:

1. **`batch_analysis.py`** - Individual analysis per breeding strategy
2. **`batch_analysis_combined.py`** - Side-by-side comparison of kennels vs mills (total population)
3. **`batch_analysis_combined_desired.py`** - Side-by-side comparison (desired/show-quality population only)

All three tools generate charts showing undesirable trait frequencies across generations with ensemble aggregates.

---

## Tool 1: Individual Batch Analysis (`batch_analysis.py`)

### Purpose
Analyze a single batch of simulation runs (e.g., kennel-only or mill-only), creating individual charts for each undesirable trait.

### Usage

```bash
# Basic (uses mean aggregate by default)
python batch_analysis.py <directory>

# With specific aggregate method
python batch_analysis.py <directory> <method>
```

### Examples

```bash
# Kennels with mean (default)
python batch_analysis.py run4/run4a_kennels

# Mills with median
python batch_analysis.py run4/run4b_mills median

# With confidence intervals
python batch_analysis.py run4/run4a_kennels mean_ci
```

### Output

- **Text Reports**: Saved in `<directory>/batch_analysis/`, one `.txt` file per simulation
- **Charts**: Saved in `<directory>/`, one PNG per undesirable trait
  - Filenames: `undesirable_<trait_name>_trends.png`
  - Individual runs shown in grey
  - Aggregate trend shown in dark red

### Chart Features

Each chart displays:
- **Title**: Trait name (e.g., "Weak Bones")
- **Subtitle**: Breeder ratio (e.g., "Kennels 95% : 5% Mills")
- **Starting genotype frequencies** at generation 0
- **Tracked genotypes**: Which genotype(s) represent the undesirable phenotype
- **Grey lines**: Individual simulation runs
- **Dark red line**: Aggregate trend
- **Y-axis**: Time (inverted - earlier generations at top)
- **X-axis**: Percentage of total population with undesirable phenotype (0-100%)

---

## Tool 2: Combined Batch Analysis (`batch_analysis_combined.py`)

### Purpose
Create side-by-side comparison charts showing kennels vs mills on the same graph, measuring undesirable traits in the **total population**.

### Usage

```bash
python batch_analysis_combined.py <kennel_dir> <mill_dir> <output_dir> [aggregate_method]
```

### Examples

```bash
# Default (mean aggregate)
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined

# With median
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined median

# With confidence intervals
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined mean_ci
```

### Output

Creates comparison charts in `<output_dir>/`:
- Filenames: `combined_<trait_name>_trends.png`
- One chart per undesirable trait (9 total)

### Color Scheme (Color-Blind Friendly)

- **Kennels**:
  - Individual runs: Light blue (#56B4E9) at 25% opacity
  - Ensemble average: Dark blue (#0173B2) bold line
  
- **Mills**:
  - Individual runs: Yellow-orange (#F0E442) at 25% opacity
  - Ensemble average: Dark orange (#DE8F05) bold line

Colors are designed for deuteranopia/protanopia accessibility and grayscale printing.

### What It Measures

**X-axis**: "Undesirable Phenotype (% of Total Population)"

This shows the percentage of **all creatures** (regardless of desired traits) that have each undesirable phenotype.

---

## Tool 3: Desired Population Analysis (`batch_analysis_combined_desired.py`)

### Purpose
Create side-by-side comparison charts showing kennels vs mills, but measuring undesirable traits **only among creatures with ALL desired phenotypes** (show-quality animals).

### Usage

```bash
python batch_analysis_combined_desired.py <kennel_dir> <mill_dir> <output_dir> [aggregate_method]
```

### Examples

```bash
# Default (mean aggregate)
python batch_analysis_combined_desired.py run4/run4a_kennels run4/run4b_mills run4/combined_desired

# With median
python batch_analysis_combined_desired.py run4/run4a_kennels run4/run4b_mills run4/combined_desired median
```

### Output

Creates charts in `<output_dir>/`:
- Filenames: `combined_desired_<trait_name>_trends.png`
- One chart per undesirable trait (9 total)
- Same color scheme as standard combined charts

### What It Measures

**X-axis**: "Undesirable Phenotype (% of Desired Population)"

This answers: **"Of creatures that have Emerald Eyes AND Silky Coat AND Long Tail, what percentage also have this undesirable trait?"**

### Desired Phenotypes

Automatically detected from config's `target_phenotypes` section. For runs 3-5:
- Emerald Eyes (trait 0)
- Silky Coat (trait 1)
- Long Tail (trait 2)

A creature must have **ALL THREE** to be included in the "desired population."

---

## Aggregate Methods

All three tools support four aggregate methods:

| Method | Description | Best For |
|--------|-------------|----------|
| **`mean`** | Ensemble average across all runs | **DEFAULT** - smooth typical behavior |
| **`median`** | Middle value at each generation | When you have outlier runs |
| **`mean_ci`** | Mean with shaded ±1 std deviation | Showing variation/confidence |
| **`moving_avg`** | 3-generation moving average | Extra-smooth trend visualization |

### Choosing a Method

- **Use mean**: Default choice for most cases, smooth typical trend
- **Use median**: When outlier runs might skew results
- **Use mean_ci**: To visualize variability/uncertainty across runs
- **Use moving_avg**: To smooth noisy generation-to-generation fluctuations

---

## Typical Analysis Workflow

```bash
# Step 1: Individual kennel analysis
python batch_analysis.py run4/run4a_kennels

# Step 2: Individual mill analysis
python batch_analysis.py run4/run4b_mills

# Step 3: Combined total population comparison
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined

# Step 4: Combined desired population comparison
python batch_analysis_combined_desired.py run4/run4a_kennels run4/run4b_mills run4/combined_desired
```

This produces:
- Individual charts for kennels only
- Individual charts for mills only
- Combined charts showing total population comparisons
- Combined charts showing show-quality population comparisons

---

## When to Use Each Tool

### Use `batch_analysis.py` when:
- You want to focus on one breeding strategy at a time
- You need detailed text reports for each simulation
- You're analyzing a single batch in isolation

### Use `batch_analysis_combined.py` when:
- You want direct visual comparison of breeding strategies
- You care about overall population health
- You're tracking trait spread across all creatures
- You want to answer: "Which strategy produces healthier populations overall?"

### Use `batch_analysis_combined_desired.py` when:
- You're breeding for specific show/competition traits
- You want to know: "Of my best animals, how many have defects?"
- You're evaluating breeding program quality control
- You care about the **marketable/show-worthy** subset
- You want to answer: "Which strategy produces better show-quality animals?"

---

## Chart Interpretation

### Individual Charts (batch_analysis.py)
- **Grey lines**: Each individual simulation run
- **Red line**: Aggregate showing overall trend
- **Look for**: Direction of trend (increasing/decreasing), variability between runs

### Combined Charts (both tools)
- **Blue/Teal**: Kennels (light = individual runs, dark = aggregate)
- **Orange/Yellow**: Mills (light = individual runs, dark = aggregate)
- **Look for**: Separation between strategies, convergence/divergence over time

### Key Insights

**Standard Combined vs Desired-Only:**

- **Standard charts**: "How healthy is my entire breeding operation?"
- **Desired-only charts**: "How healthy are my show-quality animals?"

A breeding program might have:
- Low overall defect rates (standard charts look good)
- But high defects in show-quality animals (desired-only charts look bad)

This indicates defects clustering in the valuable subset - a critical breeding failure.

---

## Examples from Run 4

Run 4 configuration:
- 200 creatures, 20 years, 20 total breeders
- Batch A: 19 kennels, 1 mill (seeds 5000-5014)
- Batch B: 1 kennel, 19 mills (seeds 6000-6014)

```bash
# Analyze kennels
python batch_analysis.py run4/run4a_kennels

# Analyze mills  
python batch_analysis.py run4/run4b_mills

# Compare total populations
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined

# Compare show-quality populations
python batch_analysis_combined_desired.py run4/run4a_kennels run4/run4b_mills run4/combined_desired
```

---

## Technical Notes

### File Locations
- **Scripts**: Top-level directory (`batch_analysis.py`, etc.)
- **Individual results**: `<run_dir>/<batch_dir>/` (e.g., `run4/run4a_kennels/`)
- **Combined results**: User-specified output directory (e.g., `run4/combined/`)

### Chart Format
- PNG images
- 10x8 inch figure size
- 300 DPI for publication quality
- Y-axis inverted (time flows downward)

### Performance
- Processes all `.db` files in specified directory
- Parallelizable across multiple runs
- Efficient SQLite queries for large simulations
