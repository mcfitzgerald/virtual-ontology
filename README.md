# SQLOnt: Virtual Ontology for Direct SQL Generation

## Overview

SQLOnt is a prototype system that explores a novel approach to semantic data integration by creating a "virtual ontology" layer. Instead of materializing data into formal ontology formats (OWL/RDF) and triple stores, SQLOnt leverages Large Language Models (LLMs) to directly translate natural language queries into SQL using ontological context.

## Core Concept

Traditional semantic data systems require:
1. Formal ontology definition (OWL/RDF)
2. Data transformation into triple/graph format
3. Specialized query languages (SPARQL)
4. Complex ETL pipelines

**SQLOnt's approach:**
- Maintain data in existing SQL databases
- Define lightweight ontology (TBox/RBox with descriptions)
- Map ontological concepts to database schema
- Use LLM with ontology+schema context to generate SQL directly
- Capture query intent for pattern learning and improvement

## Key Innovation

By providing an LLM with both ontological structure and database schema mappings, we can preserve the semantic reasoning benefits of ontologies while eliminating the overhead of intermediate representations. This creates a more practical path to AI-compatible data access.

## System Architecture

INSERT DIAGRAM

### Components

1. **Ontology Declaration Layer**
   - TBox (Terminological Box): Class hierarchies and properties
   - RBox (Role Box): Relationship definitions and constraints
   - Natural language descriptions for context
   - Mappings to SQL schema elements

2. **Query Processing Pipeline**
   ```
   Natural Language Query
           �
   Concept Extraction
           �
   Context Selection (relevant ontology/schema fragments)
           �
   LLM SQL Generation
           �
   Query Execution (with limits for preview)
           �
   Result Caching / Full Execution
           �
   Python Analysis Tools (for complex operations)
   ```

3. **Learning Loop**
   - Semi-random SQL exploration of ontology/data space
   - Compilation of successful query patterns
   - Pattern compression and context enhancement
   - Gradual improvement of generation success rate

### Environment Requirements

Designed to operate in an LLM-powered development environment (like Claude Code) with:
- LLM access for query generation
- Planning and execution loop capabilities
- Conversation-driven refinement
- File read/write for caching
- Tool access for SQL execution and data source connections

## Implementation Strategy

### Context Optimization
- **Minimal Effective Context**: Balance between completeness and token efficiency
- **Dynamic Selection**: Choose relevant ontology fragments based on query intent
- **Pattern Library**: Cached successful query templates indexed by concepts

### Intent-Driven Pattern Learning
The system captures query intent at execution time, enabling pattern extraction and learning:

1. **Intent Capture**: LLM provides concise intent (≤140 chars) when generating SQL
2. **Query Logging**: Enhanced logging captures intent alongside SQL and results
3. **Pattern Extraction**: Simple extraction of successful query patterns
4. **LLM Analysis**: Pattern recognition and generalization by LLM

This creates a feedback loop where successful queries inform future generation.

### Failure Management
- **Human-in-the-Loop**: System augments human capability, not replace it
- **Progressive Refinement**: Iterative query improvement through conversation
- **Acceptable Failure Rate**: Optimize for speed and practicality over perfection

### Performance Optimization
- **Result Caching**: Local file store (Parquet/CSV) for query results
- **Preview Mode**: Use SQL LIMIT for LLM reasoning and verification
- **Python Processing**: Heavy analytical operations on cached data

## Example Workflow

INSERT VIDEO

## Advantages

1. **No ETL Required**: Work directly with existing SQL databases
2. **Semantic Reasoning**: Preserve ontological inference capabilities
3. **Practical Integration**: Lower barrier to semantic data access
4. **Flexible Evolution**: Learn and improve query patterns over time
5. **Human-Centric**: Augments rather than replaces human expertise

## Challenges & Mitigations

| Challenge | Mitigation Strategy |
|-----------|-------------------|
| Text-to-SQL failures | Ontology context reduces ambiguity |
| Complex joins | Query templates from ontology patterns |
| Context limits | Dynamic context selection |
| Semantic correctness | Validation against ontological constraints |
| Performance | Caching and preview mechanisms |

## Evaluation Metrics

Beyond traditional text-to-SQL benchmarks, SQLOnt requires evaluation of:
- **Semantic Correctness**: Queries respect ontological constraints
- **Inference Completeness**: Transitive/inherited relationships captured
- **Practical Efficiency**: Time-to-insight vs traditional approaches
- **User Satisfaction**: Reduction in query development time

## Project Status

**Current Stage**: Prototype with Working Demo

**Implemented Features**:
- ✅ SQL execution API with safety controls
- ✅ Intent-aware query logging system
- ✅ Pattern extraction from successful queries
- ✅ LLM-based SQL generation with ontological context
- ✅ Demonstration with real MES manufacturing data

**Next Steps**:
- Automated context selection based on query intent
- Expand pattern library through continued use
- Implement confidence scoring for generated queries
- Add support for multiple data sources

## Future Directions

- Integration with existing ontology standards (OWL/RDFS)
- Automated ontology extraction from database schemas
- Multi-database federation through virtual ontology layer
- Query optimization using ontological constraints
- Benchmark development for semantic SQL generation

## Demo: Manufacturing Execution System (MES)

This repository includes a demonstration of SQLOnt using Manufacturing Execution System (MES) data from a bottled beverage production facility. The demo showcases how ontological context enables natural language queries against production data.

### Starting the SQL API

The demo includes a FastAPI-based SQL interface for querying the MES database:

```bash
# Start the API server
./api.sh start

# Check API status
./api.sh status

# Stop the API server
./api.sh stop

# Restart the API
./api.sh restart
```

Once started, the API is available at:
- API endpoint: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- SQL execution: `POST /query` with JSON body `{"sql": "SELECT...", "limit": 1000}`

### Executing Queries with Intent Tracking

The `query-log.sh` wrapper enables intent-aware query execution:

```bash
# Execute query with intent description
./query-log.sh POST /query \
  --intent "Find equipment causing downstream starvation" \
  -d '{"sql": "SELECT * FROM mes_data WHERE..."}'

# View logged queries
./query-log.sh --show-log <query_id>
```

Intent descriptions (≤140 chars) are logged alongside SQL for pattern learning.

### Sample Data

The MES dataset (`data/mes_data_with_kpis.csv`) contains production metrics captured at 5-minute intervals:

| Timestamp | ProductionOrderID | LineID | EquipmentID | EquipmentType | ProductID | ProductName | MachineStatus | DowntimeReason | GoodUnitsProduced | ScrapUnitsProduced | TargetRate_units_per_5min | StandardCost_per_unit | SalePrice_per_unit | Availability_Score | Performance_Score | Quality_Score | OEE_Score |
|-----------|------------------|--------|-------------|---------------|-----------|-------------|---------------|----------------|-------------------|-------------------|---------------------------|----------------------|-------------------|-------------------|------------------|---------------|-----------|
| 2025-06-01 00:00:00 | ORD-1000 | 1 | LINE1-FIL | Filler | SKU-2002 | 16oz Energy Drink | Running | | 218 | 4 | 450 | 0.55 | 1.75 | 100.0 | 49.3 | 98.2 | 48.4 |
| 2025-06-01 00:00:00 | ORD-1000 | 1 | LINE1-PCK | Packer | SKU-2002 | 16oz Energy Drink | Stopped | UNP-JAM | 0 | 0 | 450 | 0.55 | 1.75 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2025-06-01 00:00:00 | ORD-1000 | 1 | LINE1-PAL | Palletizer | SKU-2002 | 16oz Energy Drink | Running | | 249 | 5 | 450 | 0.55 | 1.75 | 100.0 | 56.4 | 98.0 | 55.3 |
| 2025-06-01 00:00:00 | ORD-1039 | 2 | LINE2-FIL | Filler | SKU-2001 | 12oz Soda | Running | | 324 | 4 | 475 | 0.2 | 0.65 | 100.0 | 69.1 | 98.8 | 68.2 |
| 2025-06-01 00:00:00 | ORD-1039 | 2 | LINE2-PCK | Packer | SKU-2001 | 12oz Soda | Stopped | UNP-JAM | 0 | 0 | 475 | 0.2 | 0.65 | 0.0 | 0.0 | 0.0 | 0.0 |

The data includes:
- **Production metrics**: Units produced (good/scrap), target rates
- **Equipment status**: Running/Stopped states with downtime reason codes
- **Financial data**: Standard costs and sale prices per unit
- **KPI scores**: Availability, Performance, Quality, and OEE (Overall Equipment Effectiveness)

### Ontology Structure

The MES ontology (`ontology/ontology_spec.yaml`) defines the conceptual model:

#### Class Hierarchy (TBox)
- **Process**: Manufacturing workflows
  - ProductionOrder: Customer-driven manufacturing requests
- **Resource**: Production assets
  - Equipment: Physical machines (Filler, Packer, Palletizer)
  - ProductionLine: Complete equipment sets
  - Product: Manufactured items
- **Event**: Time-stamped occurrences
  - ProductionLog: Metrics when equipment is running
  - DowntimeLog: Stoppage events with reasons
- **Reason**: Categorized explanations
  - PlannedDowntime: Changeover, Cleaning, Preventive Maintenance
  - UnplannedDowntime: Mechanical Failure, Material Jam, Quality Check, etc.

#### Relationships (RBox)
- **Equipment flow**: `isUpstreamOf`/`isDownstreamOf` - Material flow direction
- **Line membership**: `belongsToLine`/`hasEquipment` - Equipment-line associations
- **Production tracking**: `executesOrder`, `producesProduct` - Order fulfillment
- **Event logging**: `logsEvent`, `hasDowntimeReason` - Historical records

### Database Schema

The database schema (`ontology/database_schema.yaml`) maps the ontological concepts to SQL tables, providing the bridge between semantic queries and the underlying data structure.

### Pattern Learning Workflow

1. **Execute queries with intent**:
```bash
echo '{"sql": "SELECT COUNT(*) FROM mes_data"}' | \
  ./query-log.sh POST /query --intent "Count total records" -d @-
```

2. **Extract successful patterns**:
```bash
python3 extract_queries.py
# Creates extracted_patterns.yaml with intent-SQL pairs
```

3. **Analyze patterns** (LLM task):
- Identify common SQL structures
- Map intents to ontological concepts
- Generate reusable templates

### Example Queries

With the ontology and schema context, natural language queries like these become possible:

- "Show me all unplanned downtime events for fillers in the last week"
- "Which production line has the best OEE score for energy drinks?"
- "Find all material jams that occurred downstream of equipment with mechanical failures"
- "Calculate the total production loss from preventive maintenance activities"

These queries leverage the ontological understanding of equipment relationships, downtime categorization, and production flow without requiring users to know the specific database structure.

### Discovered Query Patterns

Through intent-driven pattern learning, the system identifies reusable patterns:

1. **Status Queries**: Use `MAX(timestamp)` for current state
2. **Performance Analysis**: Aggregate with `AVG()`, filter by `Running` status
3. **Categorization**: Use `CASE` statements with ontology-aware prefixes
4. **Relationship Analysis**: Self-joins for equipment cascade effects

## Contributing

This is an experimental project exploring the intersection of semantic technologies and modern LLM capabilities. Contributions, ideas, and use cases are welcome.

## License

[To be determined]