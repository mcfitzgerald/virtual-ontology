# SQLite Workarounds for SQLOnt System

Based on the MES experiment analysis, here are proven workarounds for SQLite limitations encountered in the virtual ontology system.

## Missing Functions

### 1. STDDEV() - Standard Deviation
**Problem**: SQLite doesn't have built-in STDDEV function
**Workaround**: Use range or approximation methods

```sql
-- Instead of STDDEV(oee_score)
SELECT 
  AVG(oee_score) as mean,
  MAX(oee_score) - MIN(oee_score) as range,
  CAST(SUM(CASE WHEN oee_score > AVG(oee_score) THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as above_mean_pct
FROM mes_data
```

### 2. NOW() - Current Timestamp
**Problem**: NOW() doesn't exist in SQLite
**Workaround**: Use datetime('now') but be aware it won't match historical data

```sql
-- Don't use:
WHERE timestamp > NOW() - INTERVAL '7 days'

-- Use for current time:
WHERE timestamp > datetime('now', '-7 days')

-- For historical data, use explicit dates:
WHERE timestamp BETWEEN '2025-06-07' AND '2025-06-14'
```

## SQL Construct Restrictions

### 3. CTEs (Common Table Expressions)
**Problem**: API rejects CTEs as "not SELECT statements"
**Workaround**: Use subqueries

```sql
-- Instead of:
WITH daily_stats AS (
  SELECT DATE(timestamp) as day, AVG(oee_score) as avg_oee
  FROM mes_data
  GROUP BY day
)
SELECT * FROM daily_stats WHERE avg_oee > 70

-- Use:
SELECT * FROM (
  SELECT DATE(timestamp) as day, AVG(oee_score) as avg_oee
  FROM mes_data
  GROUP BY DATE(timestamp)
) AS daily_stats
WHERE avg_oee > 70
```

## Date/Time Functions

### 4. Date Extraction
**Problem**: Different syntax from other databases
**Workaround**: Use strftime()

```sql
-- Hour extraction:
CAST(strftime('%H', timestamp) AS INTEGER) as hour

-- Day of week (0=Sunday):
CAST(strftime('%w', timestamp) AS INTEGER) as day_of_week

-- Date only:
DATE(timestamp)

-- Month:
strftime('%Y-%m', timestamp) as month
```

### 5. Date Differences
**Problem**: No DATEDIFF function
**Workaround**: Use julianday()

```sql
-- Days between dates:
julianday(end_date) - julianday(start_date) as days_diff

-- Hours between timestamps:
(julianday(end_time) - julianday(start_time)) * 24 as hours_diff
```

## Tool-Specific Issues

### 6. query-log.sh JSON Escaping
**Problem**: Shell mangles inline JSON with complex SQL
**Workaround**: Use file reference

```bash
# Don't use inline JSON:
./query-log.sh POST /query --intent "test" -d '{"sql": "SELECT..."}'

# Create file first:
cat > /tmp/query.json << 'EOF'
{"sql": "SELECT * FROM mes_data WHERE equipment_id = 'LINE1-FIL' LIMIT 10"}
EOF

# Then reference file:
./query-log.sh POST /query --intent "Test query" -d @/tmp/query.json
```

## Performance Considerations

### 7. Default Row Limits
**Problem**: API defaults to 1000 rows
**Workaround**: Explicitly specify higher limits when needed

```json
{
  "sql": "SELECT * FROM mes_data",
  "limit": 50000
}
```

### 8. Index Usage
**Note**: SQLite query planner is generally good, but for large datasets:

```sql
-- Ensure timestamp filtering comes first for time-series:
WHERE timestamp BETWEEN '2025-06-01' AND '2025-06-14'
  AND equipment_id = 'LINE1-FIL'
  
-- Not:
WHERE equipment_id = 'LINE1-FIL'
  AND timestamp BETWEEN '2025-06-01' AND '2025-06-14'
```

## Statistical Functions

### 9. Percentiles
**Problem**: No built-in percentile functions
**Workaround**: Use NTILE or manual calculation

```sql
-- Approximate median (50th percentile):
SELECT AVG(oee_score) as median
FROM (
  SELECT oee_score
  FROM mes_data
  ORDER BY oee_score
  LIMIT 2 - (SELECT COUNT(*) FROM mes_data) % 2
  OFFSET (SELECT (COUNT(*) - 1) / 2 FROM mes_data)
)
```

## Best Practices

1. **Always test date functions** with your actual data timeframe
2. **Avoid complex string concatenation** in SQL - SQLite handles it differently
3. **Use CAST() explicitly** when converting types
4. **Remember LIMIT defaults** and specify when needed
5. **Test query in pieces** when debugging complex statements
6. **Use parameterized templates** for reusable patterns

## Success Patterns

Based on 86% success rate from 30+ queries:

1. **Simple aggregations work perfectly**: COUNT, SUM, AVG, MIN, MAX
2. **Window functions ARE supported**: LAG, LEAD, OVER
3. **CASE statements work well**: Great for categorization
4. **Self-joins work**: Useful for correlation analysis
5. **strftime is powerful**: Handles most time-based needs

## Migration Path

If moving to PostgreSQL later:
- CTEs will work immediately
- STDDEV and other statistical functions available
- Better date/time handling with INTERVAL
- Keep templates parameterized for easy migration