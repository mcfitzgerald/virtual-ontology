# Archive Plan for Fresh Implementation

## What to KEEP (Essential)

### 1. Ontology & Configuration (Core Architecture)
```
ontology/
├── twin_ontology.yaml         # Equipment type definitions
├── control_mappings.yaml      # Control parameter mappings
└── *.yaml                     # Any other ontology files

manifests/
├── equipment_manifest.yaml    # Equipment instances
├── production_manifest.yaml   # Production line configs
├── system_config.yaml        # System-wide settings
└── *.yaml                    # Any other manifest files

config/                        # If exists, keep all config files
```

### 2. Target Output & Data
```
ORIGINAL_2WEEK.csv            # Target MES output format
data/                         # Any reference data files
```

### 3. Project Documentation
```
CLAUDE.md                     # Instructions for Claude
README.md                     # Project overview
TWIN_MODEL_FRESH_SPEC.md     # Fresh implementation spec
CHANGELOG.md                  # If tracking changes
```

### 4. Project Infrastructure
```
pyproject.toml               # Poetry configuration
poetry.lock                  # Locked dependencies
.venv/                      # Virtual environment
.gitignore                  # Git ignore rules
.git/                       # Git repository
```

## What to ARCHIVE (Old Implementation)

### 1. Old Code
```
twin_model/                  # Entire old implementation directory
├── primitives/             # Mixed Store/Container code
├── transduction/           # Old transduction layer
├── control/                # Control system (may keep if needed)
├── monitoring/             # Old monitoring
└── tests/                  # Old tests
```

### 2. Old Documentation & Scripts
```
CONTAINER_MIGRATION_PLAN.md  # Partial refactor plan
validate_container_refactor.py
run_container_tests.py
run_mes_simulation.py        # If using old primitives
test_mes_output*.csv         # Old test outputs
mes_*.csv                    # Old simulation outputs
```

## Archive Commands

```bash
# Create archive directory with timestamp
mkdir -p archive/$(date +%Y%m%d)_store_based

# Move old implementation
mv twin_model archive/$(date +%Y%m%d)_store_based/
mv CONTAINER_MIGRATION_PLAN.md archive/$(date +%Y%m%d)_store_based/
mv validate_container_refactor.py archive/$(date +%Y%m%d)_store_based/
mv run_container_tests.py archive/$(date +%Y%m%d)_store_based/
mv run_mes_simulation.py archive/$(date +%Y%m%d)_store_based/ 2>/dev/null || true

# Move old outputs (keeping ORIGINAL_2WEEK.csv)
mv mes_*.csv archive/$(date +%Y%m%d)_store_based/ 2>/dev/null || true
mv test_mes_output*.csv archive/$(date +%Y%m%d)_store_based/ 2>/dev/null || true

# Create fresh structure
mkdir -p twin_model/{primitives,transduction,monitoring,tests/{unit,integration}}

# Create placeholder __init__.py files
touch twin_model/__init__.py
touch twin_model/primitives/__init__.py
touch twin_model/transduction/__init__.py
touch twin_model/monitoring/__init__.py
touch twin_model/tests/__init__.py
```

## Fresh Start Checklist

- [ ] Archive old implementation
- [ ] Keep ontology files
- [ ] Keep manifest files  
- [ ] Keep ORIGINAL_2WEEK.csv as target
- [ ] Keep CLAUDE.md for instructions
- [ ] Keep TWIN_MODEL_FRESH_SPEC.md as blueprint
- [ ] Create fresh twin_model directory structure
- [ ] Start implementation from spec

## Next Session Instructions

When starting the fresh implementation:

1. **Reference the spec**: `TWIN_MODEL_FRESH_SPEC.md`
2. **Use the ontology**: Load from `ontology/` directory
3. **Use the manifests**: Load from `manifests/` directory
4. **Target the output format**: Match `ORIGINAL_2WEEK.csv`
5. **Follow CLAUDE.md**: Your coding instructions

The fresh implementation should be purely Container-based with no legacy Store code.