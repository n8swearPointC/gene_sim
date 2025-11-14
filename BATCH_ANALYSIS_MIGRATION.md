# Batch Analysis Scripts - Unified Interface Migration

## Summary

The batch analysis tools have been consolidated into a single unified script (`batch_analysis_unified.py`) that provides a consistent, user-friendly interface for all analysis modes.

## What Changed

### New Unified Script
- **`batch_analysis_unified.py`** - Single entry point for all batch analysis operations
  - Uses proper argument parsing with `argparse`
  - Provides clear help text and examples
  - Supports short-form flags (`-i`, `-c`, `-cd`)
  - Consistent parameter ordering across all modes

### Legacy Scripts (Deprecated)
The following scripts are deprecated but maintained for backward compatibility:
- `batch_analysis.py` → Use `batch_analysis_unified.py --individual`
- `batch_analysis_combined.py` → Use `batch_analysis_unified.py --combined`
- `batch_analysis_combined_desired.py` → Use `batch_analysis_unified.py --combined-desired`

Each legacy script now displays a deprecation warning when run, directing users to the unified interface.

## Migration Guide

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

1. **Consistent Interface**: All modes use the same argument style
2. **Better Help**: Built-in `--help` flag with examples
3. **Short Forms**: Use `-i`, `-c`, `-cd` for brevity
4. **Clear Parameters**: Named flags make intent explicit
5. **Future-Proof**: Easier to extend with new features

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
