# Batch Analysis Scripts - Unified Interface Migration

## Summary

The batch analysis tools have been consolidated into a single unified script (`batch_analysis_unified.py`) with a **streamlined interface** that can run all analyses with one command.

## What Changed

### New Streamlined Interface

**Before (4 separate commands):**
```bash
python batch_analysis.py run5/run5a_kennels
python batch_analysis.py run5/run5b_mills
python batch_analysis_combined.py run5/run5a_kennels run5/run5b_mills run5/combined
python batch_analysis_combined_desired.py run5/run5a_kennels run5/run5b_mills run5/combined_desired
```

**After (1 command):**
```bash
python batch_analysis_unified.py run5/run5a_kennels run5/run5b_mills
```

This single command automatically runs all four analyses and organizes outputs.

### New Unified Script
- **`batch_analysis_unified.py`** - Single entry point for all batch analysis operations
  - **Full analysis mode** (default): Provide two directories, get all analyses
  - **Individual modes**: Use flags for specific analyses
  - Uses proper argument parsing with `argparse`
  - Interactive confirmation before starting full analysis
  - Clear progress indicators for each step
  - Automatic output directory determination

### Legacy Scripts (Deprecated)
The following scripts are deprecated but maintained for backward compatibility:
- `batch_analysis.py` → Use `batch_analysis_unified.py --individual`
- `batch_analysis_combined.py` → Use `batch_analysis_unified.py --combined`
- `batch_analysis_combined_desired.py` → Use `batch_analysis_unified.py --combined-desired`

Each legacy script now displays a deprecation warning when run.

## Migration Guide

### Full Analysis (Recommended)

**Old (4 commands):**
```bash
python batch_analysis.py run4/run4a_kennels
python batch_analysis.py run4/run4b_mills
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined
python batch_analysis_combined_desired.py run4/run4a_kennels run4/run4b_mills run4/combined_desired
```

**New (1 command):**
```bash
python batch_analysis_unified.py run4/run4a_kennels run4/run4b_mills
```

### Individual Batch Analysis

**Old:**
```bash
python batch_analysis.py run4/run4a_kennels
python batch_analysis.py run4/run4a_kennels median
```

**New:**
```bash
python batch_analysis_unified.py --individual run4/run4a_kennels
python batch_analysis_unified.py -i run4/run4a_kennels --aggregate median
```

### Combined Analysis (Total Population)

**Old:**
```bash
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined
python batch_analysis_combined.py run4/run4a_kennels run4/run4b_mills run4/combined median
```

**New:**
```bash
python batch_analysis_unified.py --combined run4/run4a_kennels run4/run4b_mills run4/combined
python batch_analysis_unified.py -c run4/run4a_kennels run4/run4b_mills run4/combined -a median
```

### Combined Analysis (Desired Population Only)

**Old:**
```bash
python batch_analysis_combined_desired.py run4/run4a_kennels run4/run4b_mills run4/combined_desired
python batch_analysis_combined_desired.py run4/run4a_kennels run4/run4b_mills run4/combined_desired median
```

**New:**
```bash
python batch_analysis_unified.py --combined-desired run4/run4a_kennels run4/run4b_mills run4/combined_desired
python batch_analysis_unified.py -cd run4/run4a_kennels run4/run4b_mills run4/combined_desired -a median
```

## Benefits

1. **Dramatically Simpler**: One command instead of four for full analysis
2. **Automatic Organization**: Output directories determined automatically
3. **Interactive**: Confirmation prompt with summary before running
4. **Progress Tracking**: Clear step indicators (1/4, 2/4, etc.)
5. **Consistent Interface**: Same argument style across all modes
6. **Better Help**: Built-in `--help` flag with examples
7. **Short Forms**: Use `-i`, `-c`, `-cd`, `-a` for brevity
8. **Future-Proof**: Easier to extend with new features

## Key Improvement: Full Analysis Mode

The biggest improvement is the new **full analysis mode**:

```bash
# Just provide two directories
python batch_analysis_unified.py run5/run5a_kennels run5/run5b_mills
```

This automatically:
- Runs individual analysis on both directories
- Creates combined comparison charts (total population)
- Creates combined comparison charts (desired population)
- Organizes all outputs in appropriate directories
- Provides progress updates for each step
- Shows a comprehensive summary at the end

**Before:** 4 commands, manual output directory management, ~150 characters typed  
**After:** 1 command, automatic output management, ~70 characters typed  
**Time saved:** ~75% reduction in commands and typing

## Implementation Details

- The unified script imports functions from `batch_analysis.py`
- All core analytics logic remains unchanged
- No changes to output formats or chart generation
- Legacy scripts still functional (with deprecation warnings)

## Usage Examples

```bash
# Get help
python batch_analysis_unified.py --help

# Individual analysis (kennels)
python batch_analysis_unified.py --individual run4/run4a_kennels

# Individual analysis (mills with median)
python batch_analysis_unified.py -i run4/run4b_mills -a median

# Combined total population
python batch_analysis_unified.py --combined run4/run4a_kennels run4/run4b_mills run4/combined

# Combined desired population with confidence intervals
python batch_analysis_unified.py -cd run4/run4a_kennels run4/run4b_mills run4/combined_desired -a mean_ci
```

## Files Modified

### Created
- `batch_analysis_unified.py` - New unified script

### Updated
- `batch_analysis.py` - Added deprecation warning in docstring and main()
- `batch_analysis_combined.py` - Added deprecation warning in docstring and main()
- `batch_analysis_combined_desired.py` - Added deprecation warning in docstring and main()
- `BATCH_ANALYSIS_DOCUMENTATION.md` - Updated to document unified interface
- `README.md` - Added batch analysis quick start section

## Backward Compatibility

All legacy scripts continue to work exactly as before, but now display a deprecation warning:

```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEPRECATION WARNING
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This script (batch_analysis.py) is deprecated.
Please use the unified interface instead:

  python batch_analysis_unified.py --individual <directory> [--aggregate method]

Example:
  python batch_analysis_unified.py --individual run4/run4a_kennels

Continuing with legacy behavior...
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

## Recommendations

1. **New scripts**: Use the unified interface
2. **Existing scripts**: Update when convenient, no urgency
3. **Documentation**: Reference unified interface in all new documentation
4. **Training**: Teach new users the unified interface

## Future Deprecation Timeline

- **Current**: Legacy scripts functional with warnings
- **Next release**: Consider marking legacy scripts for removal
- **Future**: Remove legacy scripts entirely (if desired)

For now, both interfaces are fully supported.
