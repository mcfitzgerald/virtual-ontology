# Virtual Twin Configuration Management

## Overview

The Virtual Twin system manages simulation configurations through a database-backed storage system that provides efficient deduplication, versioning, and traceability. This replaces the previous file-based approach to avoid repository clutter and improve scalability.

## Architecture

### Configuration Storage

All simulation configurations are now stored in the SQLite database in the `simulation_configs` table with the following structure:

- **config_id**: Unique identifier (format: `cfg-YYYYMMDD-HHMMSS-hash`)
- **run_id**: Links to simulation run in `twin_runs` table
- **config_type**: Type of configuration (full, delta, base)
- **config_json**: Complete configuration as JSON
- **config_hash**: SHA256 hash for deduplication
- **created_at**: Timestamp of creation
- **description**: Human-readable description
- **is_archived**: Soft delete flag

### Key Components

#### 1. ConfigurationManager (`twin/config_manager.py`)

The central manager for all configuration operations:

```python
from twin.config_manager import ConfigurationManager

config_mgr = ConfigurationManager()

# Store a configuration
config_id = config_mgr.store_config(
    config_dict,
    run_id="sim-123",
    config_type="full",
    description="Optimized parameters for energy reduction"
)

# Retrieve a configuration
config = config_mgr.get_config(config_id)

# List all configurations
configs = config_mgr.list_configs(config_type="full", limit=10)

# Archive old configurations
archived_count = config_mgr.cleanup_old_configs(days_to_keep=30)
```

#### 2. ConfigTransformer (`twin/config_transformer.py`)

Transforms actionable parameters into full configurations:

```python
from twin.config_transformer import ConfigTransformer
from twin.actionable_parameters import ActionableParameters

transformer = ConfigTransformer()
params = ActionableParameters()
params.set_value("micro_stop_probability", 0.15)

# Automatically saves to database
config = transformer.apply_parameters(params, save_path="auto")
```

#### 3. SimulationRunner (`twin/simulation_runner.py`)

Uses configurations from database for simulations:

```python
from twin.simulation_runner import SimulationRunner

runner = SimulationRunner()
# Configurations are automatically linked to runs
result = runner.run_simulation(parameters=params)
```

## Configuration Types

### 1. **Full Configurations**
Complete simulation configuration including all parameters, equipment definitions, product specifications, and anomaly patterns. These are ~16KB each and contain everything needed to reproduce a simulation.

### 2. **Delta Configurations**
Only the changes from the base configuration. Stored in `twin_runs.config_delta_json` for efficiency. Example:
```json
{
    "micro_stop_probability": 0.15,
    "performance_factor": 0.85,
    "scrap_multiplier": 2.0
}
```

### 3. **Base Configuration**
The original `mes_data_config.json` that serves as the foundation for all transformations.

## Deduplication

The system automatically deduplicates configurations based on their content hash:

1. **Hash Calculation**: SHA256 hash of the configuration (excluding volatile metadata)
2. **Duplicate Detection**: If identical config exists, returns existing config_id
3. **Space Efficiency**: 11 identical configs were reduced to 1 during migration

## Migration from File-Based Storage

### What Changed

**Before:**
- Configs stored as JSON files in `twin/configs/`
- Files accumulated over time (176KB for 11 configs)
- Tracked in version control
- No deduplication

**After:**
- Configs stored in database
- Automatic deduplication
- Linked to simulation runs
- Archive directory for important exports

### Migration Process

Run the migration script to move existing configs:

```bash
python scripts/migrate_configs.py
```

This will:
1. Read all JSON files from `twin/configs/`
2. Store unique configs in database
3. Archive files to `data/simulation_configs/archive/`
4. Remove the `twin/configs/` directory

## Usage Patterns

### Creating a New Simulation

```python
# 1. Define parameters
params = ActionableParameters()
params.micro_stop_probability = 0.20
params.performance_factor = 0.90

# 2. Transform to config (auto-saves to DB)
transformer = ConfigTransformer()
config = transformer.apply_parameters(params, save_path="auto")

# 3. Run simulation (links config to run)
runner = SimulationRunner()
results = runner.run_simulation(parameters=params)
```

### Retrieving Historical Configs

```python
config_mgr = ConfigurationManager()

# Get config for a specific run
config = config_mgr.get_config_by_run("sim-20250809-123456")

# List recent configs
recent = config_mgr.list_configs(limit=10)
for cfg in recent:
    print(f"{cfg['config_id']}: {cfg['description']}")
```

### Exporting for Archive

```python
# Export important config to file
config_mgr.export_config_to_file(
    config_id="cfg-20250810-141233-68915975",
    output_dir="data/simulation_configs/important"
)
```

## Database Queries

### Find Configs by Parameter

```sql
-- Find all configs with low micro-stop probability
SELECT config_id, config_json->>'$.twin_metadata.parameters_applied.micro_stop_probability' as micro_stop
FROM simulation_configs
WHERE json_extract(config_json, '$.twin_metadata.parameters_applied.micro_stop_probability') < 0.2;
```

### Get Config for Run

```sql
-- Get configuration used for a specific run
SELECT sc.config_id, sc.config_json
FROM simulation_configs sc
JOIN twin_runs tr ON sc.run_id = tr.run_id
WHERE tr.run_id = 'sim-20250809-123456';
```

## File System Structure

```
data/
├── mes_database.db              # Contains simulation_configs table
└── simulation_configs/
    ├── archive/                 # Migrated file configs
    │   ├── sim-20250809-*.json
    │   └── ...
    └── important/               # Exported important configs
        └── cfg-*.json
```

## Benefits

1. **No Repository Clutter**: Configs not tracked in git
2. **Deduplication**: Identical configs stored once
3. **Traceability**: Every config linked to runs
4. **Scalability**: Database handles thousands of configs efficiently
5. **Queryability**: SQL queries to find specific configurations
6. **Archival**: Important configs can be exported

## Cleanup and Maintenance

### Automatic Cleanup

Archive configs older than 30 days:

```python
config_mgr = ConfigurationManager()
archived = config_mgr.cleanup_old_configs(days_to_keep=30)
print(f"Archived {archived} old configurations")
```

### Manual Cleanup

Using the enhanced database cleanup tool:

```bash
# Remove archived configs from database
python api/database_setup_enhanced.py clean --tables simulation_configs --preserve important_configs

# Clean configs older than 60 days
python api/database_setup_enhanced.py clean --older-than 60
```

## Best Practices

1. **Always use ConfigurationManager** for config operations
2. **Link configs to runs** for traceability
3. **Add descriptions** to important configs
4. **Export critical configs** to files for long-term archive
5. **Regular cleanup** of old archived configs
6. **Use deduplication** - let the system handle duplicates

## Troubleshooting

### Config Not Found

```python
# Check if config exists
config = config_mgr.get_config("cfg-xyz")
if not config:
    # List available configs
    available = config_mgr.list_configs()
    print(f"Available configs: {[c['config_id'] for c in available]}")
```

### Duplicate Configs

The system automatically handles duplicates. If you see the message:
```
Config already exists with ID: cfg-20250810-141233-68915975
```
This means an identical configuration was already stored and the existing ID is being reused.

### Database Space

Check space used by configs:

```sql
SELECT 
    COUNT(*) as total_configs,
    SUM(LENGTH(config_json)) / 1024.0 / 1024.0 as size_mb
FROM simulation_configs
WHERE is_archived = 0;
```

## Migration Checklist

- [x] Database table created (`simulation_configs`)
- [x] Existing configs migrated to database
- [x] ConfigTransformer updated to save to DB
- [x] SimulationRunner updated to use DB configs
- [x] File configs moved to archive
- [x] `.gitignore` updated
- [x] Documentation created

## Future Enhancements

1. **Config Versioning**: Track config evolution over time
2. **Config Templates**: Predefined scenarios
3. **Config Validation**: Schema validation before storage
4. **Config Comparison**: Diff tool for configs
5. **Config Search**: Full-text search in configurations