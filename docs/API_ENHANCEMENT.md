# API Enhancement Documentation

## Overview

The MES Virtual Twin API has been upgraded from v3.0.0 to v3.1.0 to support the more complex database architecture with 18 tables including simulation configurations. The API now provides comprehensive database management endpoints alongside the existing query and simulation capabilities.

## Key Improvements

### 1. **Fixed Critical Import Issue**
- **Problem**: API failed to start with `ModuleNotFoundError: No module named 'twin'`
- **Solution**: Corrected import paths in `simulation_endpoints.py`
- **Status**: ✅ API now starts successfully

### 2. **New Database Management Endpoints**
Added a complete suite of database management endpoints under `/api/database`:

#### Database Statistics (`GET /api/database/stats`)
Returns comprehensive database statistics including:
- File size in MB
- Total number of tables
- Total record count
- Record count per table

Example response:
```json
{
  "database_path": "/path/to/mes_database.db",
  "file_size_mb": 87.54,
  "total_tables": 17,
  "total_records": 2696,
  "tables": {
    "mes_data": 2592,
    "simulation_configs": 1,
    "twin_runs": 36,
    ...
  }
}
```

#### Table Information (`GET /api/database/tables`)
Lists all database tables with their structure:
- Table name
- Record count
- Column names
- Optional sample data

Query parameters:
- `include_sample`: Include sample data (default: false)
- `limit`: Number of sample rows (default: 5)

#### Configuration Management (`GET /api/database/configs`)
Lists simulation configurations stored in database:
- Configuration ID
- Associated run ID
- Configuration type (full, delta, base)
- Description
- Creation timestamp
- Configuration hash

#### Get Specific Config (`GET /api/database/config/{config_id}`)
Retrieves the full configuration JSON for a specific config ID.

#### Database Health Check (`GET /api/database/health`)
Performs health checks on the database:
- Integrity check
- Foreign key constraint validation
- Orphaned record detection
- Critical table existence verification

Response includes:
- Status: healthy, warning, or unhealthy
- List of issues (if any)
- List of warnings (if any)

#### Selective Cleanup (`POST /api/database/cleanup`)
Safely clean non-critical data with granular control:

Request body:
```json
{
  "category": "logs",  // Options: logs, simulation, optimization
  "tables": ["sync_health_log"],  // Specific tables
  "older_than_days": 7,  // Age-based cleanup
  "preserve": ["twin_runs"]  // Tables to preserve
}
```

Safety features:
- Only allows cleaning of safe, non-critical tables
- Cannot drop tables through API
- Cannot clean core data (mes_data, equipment_metadata, etc.)
- Validates all operations before execution

## API Architecture

### Router Organization

```
app (FastAPI)
├── / (root endpoints)
├── /query (SQL query execution)
├── /api/simulation/ (simulation endpoints)
│   ├── /run
│   ├── /optimize
│   └── /recommendations
└── /api/database/ (database management)
    ├── /stats
    ├── /tables
    ├── /configs
    ├── /config/{id}
    ├── /health
    └── /cleanup
```

### Safety Features

1. **Read-Only SQL Queries**: Main `/query` endpoint only accepts SELECT statements
2. **Safe Cleanup**: Cleanup endpoint restricted to non-critical tables
3. **Validation**: All operations validated before execution
4. **Error Handling**: Comprehensive error messages with HTTP status codes

## Usage Examples

### Check Database Health
```bash
curl http://localhost:8000/api/database/health
```

### Get Database Statistics
```bash
curl http://localhost:8000/api/database/stats
```

### List Tables with Sample Data
```bash
curl "http://localhost:8000/api/database/tables?include_sample=true&limit=3"
```

### List Simulation Configurations
```bash
curl http://localhost:8000/api/database/configs
```

### Clean Old Logs
```bash
curl -X POST http://localhost:8000/api/database/cleanup \
  -H "Content-Type: application/json" \
  -d '{"category": "logs", "older_than_days": 7}'
```

## Version History

### v3.1.0 (Current)
- Fixed import issues preventing API startup
- Added comprehensive database management endpoints
- Added database health monitoring
- Added selective cleanup capabilities
- Improved API documentation

### v3.0.0
- Added simulation endpoints
- Integrated Virtual Twin functionality
- Added optimization capabilities

### v2.0.0
- Basic SQL query execution
- FastAPI migration
- Initial MES data support

## Configuration

The API reads from the SQLite database at `data/mes_database.db` which now contains:

### Core Tables (17 total)
- **Historical Data**: mes_data, kpi_results
- **Simulation**: simulation_data, twin_runs, twin_state, parameter_history
- **Optimization**: optimization_results, recommendations
- **Configuration**: simulation_configs (new)
- **Metadata**: equipment_metadata, entity_sync_metadata, provenance_records
- **Monitoring**: quality_data, sensor_data, alert_config
- **Logs**: sync_health_log, confidence_tracking

## Development Notes

### Import Path Fix
The simulation endpoints previously used incorrect import paths with `twin.` prefix. This has been corrected to direct imports after adding the twin directory to sys.path:

```python
# Before (broken)
from twin.simulation_runner import SimulationRunner

# After (fixed)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twin'))
from simulation_runner import SimulationRunner
```

### Database Connection
All database endpoints use SQLite connections with proper transaction handling:

```python
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    # Operations here
    conn.commit()  # If modifying data
```

### Error Handling
All endpoints include proper error handling with meaningful HTTP status codes:
- 200: Success
- 400: Bad request (invalid parameters)
- 404: Resource not found
- 500: Internal server error

## Testing

Run the API:
```bash
./api.sh start
```

Test endpoints:
```bash
# Check API is running
curl http://localhost:8000/

# View interactive docs
open http://localhost:8000/docs

# Test database stats
curl http://localhost:8000/api/database/stats | jq
```

## Future Enhancements

1. **WebSocket Support**: Real-time database change notifications
2. **Backup/Restore Endpoints**: Database backup management through API
3. **Query History API**: Access to query_logs.json through API
4. **Metrics Endpoint**: Prometheus-compatible metrics
5. **GraphQL Support**: Alternative query interface
6. **Rate Limiting**: Protect against excessive requests
7. **Authentication**: Add API key or OAuth support for production

## Summary

The API has been successfully upgraded to handle the more complex database architecture while maintaining backward compatibility. The new database management endpoints provide visibility and control over the 18-table structure, while safety features ensure data integrity. The API is now more robust, maintainable, and ready for production use.