# Enhanced Query Logging System

## Overview

The query logging system (`query-log.sh`) has been enhanced to support both historical MES queries and twin simulation queries, with rich context capture for machine learning and pattern analysis.

## Architecture

```
User Query (Natural Language)
         ↓
LLM Agent (Claude Code)
  • Understands intent
  • Translates NL to SQL
  • Determines category/domain
  • Provides context metadata
         ↓
query-log.sh
  • Accepts metadata from LLM
  • Auto-detects table categories
  • Logs with full context
  • Tracks for learning
         ↓
API Execution
  • Runs SQL query
  • Returns results
         ↓
Learning History
  • query_logs.json (all SQL queries)
  • twin_operations.jsonl (non-SQL twin ops)
```

## Enhanced Features

### 1. Natural Language Capture
Stores the original user query alongside the generated SQL for learning NL→SQL patterns.

### 2. Query Categorization
- **historical**: Queries against MES production data (mes_data, equipment_metadata)
- **twin**: Queries against simulation/optimization data (twin_runs, simulation_data)
- **hybrid**: Queries joining both domains

### 3. Domain Classification
- **mes_production**: Historical production data
- **simulation**: Twin simulation results
- **optimization**: Optimization and recommendations
- **state**: Twin state and parameters
- **comparison**: Comparing historical vs simulated
- **analysis**: Complex analytical queries

### 4. Auto-Detection
Automatically detects category and domain based on tables referenced in SQL.

### 5. Analytics Dashboard
Built-in analytics to analyze query patterns and usage.

## Usage

### Basic Query with Context

```bash
# Historical query
./query-log.sh POST /query \
  --nl "Which equipment has the lowest OEE?" \
  --intent "Identify maintenance priorities" \
  -d @query.json

# Twin query
./query-log.sh POST /query \
  --nl "Show recent simulation results" \
  --intent "Review simulations" \
  --category twin \
  -d @query.json

# Hybrid query
./query-log.sh POST /query \
  --nl "Compare baseline to optimized scenario" \
  --intent "Validate improvements" \
  -d @query.json
```

### View Analytics

```bash
# Show query analytics summary
./query-log.sh --analytics

# Output includes:
# - Total queries by category
# - Queries by domain
# - Recent NL queries
# - Most accessed tables
```

### View Specific Log Entry

```bash
# Show full details of a query
./query-log.sh --show-log <query_id>
```

## Log Structure

Each log entry contains:

```json
{
  "id": "20250815_151108_c7f9",
  "timestamp": "2025-08-15T19:11:08Z",
  "method": "POST",
  "endpoint": "/query",
  "intent": "Identify maintenance priorities",
  "natural_language": "Which equipment has the lowest OEE?",
  "category": "historical",
  "domain": "mes_production",
  "tables_accessed": "mes_data",
  "sql_query": "SELECT equipment_id, AVG(oee_score)...",
  "request_body": "{...}",
  "response": "{...}",
  "response_size": 242,
  "truncated": false,
  "status_code": 200
}
```

## LLM Agent Integration

As the LLM agent (Claude Code), I provide:

1. **Natural Language**: The original user query
2. **Intent**: Business purpose of the query
3. **Category**: Type of data being queried
4. **Domain**: Specific area of the system
5. **SQL**: The generated SQL query

This metadata enriches the logs for:
- Pattern learning
- Query optimization
- Usage analytics
- Audit trails

## Learning and Improvement

The logged data enables:

### 1. NL→SQL Pattern Analysis
Identify common query patterns and how users phrase requests.

### 2. Query Optimization
Spot inefficient queries and suggest improvements.

### 3. Usage Insights
Understand which data is most accessed and why.

### 4. Twin vs Historical Analysis
See the balance between historical analytics and twin simulations.

## Files and Storage

### Primary Logs
- `learning_history/query_logs.json` - All SQL queries with metadata

### Related Logs
- `learning_history/twin_operations.jsonl` - Non-SQL twin operations (financial calcs, etc.)

### Future Enhancements
- `learning_history/query_mappings.json` - NL→SQL pattern library
- `learning_history/query_templates.json` - Common query templates

## Best Practices

### For LLM Agents

1. **Always provide NL context** when available
2. **Set clear intent** for business understanding
3. **Let auto-detection work** unless override needed
4. **Use descriptive intents** (140 char max)

### For Query Analysis

1. **Regular analytics reviews** using `--analytics`
2. **Pattern extraction** from successful queries
3. **Error analysis** from failed queries
4. **Cross-domain insights** from hybrid queries

## Troubleshooting

### JSON Escaping Issues
Always use file references for complex queries:
```bash
echo '{"sql": "SELECT ..."}' > query.json
./query-log.sh POST /query -d @query.json
```

### Category Detection
- Based on table names in SQL
- Override with `--category` if needed
- Check with `--analytics` to verify

### Large Responses
- Automatically truncated for display
- Full response saved in log
- Use `--show-log <id>` to view full data

## Examples

### Historical Production Query
```bash
echo '{"sql": "SELECT line_id, AVG(oee_score) FROM mes_data GROUP BY line_id"}' > /tmp/q.json
./query-log.sh POST /query \
  --nl "What's the average OEE by production line?" \
  --intent "Line performance comparison" \
  -d @/tmp/q.json
```

### Twin Simulation Query
```bash
echo '{"sql": "SELECT * FROM twin_runs ORDER BY created_at DESC LIMIT 5"}' > /tmp/q.json
./query-log.sh POST /query \
  --nl "Show me recent simulation runs" \
  --intent "Review latest simulations" \
  --category twin \
  -d @/tmp/q.json
```

### Hybrid Comparison Query
```bash
echo '{"sql": "SELECT ... FROM mes_data JOIN simulation_data ..."}' > /tmp/q.json
./query-log.sh POST /query \
  --nl "Compare actual vs simulated performance" \
  --intent "Validate twin accuracy" \
  -d @/tmp/q.json
```

## Configuration

Edit the script to modify:
- `API_BASE_URL`: API endpoint (default: http://localhost:8000)
- `LOG_FILE`: Log storage location (default: learning_history/query_logs.json)
- `MAX_DISPLAY_SIZE`: Response truncation threshold (default: 5000 bytes)

## Future Roadmap

1. **Query Templates**: Pre-built templates for common queries
2. **Pattern Learning**: Automatic NL→SQL pattern extraction
3. **Query Suggestions**: Suggest similar successful queries
4. **Performance Metrics**: Track query execution times
5. **Visualization**: Dashboard for query analytics
6. **Export Capabilities**: Export logs for external analysis