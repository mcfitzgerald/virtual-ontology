# Twin Model Cleanup Guide

## Directory Structure After Cleanup

```
twin_model/
├── __init__.py                    # KEEP - Main package init
├── model_builder.py               # KEEP - Ontology-driven model builder
├── primitives/                    # KEEP - All new primitive implementations
│   ├── __init__.py
│   ├── base.py                   # Core primitive base class
│   ├── equipment.py              # Equipment primitive
│   ├── buffer.py                 # Buffer primitive  
│   ├── source.py                 # Source primitive
│   ├── sink.py                   # Sink primitive
│   ├── scheduler.py              # Scheduler primitive
│   └── monitor.py                # Monitor primitive
├── transduction/                  # KEEP - MES transduction layer
│   ├── __init__.py
│   └── mes_transducer.py         # MES data converter
└── tests/                         # KEEP - All test files (moved here)
    ├── __init__.py
    ├── test_phase1_primitives.py
    ├── test_phase1_3_primitives.py
    ├── test_phase1_4_primitives.py
    ├── test_phase2_integration.py
    ├── test_phase2_model_builder.py
    ├── test_phase2_complete.py
    ├── test_phase3_manifests.py
    ├── test_phase4_transduction.py
    ├── test_phase5_integration.py
    └── test_phase6_validation.py
```

## Files to REMOVE (Legacy Code)

### Root Level Legacy Files
```bash
# OLD equipment/buffer implementations (replaced by primitives/)
rm twin_model/equipment.py          # Old equipment class
rm twin_model/buffer.py              # Old buffer class
rm twin_model/production_line.py    # Old production line
rm twin_model/runner.py              # Old simulation runner
rm twin_model/config.py              # Old config system
rm twin_model/transduction.py        # Old transduction (replaced by transduction/)

# Old test files (already moved to tests/)
rm twin_model/test_simulation.py     # Old test
rm twin_model/test_transduction.py   # Old test
```

### Documentation to Remove
```bash
# Remove auto-generated docs (can regenerate if needed)
rm -rf twin_model/docs/_build/
rm -rf twin_model/docs/_static/
rm -rf twin_model/docs/_templates/
rm twin_model/docs/conf.py          # Old Sphinx config
```

### Cache and Temp Files
```bash
# Remove Python cache
rm -rf twin_model/__pycache__/
rm -rf twin_model/**/__pycache__/
rm -rf twin_model/**/*.pyc
```

## Cleanup Commands

Run these commands to clean up:

```bash
# 1. Move test files (if not already done)
mkdir -p twin_model/tests
mv test_phase*.py twin_model/tests/ 2>/dev/null

# 2. Remove legacy Python files
rm twin_model/equipment.py
rm twin_model/buffer.py
rm twin_model/production_line.py
rm twin_model/runner.py
rm twin_model/config.py
rm twin_model/transduction.py
rm twin_model/test_simulation.py
rm twin_model/test_transduction.py

# 3. Clean up documentation
rm -rf twin_model/docs/

# 4. Remove Python cache
find twin_model -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find twin_model -name "*.pyc" -delete

# 5. Remove any .pyc files
find . -name "*.pyc" -delete
```

## Files to KEEP

### Core Implementation
- `twin_model/__init__.py` - Package initialization
- `twin_model/model_builder.py` - Ontology-driven model builder
- `twin_model/primitives/*` - All primitive implementations
- `twin_model/transduction/*` - MES transduction layer

### Tests (in twin_model/tests/)
- All `test_phase*.py` files

### Configuration & Data
- `ontology/twin_ontology.yaml` - Ontology definition
- `manifests/*.yaml` - Production and equipment manifests
- `archive/misc/data/mes_data_with_kpis.csv` - Reference data

### Documentation (at root level)
- `ONTOLOGY_DRIVEN_ARCHITECTURE.md` - Architecture documentation
- `MES_DATA_ANALYSIS_REPORT.md` - Data analysis
- `SYSTEM_DOCUMENTATION.md` - System docs (from Phase 6)
- `API_REFERENCE.md` - API reference (from Phase 6)

## Verification After Cleanup

After cleanup, verify the system still works:

```python
# Test import structure
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.primitives import Equipment, Buffer, Source, Sink
from twin_model.transduction import MESTransducer

# Run a quick test
python twin_model/tests/test_phase1_primitives.py
```

## Final Directory Size

After cleanup, the `twin_model` directory should be much smaller:
- Before: ~10MB (with docs and legacy code)
- After: ~500KB (just essential code)

The clean structure follows Python package best practices with:
- Clear separation of concerns (primitives, transduction, tests)
- No legacy/duplicate code
- Minimal dependencies
- Clean import paths