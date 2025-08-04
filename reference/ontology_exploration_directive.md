# Directive: Systematic Ontology Exploration Through SQL Pattern Discovery

## Mission
You are tasked with systematically exploring an ontology by generating and testing SQL queries that traverse its structure in diverse ways. Your goal is to discover effective patterns for navigating ontological relationships, hierarchies, and properties that can be reused for future query generation.

## Context
- **Ontology File**: `ontology/ontology_spec.yaml` - Contains classes, relationships, properties, and business rules
- **Database Schema**: `ontology/database_schema.yaml` - Maps ontology to SQL tables/columns
- **Data Table**: `mes_data` - Single denormalized table with all production data
- **Query Tool**: Use `./query-log.sh POST /query --intent "description" -d @/tmp/query.json`
- **Success Metric**: Generate working SQL that reveals interesting ontological patterns

## Exploration Strategy

### Phase 1: Class Hierarchy Exploration
Systematically test how to identify and filter class membership:

1. **Direct Class Filtering**
   - Test each class condition from the ontology (e.g., `machine_status = 'Running'` for ProductionLog)
   - Try filtering by each equipment subclass using `equipment_type`
   - Explore reason hierarchy with prefix patterns (`PLN-%`, `UNP-%`)

2. **Class Intersection**
   - Combine multiple class conditions (e.g., Running Fillers, Stopped Packers)
   - Test class membership across time windows
   - Find entities that switch classes

3. **Hierarchy Navigation**
   - Navigate from parent to child classes
   - Test CASE statements for dynamic classification
   - Explore multi-level hierarchies (UnplannedDowntime → MaterialJam)

### Phase 2: Relationship Traversal
Explore different ways to follow ontological relationships:

1. **Direct Relationships**
   - Test each relationship from ontology (belongsToLine, isUpstreamOf, etc.)
   - Use GROUP BY to aggregate along relationships
   - JOIN patterns for relationship following

2. **Transitive Relationships**
   - Chain multiple relationships (Line → Equipment → Events)
   - Explore upstream/downstream cascades
   - Time-correlated relationships

3. **Inverse Relationships**
   - Test both directions of bidirectional relationships
   - Aggregate from many-to-one perspectives
   - Find orphaned entities without relationships

### Phase 3: Property Pattern Discovery
Explore operations on ontological properties:

1. **Property Aggregation**
   - Test different aggregation functions on each property type
   - Combine properties in calculations (margins, ratios)
   - Statistical analysis (distributions, correlations)

2. **Property Constraints**
   - Test validation rules from ontology
   - Find constraint violations
   - Explore edge cases and boundaries

3. **Cross-Property Patterns**
   - Discover correlations between properties
   - Calculate derived metrics using business rules
   - Test property inheritance in hierarchies

### Phase 4: Temporal Patterns
Explore time-based traversal:

1. **Temporal Slicing**
   - Group by different time granularities (hour, shift, day, week)
   - Moving windows and rolling averages
   - Peak/valley detection

2. **Event Sequences**
   - Find patterns in event ordering
   - Detect state transitions
   - Measure time between related events

3. **Temporal Relationships**
   - Events happening simultaneously
   - Cascading events within time windows
   - Periodicity and seasonality

### Phase 5: Complex Traversals
Combine multiple patterns:

1. **Multi-Hop Queries**
   - Traverse multiple relationships in one query
   - Combine hierarchy navigation with aggregation
   - Cross-class correlations

2. **Conditional Traversal**
   - Different paths based on conditions
   - Dynamic relationship following
   - Adaptive aggregation strategies

3. **Ontology-Aware Analytics**
   - Use business rules in calculations
   - Apply domain constraints
   - Semantic aggregations

## Query Generation Guidelines

For each exploration attempt:

1. **Start with Intent**: Describe what ontological pattern you're exploring
2. **Map to SQL**: Translate the ontological concept to SQL constructs
3. **Test Incrementally**: Start simple, add complexity gradually
4. **Document Patterns**: Note successful patterns and why they work
5. **Handle Failures**: Learn from failed queries about system limitations

## Example Explorations

```sql
-- PATTERN: Navigate equipment hierarchy while aggregating KPIs
-- Intent: "Find average OEE for each equipment subclass"
SELECT 
  equipment_type as subclass,
  AVG(oee_score) as avg_oee,
  COUNT(DISTINCT equipment_id) as equipment_count
FROM mes_data
WHERE machine_status = 'Running'
GROUP BY equipment_type

-- PATTERN: Traverse relationships with temporal correlation  
-- Intent: "Find cascade patterns between upstream and downstream equipment"
SELECT 
  a.equipment_id as upstream,
  b.equipment_id as downstream,
  a.downtime_reason as upstream_reason,
  b.downtime_reason as downstream_reason,
  ABS(julianday(b.timestamp) - julianday(a.timestamp)) * 24 * 60 as minutes_apart
FROM mes_data a
JOIN mes_data b ON a.line_id = b.line_id
WHERE a.equipment_type = 'Filler'
  AND b.equipment_type = 'Packer'
  AND a.machine_status = 'Stopped'
  AND b.machine_status = 'Stopped'
  AND ABS(julianday(b.timestamp) - julianday(a.timestamp)) * 24 * 60 < 5

-- PATTERN: Apply business rules for semantic calculation
-- Intent: "Calculate true OEE impact including financial loss"
SELECT 
  equipment_id,
  AVG(oee_score) as avg_oee,
  SUM(CASE 
    WHEN oee_score < 85 THEN 
      (85 - oee_score) / 100 * target_rate_units_per_5min * (sale_price_per_unit - standard_cost_per_unit)
    ELSE 0 
  END) as opportunity_cost
FROM mes_data
WHERE machine_status = 'Running'
GROUP BY equipment_id
```

## Success Criteria

1. **Coverage**: Test all major classes, relationships, and properties
2. **Diversity**: Use various SQL constructs (JOIN, CASE, GROUP BY, window functions)
3. **Depth**: Explore multi-level hierarchies and transitive relationships
4. **Innovation**: Discover non-obvious traversal patterns
5. **Reusability**: Create parameterizable templates

## Output Format

For each successful pattern, document:
```yaml
pattern_name: "Hierarchical Equipment KPI Aggregation"
intent: "Navigate equipment hierarchy while computing KPIs"
ontology_concepts: ["Equipment", "hasOEEScore", "equipment_type"]
sql_template: |
  SELECT equipment_type, AVG({kpi_metric}) 
  FROM {table}
  WHERE {class_condition}
  GROUP BY equipment_type
example_use_case: "Compare performance across equipment types"
complexity: "simple|intermediate|advanced"
reusability: "high|medium|low"
```

## Constraints & Workarounds

Remember SQLite limitations:
- No STDDEV() - use MIN/MAX range
- No CTEs - use subqueries
- Date functions use strftime()
- No NOW() - use explicit dates for historical data

## Exploration Checklist

- [ ] Test all class hierarchy levels
- [ ] Traverse each relationship type
- [ ] Aggregate each property type
- [ ] Explore temporal patterns at multiple granularities
- [ ] Combine patterns for complex traversals
- [ ] Document reusable templates
- [ ] Identify system limitations
- [ ] Create pattern library

## Remember

The goal is not just to write working SQL, but to discover systematic ways to traverse the ontology that can be reused across different domains. Think of yourself as a cartographer mapping the navigational patterns of the ontological space.

Start with simple patterns and gradually increase complexity. Each query should teach you something about how to effectively traverse ontological structures through SQL.