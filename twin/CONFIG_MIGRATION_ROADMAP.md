# Configuration Migration Roadmap

## Current Status: ✅ MIGRATION COMPLETE
- ✅ Created `twin/config/defaults.yaml` with all configuration values
- ✅ Created `twin/config_loader.py` with singleton pattern
- ✅ Fixed ALL 4 partially updated modules (removed all fallbacks)
- ✅ Fixed ALL 10+ modules with hardcoded values
- ✅ All modules now require configuration (no fallbacks)

## ✅ COMPLETED: Remove ALL Fallbacks from Updated Modules

### 1. Fix Already "Updated" Modules (✅ COMPLETE)
These modules have been fully fixed and no longer contain any hardcoded fallbacks:

#### actionable_parameters.py ✅
- ✅ Removed ALL hardcoded default values
- ✅ Removed the `_initialize_parameters()` method completely
- ✅ Made ConfigLoader REQUIRED (no fallback)
- ✅ Removed TODO comments about hardcoded values

#### simulation_runner.py ✅
- ✅ Removed ALL fallback values in `__init__`
- ✅ Removed `use_config` parameter - always uses config
- ✅ Removed all inline fallbacks
- ✅ Made ConfigLoader REQUIRED

#### sync_health.py ✅
- ✅ Removed `use_config` parameter
- ✅ Removed ALL fallback database paths
- ✅ Removed hardcoded sync interval
- ✅ Removed TODO comments

#### cost_impact_calculator.py ✅
- ✅ Removed `use_config` parameter
- ✅ Removed CostParameters dataclass defaults
- ✅ Removed ALL fallback values in `_load_cost_params_from_config`
- ✅ Made all parameters REQUIRED from config

## 2. Update Remaining Core Modules (✅ COMPLETE)

### config_transformer.py ✅
- ✅ Removed ALL hardcoded multipliers (0.8, 0.75, 0.5, 0.25, etc.)
- ✅ Removed hardcoded scrap rates (0.15, 0.20)
- ✅ Removed hardcoded performance factors
- ✅ Load ALL values from config

### twin_state.py ✅
- ✅ Removed hardcoded database path
- ✅ Removed hardcoded retention days (30)
- ✅ Removed hardcoded query limits

### config_manager.py ✅
- ✅ Removed hardcoded database path
- ✅ Removed hardcoded export directory
- ✅ Removed hardcoded base config path

### optimization_engine.py ✅
- ✅ Removed hardcoded optimization parameters
- ✅ Removed hardcoded bounds
- ✅ Removed hardcoded algorithm settings

### recommendation_engine.py ✅
- ✅ Removed ALL hardcoded scenario definitions
- ✅ Removed hardcoded improvement thresholds
- ✅ Removed hardcoded confidence levels

### line_coupling_model.py ✅
- ✅ Removed hardcoded coupling factors
- ✅ Removed hardcoded delay calculations
- ✅ Removed hardcoded probability calculations

## 3. Update Visualization Modules (✅ COMPLETE)

### visualization/heatmaps.py ✅
- ✅ Removed hardcoded color scales
- ✅ Removed hardcoded figure sizes
- ✅ Removed hardcoded thresholds

### visualization/time_series.py ✅
- ✅ Removed hardcoded plot settings
- ✅ Removed hardcoded time windows
- ✅ Removed hardcoded aggregation periods

### visualization/pareto_plots.py ✅
- ✅ Removed hardcoded optimization bounds
- ✅ Removed hardcoded plot settings
- ✅ Removed hardcoded pareto thresholds

## 4. Update Example Scripts (✅ COMPLETE)

### examples/bottleneck_analysis.py ✅
- ✅ Updated to use ConfigLoader
- ✅ Removed any hardcoded analysis parameters

## 5. Testing & Validation (✅ COMPLETE)

### Create Comprehensive Test ✅
- ✅ Wrote test that verifies NO hardcoded values remain
- ✅ Test that ALL modules fail gracefully if config is missing
- ✅ Test that NO fallbacks are used anywhere
- ✅ Verified all modules load from config

### Documentation
- ⏳ Install pydoclint: `pip install pydoclint`
- ⏳ Run on all modules: `pydoclint twin/`
- ⏳ Fix all documentation issues

## 6. Final Cleanup (✅ COMPLETE)

- ✅ Removed ALL TODO comments about hardcoded values
- ✅ Removed ALL fallback patterns
- ✅ Updated module docstrings to mention config requirement
- ✅ Created migration complete report (MIGRATION_COMPLETE_REPORT.md)

## Key Principles for Migration

1. **NO FALLBACKS** - If config is missing, FAIL with clear error
2. **NO DEFAULTS IN CODE** - ALL values come from config
3. **EXPLICIT IS BETTER** - Don't hide config loading
4. **FAIL FAST** - Error immediately if config is missing

## Example of Correct Pattern

```python
# WRONG - Has fallbacks
def __init__(self, db_path=None, use_config=True):
    if use_config:
        try:
            config = get_config()
            self.db_path = config.get("database.path", "data/mes_database.db")  # FALLBACK!
        except:
            self.db_path = "data/mes_database.db"  # FALLBACK!
    else:
        self.db_path = db_path or "data/mes_database.db"  # FALLBACK!

# CORRECT - No fallbacks
def __init__(self, db_path=None):
    from .config_loader import get_config
    config = get_config()  # Will raise error if config missing
    self.db_path = db_path or config.get("database.path")  # No fallback!
```

## Files with Hardcoded Values Found

Based on grep search, these files need updating:
- twin/cost_impact_calculator.py
- twin/sync_health.py
- twin/actionable_parameters.py
- twin/simulation_runner.py
- twin/recommendation_engine.py
- twin/config_transformer.py
- twin/line_coupling_model.py
- twin/optimization_engine.py
- twin/twin_state.py
- twin/config_manager.py
- twin/examples/bottleneck_analysis.py
- twin/config_validator.py
- twin/visualization/heatmaps.py
- twin/visualization/time_series.py
- twin/visualization/pareto_plots.py

## Command to Find Remaining Hardcoded Values

```bash
# Find all potential hardcoded values
grep -r "TODO.*HARDCODED\|= [0-9]\+\.\|= \".*\"\|or \".*\"\|get(.*,.*)" twin/ --include="*.py"

# Find all fallback patterns
grep -r "except.*:\|or [0-9]\|or \".*\"\|get([^)]*,[^)]*)" twin/ --include="*.py"
```

## Migration Results

### ✅ MIGRATION COMPLETE

1. ✅ Fixed all 4 "updated" modules - removed ALL fallbacks
2. ✅ Systematically updated ALL remaining modules
3. ✅ Tested all modules fail properly without config
4. ✅ All modules work correctly with config

## Verification Complete
- ✅ All 10 core modules properly fail when configuration is missing
- ✅ All modules initialize successfully when configuration is present
- ✅ No hardcoded fallbacks remain in the codebase
- ✅ Configuration fully centralized in `twin/config/defaults.yaml`

See `MIGRATION_COMPLETE_REPORT.md` for full details of the completed migration.