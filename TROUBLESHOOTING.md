# Troubleshooting Guide

## Known System Characteristics

### Database & API
- **Database**: SQLite at `data/mes_database.db` (not PostgreSQL/MySQL)
- **Current Data**: Check with `SELECT MIN(date(timestamp)), MAX(date(timestamp)) FROM mes_data`
- **API Restrictions**: SELECT-only queries through query-log.sh
- **JSON Handling**: Inline JSON often fails - use file references

### KPI & Data Formats
- **KPI Storage**: All KPIs stored as percentages (e.g., 68.17 means 68.17%)
- **SimulationRun Access**: Use `result.kpi_summary['mean_oee']` NOT `result['mean_oee']` or `result.kpis`
- **OEE Values**: SimulationRun returns OEE as percentages (0-100), not fractions (0-1)
- **OEE Complexity**: Simulated OEE uses complex interaction model (not simple A×P×Q multiplication)
- **Production Value**: Query actual: `SELECT SUM(good_units_produced * sale_price_per_unit) FROM mes_data WHERE date(timestamp) = ?`

## SQLite-Specific Limitations

### Query Constraints
- No CTEs (WITH clauses) - use subqueries instead
- No STDDEV() - calculate manually or use approximations
- Use strftime() for date operations, not date functions
- JSON often needs escaping - always use file references

### Common Date Patterns
```sql
-- Single day data (most common)
WHERE date(timestamp) = '2025-06-01'

-- Date range
WHERE strftime('%Y-%m-%d', timestamp) BETWEEN '2025-06-01' AND '2025-06-07'  

-- Check current data period first:
SELECT MIN(date(timestamp)) as start_date, 
       MAX(date(timestamp)) as end_date 
FROM mes_data
```

## Data Management

### Checking Current Data
```bash
# Check data period
echo '{"sql": "SELECT MIN(date(timestamp)) as start, MAX(date(timestamp)) as end FROM mes_data"}' | ./query-log.sh POST /query

# Check table sizes
./api.sh status  # Shows all table record counts
```

### Managing Simulation Data
Simulation data accumulates over time (simulation_data table can have 800K+ records from multiple runs).
```bash
# Check simulation data size
echo '{"sql": "SELECT COUNT(*) as records, COUNT(DISTINCT run_id) as runs FROM simulation_data"}' | ./query-log.sh POST /query

# Note: API is read-only. To clean old simulations, coordinate with system admin.
# Consider using run_id filters in queries to focus on specific simulations.
```

## Debugging Workflow

When calculations seem wrong:
1. Create test script in `/tmp/debug_issue.py`
2. Check intermediate values step-by-step
3. Verify KPI formats (percentages vs fractions)
4. Compare estimated vs simulated results
5. Use smaller parameter changes to validate direction

## Error Recovery

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| API not running | Run `./api.sh start` |
| Query fails | Check JSON format uses "sql" field, not "query" |
| Import error | Verify PYTHONPATH is set correctly |
| No data returned | Check date ranges and table names in queries |
| Simulation fails | Ensure parameters are within valid ranges |

### Environment Setup Issues
- **ModuleNotFoundError**: Activate virtual environment: `source ~/.venvs/ont/bin/activate`
- **Path issues**: Set `PYTHONPATH=/Users/michael/github/virtual-ontology:$PYTHONPATH`

## Common Pitfalls

### Top 3 Gotchas (See `twin/docs/PATTERNS_REFERENCE.md` for solutions)
1. **KPI Confusion**: Treating percentages as fractions → 100x calculation errors
2. **SimulationRun Access**: Using `result['kpi_summary']` instead of `result.kpi_summary` → AttributeError
3. **Wrong Attribute**: Using `result.kpis` instead of `result.kpi_summary` → AttributeError

### Other Common Mistakes
4. **Parameter Signs**: Negative changes reduce the parameter, not the outcome
5. **Hardcoded Values**: Using default $500k instead of actual production value
6. **OEE Calculation**: Multiplying raw percentages instead of fractions
7. **API Queries**: Using "query" instead of "sql" in JSON → 400 errors

## Query Execution Tips

### File-based Approach (Recommended)
```bash
# Create query file with "sql" field
echo '{"sql": "SELECT COUNT(*) FROM mes_data"}' > /tmp/query.json
# Execute with METHOD and ENDPOINT  
./query-log.sh POST /query -d @/tmp/query.json
```

### Building Complex Queries
- Build complexity gradually - start simple, then layer
- For large result sets, data saves to `learning_history/query_logs.json`
- Use file references for JSON to avoid escaping issues

## Financial Impact Calculation

### Standard Approach
1. Query actual production value first:
   ```sql
   SELECT SUM(good_units_produced * sale_price_per_unit) as daily_revenue 
   FROM mes_data WHERE date(timestamp) = '2025-06-01'
   ```
2. Weekly value = daily_revenue * 7 (typically ~$4.1M)
3. Impact = weekly_value * (OEE_improvement_percentage_points / 100)

### Validation
- Always use actual production values, not hardcoded estimates
- Include confidence intervals in predictions
- Test with smaller parameter changes first