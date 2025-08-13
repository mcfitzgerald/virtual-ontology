# System Improvement Recommendations

## Issues Discovered During Bottleneck Analysis Session

### 1. Column Name Mismatch
**Problem**: SYSTEM_PROMPT references column names that don't match actual database
- Documentation says: `availability`, `performance`, `quality`
- Actual columns: `availability_score`, `performance_score`, `quality_score`

**Impact**: Failed queries until column names were discovered through data sampling

**Fix Required**:
- Update SYSTEM_PROMPT.md with correct column names
- Update ontology/database_schema.yaml with actual schema

### 2. Missing Column Documentation
**Problem**: Had to use `SELECT * FROM mes_data LIMIT 1` to discover schema since PRAGMA table_info is blocked

**Fix Required**:
- Add complete column listing in database_schema.yaml
- Include data types and descriptions for each column

### 3. JSON Escaping Issues
**Problem**: Multiple query failures due to quote escaping in inline JSON
- Single quotes in SQL within JSON cause parse errors
- Double escaping required but error-prone

**Fix Required**:
- Document best practice: always write to file first
- Add examples of proper escaping patterns in SYSTEM_PROMPT.md

### 4. SQLite Limitations Not Clear
**Problem**: Documentation doesn't clearly state SQLite-specific limitations
- No CTEs (WITH clauses)
- No STDDEV function
- Must use strftime() for date operations

**Fix Required**:
- Add "SQLite Limitations" section prominently in docs
- Provide SQLite-compatible alternatives for common operations

### 5. Undocumented Data Characteristics
**Problem**: Important data patterns not documented
- 216 records (8.3%) have null product_name with 0 OEE
- Downtime codes structure (PLN=Planned, UNP=Unplanned) not explained
- KPI values stored as percentages (68.17 = 68.17%, not 0.6817)

**Fix Required**:
- Add data dictionary for downtime codes
- Document null record handling
- Clarify percentage vs decimal storage

### 6. API Query Format Confusion
**Problem**: API expects `{"sql": "..."}` but error messages and some docs suggest `{"query": "..."}`

**Fix Required**:
- Standardize on one field name throughout system
- Update all documentation to use consistent format

### 7. Ontology-Database Mapping Gap
**Problem**: Ontology files don't provide clear mapping between conceptual names and actual column names

**Fix Required**:
- Add explicit mapping section in ontology_spec.yaml
- Example:
  ```yaml
  column_mappings:
    availability: availability_score
    performance: performance_score
    quality: quality_score
  ```

## Recommended Documentation Updates

### Add to SYSTEM_PROMPT.md:
```markdown
## Database Column Reference
| Conceptual Name | Actual Column | Type | Description |
|----------------|---------------|------|-------------|
| OEE | oee_score | REAL | OEE percentage (0-100) |
| Availability | availability_score | REAL | Availability percentage (0-100) |
| Performance | performance_score | REAL | Performance percentage (0-100) |
| Quality | quality_score | REAL | Quality percentage (0-100) |

## Downtime Reason Codes
- PLN-* : Planned downtime
  - PLN-CO: Changeover
  - PLN-CLN: Cleaning
- UNP-* : Unplanned downtime  
  - UNP-JAM: Equipment jam
  - UNP-ELEC: Electrical issue
  - UNP-SENS: Sensor failure
  - UNP-MAT: Material shortage
  - UNP-QC: Quality control stop
  - UNP-OPR: Operator issue
```

### Add Example Query Patterns:
```markdown
## Query Patterns That Work
# File-based approach (recommended)
echo '{"sql": "SELECT * FROM mes_data"}' > /tmp/query.json
./query-log.sh POST /query -d @/tmp/query.json

# Time-based queries (SQLite)
SELECT strftime('%H', timestamp) as hour, AVG(oee_score) 
FROM mes_data GROUP BY hour
```

## Quick Wins
1. Update SYSTEM_PROMPT.md with correct column names (5 min fix)
2. Add downtime code dictionary (10 min fix)
3. Document JSON file approach as best practice (5 min fix)

## Longer Term Improvements
1. Create comprehensive data dictionary
2. Add schema validation on API startup
3. Consider adding a /schema endpoint to API for discovery
4. Update ontology files with explicit mappings

## Testing Recommendations
- Add integration test that validates SYSTEM_PROMPT column names against actual schema
- Create test queries for all documented examples
- Validate ontology mappings against database schema on startup

## Issues Discovered During Virtual Twin & Recommendation Session

### 8. Virtual Environment Not Used by Default
**Problem**: Scripts failed with ModuleNotFoundError when not using virtual environment
- Initial attempts used system Python without required packages
- Virtual environment at `~/.venvs/ont` exists but wasn't documented clearly

**Impact**: Failed executions and confusion about dependencies

**Fix Required**:
- Add to SYSTEM_PROMPT.md: "Always use: `source ~/.venvs/ont/bin/activate`"
- Update all Python examples to include venv activation
- Consider adding automatic venv detection/activation

### 9. CostImpactCalculator Method Name Mismatch
**Problem**: Documentation/examples reference `calculate_financial_impact()` but actual method is `calculate_scenario_impact()`

**Impact**: AttributeError when following documentation

**Fix Required**:
- Update twin/API.md with correct method names
- Add docstrings with clear method signatures
- Consider adding backward compatibility aliases

### 10. CostImpactCalculator Signature Confusion
**Problem**: Method signature differs from expected:
- Expected: `calculate_scenario_impact(baseline_kpis, scenario_kpis, parameter_changes)`
- Actual: `calculate_scenario_impact(scenario, baseline_kpis, parameter_changes, n_simulations)`

**Impact**: TypeError due to missing required 'scenario' parameter

**Fix Required**:
- Document actual method signatures in twin/API.md
- Add type hints to all methods
- Create usage examples with actual signatures

### 11. RecommendationEngine Array Indexing Bug
**Problem**: RecommendationEngine.optimize() assumes 2D arrays but optimizer returns 1D for single-objective
- Line 317: `res.X[i, j]` fails when res.X is 1D
- Line 330: `res.F[i, j]` fails when res.F is 1D
- Line 343: `res.G[i]` fails when res.G is empty or wrong shape

**Impact**: IndexError preventing recommendations from working

**Fix Applied**:
```python
# Handle both 1D and 2D arrays
if len(res.X.shape) == 1:
    X_array = res.X.reshape(1, -1)
else:
    X_array = res.X
```

**Additional Fix Required**:
- Add unit tests for single vs multi-objective optimization
- Add array shape validation throughout
- Document expected array dimensions

### 12. ActionableParameters Missing Methods
**Problem**: Expected methods don't exist
- No `get_all()` method to retrieve all parameters
- Documentation suggests methods that aren't implemented

**Impact**: AttributeError when trying to inspect parameters

**Fix Required**:
- Add `get_all()` method to ActionableParameters
- Document all available methods clearly
- Add parameter introspection capabilities

### 13. RecommendationEngine Output Structure Undocumented
**Problem**: Output structure differs from expectations
- Returns 'parameters' not 'recommended_parameters'
- Returns 'expected_improvements' as deltas, not absolute values
- No clear documentation of output schema

**Impact**: KeyError when accessing expected fields

**Fix Required**:
- Document complete output schema in twin/API.md
- Add example output structures
- Consider standardizing field names across modules

### 14. Simulation Output Verbosity
**Problem**: SimulationRunner generates excessive output (~100 lines per run)
- Progress indicators flood console
- Hard to see actual results
- No quiet/verbose mode option

**Impact**: Difficult to debug and analyze results

**Fix Required**:
- Add `verbose` parameter to SimulationRunner
- Default to quieter output
- Add logging levels instead of print statements

## Process Learnings

### Virtual Twin Workflow Insights
1. **Always validate baseline first** - Run simulation with default parameters to ensure model matches historical data
2. **Parameter changes are multiplicative** - 0.5 means 50% reduction, not setting to 0.5
3. **Financial calculations need actual production values** - Don't use hardcoded $500k default

### Debugging Strategy That Worked
1. **Check method signatures first** - Use `inspect.signature()` 
2. **Test minimal examples** - Isolate the problem with simple test scripts
3. **Examine actual output structure** - Use `print(json.dumps(result, indent=2))` to understand data
4. **Fix at the source** - Don't work around bugs, fix them in the library

### Recommendation Engine Insights
1. **Genetic algorithms test thousands of combinations** - ~5000 parameter sets evaluated
2. **Single vs multi-objective require different handling** - Array dimensions change
3. **AI recommendations far exceed manual testing** - 19% improvement vs 2.7% from manual

## Updated Best Practices

### For Python Scripts
```python
#!/usr/bin/env python3
import sys
import os

# Always set Python path
sys.path.insert(0, '/Users/michael/github/virtual-ontology')

# Always activate venv in bash command
# source ~/.venvs/ont/bin/activate && python script.py
```

### For Debugging Twin Modules
```python
# Check available methods
import inspect
print(dir(object))
print(inspect.signature(method))

# Understand output structure
import json
result = method_call()
print(json.dumps(result, indent=2, default=str))
```

### For Production Analysis
1. Start with SQL analysis to establish baseline
2. Validate baseline with default simulation
3. Test single parameter changes first
4. Use RecommendationEngine for optimal combinations
5. Always calculate financial impact with actual values

## Priority Fixes
1. **CRITICAL**: Fix RecommendationEngine array handling (DONE in session)
2. **HIGH**: Document correct method signatures for all twin modules
3. **HIGH**: Add virtual environment activation to all examples
4. **MEDIUM**: Add verbose/quiet modes to simulation outputs
5. **LOW**: Standardize field names across modules