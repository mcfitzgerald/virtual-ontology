# MES Query System Guide: Capabilities, Limitations & Best Practices

## Overview
This guide documents learnings from exploring the MES (Manufacturing Execution System) query interface, based on executing 30 diverse business queries. It covers system capabilities, limitations, workarounds, and best practices.

## System Architecture
- **Database**: SQLite (not PostgreSQL/MySQL)
- **API**: FastAPI on localhost:8000
- **Query Tool**: `query-log.sh` - bash wrapper for API calls with logging
- **Data**: Single `mes_data` table with 36,288 records (June 2025, 14 days)
- **Ontology**: Semantic layer mapping business concepts to SQL

## ✅ Confirmed Capabilities

### Data Operations That Work
- **Basic Aggregations**: COUNT, SUM, AVG, MIN, MAX
- **Grouping**: GROUP BY with multiple columns
- **Filtering**: WHERE clauses with AND/OR logic
- **Joins**: Self-joins for correlation analysis
- **CASE Statements**: Complex conditional logic
- **Window Functions**: LAG, LEAD, OVER with PARTITION BY
- **String Operations**: LIKE patterns, SUBSTR
- **Type Casting**: CAST() for numeric conversions
- **NULL Handling**: NULLIF, COALESCE
- **Ordering**: ORDER BY with multiple columns
- **HAVING**: Post-aggregation filtering
- **LIMIT**: Result set limiting

### SQLite Date Functions That Work
```sql
-- Extract hour (0-23)
CAST(strftime("%H", timestamp) AS INTEGER) as hour_of_day

-- Extract day of week (0=Sunday, 6=Saturday)  
strftime("%w", timestamp) as day_of_week

-- Extract date only
DATE(timestamp) as production_date

-- Date arithmetic (note: doesn't work with "now" in historical data)
DATE("now", "-7 days")  -- SQLite syntax
datetime(timestamp, "-1 hour")  -- Subtract time

-- Calculate time differences
(julianday(end_time) - julianday(start_time)) * 24 * 60 as minutes_between

-- Min/Max dates
MIN(timestamp) as earliest, MAX(timestamp) as latest

-- Count distinct dates
COUNT(DISTINCT DATE(timestamp)) as unique_days
```

## ❌ Limitations & Restrictions

### API Restrictions
1. **No CTEs (WITH clauses)**: Returns "Only SELECT statements are allowed"
   ```sql
   -- FAILS:
   WITH temp AS (SELECT ...) SELECT * FROM temp
   
   -- WORKAROUND: Use subqueries or multiple queries
   SELECT * FROM (SELECT ...) as temp
   ```

2. **SELECT-only**: No INSERT, UPDATE, DELETE, CREATE operations

3. **Default 1000 row limit**: Use `"limit": null` in JSON for unlimited

### Missing SQLite Functions
1. **No STDDEV()**: Statistical functions not available
   ```sql
   -- FAILS:
   STDDEV(oee_score)
   
   -- WORKAROUND: Use range or custom calculation
   MAX(oee_score) - MIN(oee_score) as range
   ```

2. **No NOW()**: Not a SQLite function
   ```sql
   -- FAILS:
   WHERE timestamp > NOW() - INTERVAL '1 hour'
   
   -- WORKS (but returns no data for historical dataset):
   WHERE timestamp > datetime('now', '-1 hour')
   ```

### Query Tool Quirks

#### JSON Escaping Issues with query-log.sh
The tool has problems with inline JSON due to shell escaping:

```bash
# FAILS - Shell mangles the JSON:
./query-log.sh POST /query -d '{"sql": "SELECT * FROM mes_data"}'

# WORKS - Use file reference:
echo '{"sql": "SELECT * FROM mes_data"}' > /tmp/query.json
./query-log.sh POST /query -d @/tmp/query.json

# ALSO WORKS - Direct curl:
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  --data-raw '{"sql": "SELECT * FROM mes_data"}'
```

## 📊 Query Patterns & Examples

### Pattern 1: Time-Based Aggregation
```sql
-- Hourly performance analysis
SELECT 
  CAST(strftime("%H", timestamp) AS INTEGER) as hour,
  AVG(oee_score) as avg_oee,
  COUNT(*) as samples
FROM mes_data
WHERE machine_status = "Running"
GROUP BY hour
ORDER BY hour
```

### Pattern 2: Equipment Correlation
```sql
-- Find cascade failures (upstream causes downstream)
SELECT 
  a.equipment_id as upstream,
  b.equipment_id as downstream,
  COUNT(*) as cascade_events
FROM mes_data a
JOIN mes_data b ON 
  ABS(julianday(a.timestamp) - julianday(b.timestamp)) * 24 * 60 < 5
WHERE a.downtime_reason LIKE "UNP-%"
  AND b.downtime_reason = "UNP-MAT"
  AND SUBSTR(a.equipment_id, 1, 5) = SUBSTR(b.equipment_id, 1, 5)
GROUP BY upstream, downstream
```

### Pattern 3: Financial Calculations
```sql
-- Calculate scrap cost and lost revenue
SELECT 
  product_name,
  SUM(scrap_units_produced) as total_scrap,
  SUM(scrap_units_produced * standard_cost_per_unit) as scrap_cost,
  SUM(scrap_units_produced * sale_price_per_unit) as lost_revenue
FROM mes_data
WHERE machine_status = "Running"
GROUP BY product_name
ORDER BY lost_revenue DESC
```

### Pattern 4: Window Functions for Trends
```sql
-- Daily performance with previous day comparison
SELECT 
  DATE(timestamp) as date,
  equipment_id,
  AVG(performance_score) as daily_avg,
  LAG(AVG(performance_score), 1) OVER (
    PARTITION BY equipment_id 
    ORDER BY DATE(timestamp)
  ) as prev_day_avg
FROM mes_data
WHERE machine_status = "Running"
GROUP BY DATE(timestamp), equipment_id
```

### Pattern 5: Distribution Analysis
```sql
-- OEE distribution in 10-point buckets
SELECT 
  ROUND(oee_score/10)*10 as oee_range,
  COUNT(*) as count,
  AVG(oee_score) as avg_in_range
FROM mes_data
WHERE machine_status = "Running"
GROUP BY oee_range
ORDER BY oee_range
```

## 🔧 Workarounds for Common Issues

### Issue: Need statistical functions
```sql
-- Instead of STDDEV, calculate range and quartiles
SELECT 
  MIN(oee_score) as min,
  MAX(oee_score) as max,
  MAX(oee_score) - MIN(oee_score) as range,
  AVG(oee_score) as mean
FROM mes_data
```

### Issue: Complex multi-step analysis
```sql
-- Without CTEs, use nested subqueries
SELECT * FROM (
  SELECT 
    equipment_id,
    AVG(oee_score) as avg_oee
  FROM mes_data
  GROUP BY equipment_id
) t
WHERE avg_oee < 70
```

### Issue: Date filtering with "current" time
```sql
-- For historical data, use actual date ranges
WHERE timestamp >= '2025-06-01' 
  AND timestamp <= '2025-06-14'

-- Instead of relative dates that won't match historical data
WHERE timestamp >= datetime('now', '-7 days')
```

## 🚀 Best Practices

1. **Always test JSON locally first**
   ```bash
   echo '{"sql": "YOUR QUERY"}' | jq .  # Validates JSON
   ```

2. **Use explicit type casting for calculations**
   ```sql
   CAST(good_units AS FLOAT) / total_units * 100
   ```

3. **Quote carefully in SQL**
   - Use double quotes for strings in SQLite
   - Use single quotes in bash/JSON contexts

4. **Handle NULL values explicitly**
   ```sql
   NULLIF(denominator, 0)  -- Prevent division by zero
   ```

5. **Add meaningful aliases**
   ```sql
   COUNT(*) * 5 as downtime_minutes  -- Clear unit indication
   ```

6. **Use HAVING for post-aggregation filters**
   ```sql
   GROUP BY equipment_id
   HAVING COUNT(*) > 100  -- Filter after grouping
   ```

## 📈 Performance Considerations

- **Large result sets**: Use LIMIT or aggregate to reduce data transfer
- **Complex joins**: Self-joins work but can be slow on 36K+ records
- **String operations**: LIKE with leading wildcard ('%pattern') is slower
- **Window functions**: Work well but add processing overhead

## 🎯 Query Checklist

Before running a query:
- [ ] Valid JSON syntax (test with `jq`)
- [ ] SQL uses double quotes for strings
- [ ] Date functions use SQLite syntax
- [ ] No CTEs (WITH clauses)
- [ ] Explicit type casting where needed
- [ ] LIMIT clause for exploration queries
- [ ] File-based input for query-log.sh (`-d @/tmp/query.json`)

## 📝 Example Workflow

```bash
# 1. Create query
cat > /tmp/my_query.json << 'EOF'
{
  "sql": "SELECT line_id, AVG(oee_score) as avg_oee FROM mes_data WHERE machine_status = \"Running\" GROUP BY line_id"
}
EOF

# 2. Validate JSON
jq . /tmp/my_query.json

# 3. Execute with logging
./query-log.sh POST /query --intent "Line OEE comparison" -d @/tmp/my_query.json

# 4. Check full results if truncated
./query-log.sh --show-log <query_id>
```

## 🔍 Debugging Tips

1. **API returns 422 error**: Check JSON formatting
2. **API returns 400 error**: Check SQL syntax, likely unsupported function
3. **Empty results**: Check date ranges match data (June 2025)
4. **Timeout**: Add LIMIT, simplify joins, or break into multiple queries
5. **"Only SELECT statements allowed"**: Remove CTEs, use subqueries

## 📚 References

- SQLite Date Functions: https://www.sqlite.org/lang_datefunc.html
- SQLite SQL Syntax: https://www.sqlite.org/lang.html
- Window Functions: https://www.sqlite.org/windowfunctions.html

---

*Generated from exploration of 30 business queries against MES ontology system*