# Database Setup System

## Overview

The Virtual Twin database setup system provides a unified initialization and management interface for all database operations. It handles both historical MES data generation and Virtual Twin table creation through a single, easy-to-use command-line interface.

## Quick Start

```bash
# Initialize fresh database with sample data
python api/database_setup.py init

# Initialize with historical MES data (for testing/demos)
python api/database_setup.py init --historical --start-date 2025-06-01 --end-date 2025-06-14
```

## Commands

### Initialize Database (`init`)

Creates all necessary tables and optionally populates with sample or historical data.

```bash
# Basic initialization with sample data
python api/database_setup.py init

# Without sample data (structure only)
python api/database_setup.py init --no-sample-data

# With historical MES data
python api/database_setup.py init --historical --start-date 2025-06-01 --end-date 2025-06-14
```

### Clean Database (`clean`)

Removes data while optionally preserving structure.

```bash
# Clean data but keep tables (default)
python api/database_setup.py clean

# Complete clean - drop all tables
python api/database_setup.py clean --drop-tables
```

**Note**: Automatic backup is created before cleaning at `data/mes_database.db.backup_YYYYMMDD_HHMMSS`

### Verify Database (`verify`)

Checks database integrity and structure.

```bash
# Basic verification
python api/database_setup.py verify

# Detailed verification with constraint checks
python api/database_setup.py verify --detailed
```

### Generate Sample Data (`generate`)

Creates sample MES data for testing or development.

```bash
# Generate to CSV file
python api/database_setup.py generate --format csv --start-date 2025-06-01 --end-date 2025-06-07

# Generate directly to database
python api/database_setup.py generate --format db --start-date 2025-06-01 --end-date 2025-06-07

# Generate to both CSV and database
python api/database_setup.py generate --format both
```

## Database Structure

### Core Tables

#### Historical MES Data
- `mes_data` - Main manufacturing execution system data
- `simulation_data` - Generated simulation results
- `kpi_results` - Calculated KPI metrics

#### Virtual Twin Tables
- `twin_runs` - Twin simulation metadata
- `twin_state` - Current twin configuration
- `parameter_history` - Parameter change tracking
- `optimization_results` - Optimization run results
- `recommendations` - Generated recommendations
- `provenance_records` - PROV-O compliant tracking

#### Supporting Tables
- `equipment_metadata` - Equipment specifications
- `quality_data` - Quality metrics and defects
- `sensor_data` - Real-time sensor readings
- `alert_config` - Alert thresholds and rules
- `entity_sync_metadata` - Entity synchronization
- `sync_health_log` - System health tracking
- `confidence_tracking` - Model confidence metrics

## Configuration

The system uses `api/setup/config.json` for all configuration:

```json
{
  "database": {
    "path": "data/mes_database.db",
    "backup_enabled": true
  },
  "historical_data": {
    "default_days": 14,
    "records_per_day": 2592
  },
  "sample_data": {
    "equipment_count": 9,
    "quality_records": 6480,
    "sensor_records": 7776
  }
}
```

## Clean/Flush Mechanism

The database clean mechanism uses SQLite's built-in features for safe cleanup:

1. **Backup Creation**: Automatic backup before any destructive operation
2. **Transaction Safety**: All operations wrapped in transactions
3. **VACUUM Support**: Optimizes database after major cleanups
4. **Cascade Deletes**: Proper foreign key constraint handling

### Clean Levels

1. **Data Clean** (default): Removes all data, preserves structure
   - Uses `DELETE FROM` for each table
   - Maintains referential integrity
   - Resets auto-increment counters

2. **Full Clean** (`--drop-tables`): Complete database reset
   - Drops all tables
   - Removes all indexes
   - Requires re-initialization

### Recovery

If something goes wrong:

```bash
# List available backups
ls -la data/*.backup*

# Restore from backup
mv data/mes_database.db.backup_20250810_135602 data/mes_database.db

# Verify restored database
python api/database_setup.py verify --detailed
```

## Development

### Adding New Tables

1. Add table creation in `twin_tables.py`:
```python
def create_twin_tables(conn):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS your_new_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ...
        )
    """)
```

2. Update verification in `verify_database_setup()`:
```python
expected_tables.append('your_new_table')
```

3. Add to clean operations if needed:
```python
tables_to_clean.append('your_new_table')
```

### Extending Historical Data

Modify `mes_historical.py` to add new data patterns:

```python
def add_custom_anomaly(df, config):
    # Add your anomaly logic
    return df
```

## Troubleshooting

### Common Issues

**Database locked error**:
```bash
# Stop API server if running
./api.sh stop

# Then retry operation
python api/database_setup.py init
```

**Corrupt database**:
```bash
# Use clean with drop-tables
python api/database_setup.py clean --drop-tables

# Reinitialize
python api/database_setup.py init
```

**Missing tables after clean**:
```bash
# Reinitialize to recreate structure
python api/database_setup.py init --no-sample-data
```

### Logging

Logs are written to:
- Console (INFO level and above)
- `logs/database_setup.log` (DEBUG level)

To increase verbosity:
```python
# In database_setup.py
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Always verify after major operations**:
   ```bash
   python api/database_setup.py clean --drop-tables
   python api/database_setup.py init
   python api/database_setup.py verify --detailed
   ```

2. **Use historical data for realistic testing**:
   ```bash
   python api/database_setup.py init --historical
   ```

3. **Keep backups of important states**:
   ```bash
   cp data/mes_database.db data/mes_database.db.golden
   ```

4. **Test changes with generate first**:
   ```bash
   python api/database_setup.py generate --format csv
   # Review CSV before loading to database
   ```

## Integration with Virtual Twin

The database setup system is designed to work seamlessly with the Virtual Twin system:

1. **Historical data** provides baseline for simulations
2. **Twin tables** store simulation results and optimizations
3. **Equipment metadata** defines operational constraints
4. **Alert configurations** enable proactive monitoring

After initialization, the system is ready for:
- Natural language queries via Claude Code
- Twin simulations and optimizations
- Financial ROI calculations
- Predictive analytics

## Support

For issues or questions:
1. Check logs in `logs/database_setup.log`
2. Run verification: `python api/database_setup.py verify --detailed`
3. Review this documentation
4. Check the main [SYSTEM_ARCHITECTURE.md](../../docs/SYSTEM_ARCHITECTURE.md)