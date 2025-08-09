# Migration Guide: Virtual Ontology → Virtual Twin System

## Overview

This guide provides a complete roadmap for migrating from the original Virtual Ontology project (semantic SQL generation) to the comprehensive Virtual Twin system (ISO 23247-compliant digital twin with simulation, optimization, and real-time monitoring).

## Architecture Evolution

### Original Virtual Ontology
```
Natural Language → Ontology Layer → SQL Generation → Database Query → Results
```

### Virtual Twin System
```
Natural Language → Intent Recognition → Digital Twin Core → Multiple Engines:
├── Simulation Engine (Monte Carlo, Optimization)
├── Real-time Sync (SOSA/SSN Sensors)
├── Financial Analysis (ROI Calculator)
├── Recommendation Engine (AI-powered)
├── GraphQL API (Type-safe, Real-time)
└── Visualization Suite (Interactive Plotly)
```

## Migration Path

### Phase 1: Foundation Extension (Keep Existing)
**Preserve the original virtual ontology components while building on top**

| Original Component | Status | Enhanced In Twin |
|-------------------|--------|------------------|
| `ontology/ontology_spec.yaml` | ✅ Keep | Extended with SOSA/SSN sensors |
| `ontology/database_schema.yaml` | ✅ Keep | Augmented with twin tables |
| `data/mes_database.db` | ✅ Keep | Added simulation tables |
| `query-log.sh` | ✅ Keep | Still functional |
| `sys_prompt.md` | ✅ Keep | Reference for NLP patterns |

### Phase 2: Add Digital Twin Core
**New components that extend the ontology foundation**

```bash
# New directories to add
twin/                         # Core digital twin implementation
├── twin_ontology.py         # SOSA/SSN sensor modeling
├── actionable_parameters.py # Parameter management
├── simulation_runner.py     # Simulation engine
└── sync_monitor.py          # Real-time monitoring

api/graphql/                 # GraphQL API layer
twin/visualization/          # Plotly visualizations
```

### Phase 3: Database Schema Extension
**Add new tables while preserving existing ones**

```sql
-- Original tables (KEEP)
- mesdata (36,000+ records)
- equipment_metadata
- quality_data

-- New twin tables (ADD)
- twin_runs
- simulation_data
- optimization_results
- provenance_records
```

## Component Mapping

### 1. Ontology Evolution

#### Original Ontology (ontology_spec.yaml)
```yaml
classes:
  Equipment:
    properties:
      - equipment_id
      - equipment_type
      - line
```

#### Enhanced Twin Ontology
```python
# twin/twin_ontology.py
class VirtualTwin:
    # Extends original with:
    - SOSA sensor observations
    - QUDT units
    - State machines
    - Real-time sync
    
# Preserves original concepts:
- Equipment hierarchy
- Line relationships
- Production metrics
```

### 2. Query Interface Evolution

#### Original Query Pattern
```bash
./query-log.sh "What is the OEE for LINE1?"
# Direct SQL generation
```

#### Enhanced Twin Pattern
```python
# Natural language with intent recognition
nlp = NaturalLanguageProcessor()
intent = nlp.classify_intent("What is the OEE for LINE1?")

# Multiple execution paths:
if intent == IntentType.STATUS:
    # Real-time query
    result = twin.get_current_state("LINE1")
elif intent == IntentType.PREDICTION:
    # Run simulation
    result = runner.run_simulation(...)
elif intent == IntentType.OPTIMIZATION:
    # Multi-objective optimization
    result = optimizer.optimize(...)
```

### 3. Data Access Evolution

#### Original: Direct SQL
```python
# Simple SQL query
query = "SELECT AVG(oee) FROM mesdata WHERE line = 'LINE1'"
```

#### Enhanced: Multi-Layer Access
```python
# Layer 1: Direct SQL (preserved)
legacy_query = "SELECT * FROM mesdata"

# Layer 2: Twin API
twin.get_equipment_state("LINE1-FIL")

# Layer 3: GraphQL
query GetStatus {
    getRun(runId: "current") {
        kpiSummary { meanOee }
    }
}

# Layer 4: Simulation
runner.run_simulation(RunType.BASELINE)
```

## Step-by-Step Migration Instructions

### Step 1: Backup Existing System
```bash
# Backup database
cp data/mes_database.db data/mes_database_backup.db

# Backup configurations
cp -r ontology/ ontology_backup/
```

### Step 2: Install New Dependencies
```bash
# Add to requirements.txt
rdflib>=6.0.0
strawberry-graphql>=0.200.0
plotly>=5.0.0
fastapi>=0.100.0
numpy>=1.20.0
scipy>=1.7.0

# Install
pip install -r requirements.txt
```

### Step 3: Initialize Twin Tables
```python
# scripts/init_twin_tables.py
import sqlite3

def add_twin_tables():
    conn = sqlite3.connect("data/mes_database.db")
    
    # Add twin_runs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS twin_runs (
            run_id TEXT PRIMARY KEY,
            run_type TEXT,
            status TEXT,
            timestamp TIMESTAMP,
            config_delta_json TEXT,
            kpi_summary_json TEXT
        )
    """)
    
    # Add other tables...
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_twin_tables()
    print("Twin tables added successfully")
```

### Step 4: Create Bridge Module
```python
# bridge/ontology_twin_bridge.py
"""Bridge between original ontology and twin system"""

from ontology import OntologySpec
from twin.twin_ontology import VirtualTwin

class OntologyTwinBridge:
    def __init__(self):
        self.ontology = OntologySpec.load("ontology/ontology_spec.yaml")
        self.twin = VirtualTwin("factory-twin")
    
    def sync_equipment(self):
        """Sync equipment from ontology to twin"""
        for equipment in self.ontology.get_equipment():
            self.twin.add_equipment(
                equipment_id=equipment['id'],
                equipment_type=equipment['type'],
                line=equipment['line']
            )
    
    def translate_query(self, natural_query: str):
        """Use both systems for query processing"""
        # Try original SQL generation
        sql_result = self.ontology.generate_sql(natural_query)
        
        # Enhance with twin capabilities
        nlp = NaturalLanguageProcessor()
        intent = nlp.classify_intent(natural_query)
        
        if intent in [IntentType.PREDICTION, IntentType.OPTIMIZATION]:
            # Use twin for advanced analysis
            return self.twin.process_advanced_query(natural_query)
        else:
            # Use original SQL
            return sql_result
```

### Step 5: Gradual Feature Adoption

#### Phase A: Basic Twin (Week 1)
```python
# Start with core twin
twin = VirtualTwin("my-factory")
twin.sync_with_ontology()  # Import from original

# Test basic operations
state = twin.get_current_state("LINE1-FIL")
```

#### Phase B: Add Simulation (Week 2)
```python
# Add simulation capability
runner = SimulationRunner()
baseline = runner.run_simulation(RunType.BASELINE)

# Compare with historical SQL queries
sql_avg = "SELECT AVG(oee) FROM mesdata"
sim_avg = baseline['kpi_summary']['mean_oee']
print(f"SQL: {sql_avg}, Simulation: {sim_avg}")
```

#### Phase C: Enable Optimization (Week 3)
```python
# Add optimization
optimizer = OptimizationEngine()
result = optimizer.optimize(
    objectives=["maximize:oee"],
    constraints=["quality >= 0.95"]
)
```

#### Phase D: GraphQL API (Week 4)
```python
# Launch API
# uvicorn api.main:app --reload

# Query via GraphQL
query = """
query {
    getRuns(limit: 10) {
        runId
        kpiSummary { meanOee }
    }
}
"""
```

## Compatibility Layer

### Maintaining Backward Compatibility

```python
# compat/legacy_support.py
class LegacySupport:
    """Ensures original virtual ontology queries still work"""
    
    def execute_legacy_query(self, query: str):
        """Execute original query-log.sh style queries"""
        # Parse intent
        if "SELECT" in query.upper():
            # Direct SQL
            return self.execute_sql(query)
        else:
            # Natural language - try both systems
            results = {
                'original': self.ontology_query(query),
                'twin': self.twin_query(query)
            }
            return self.merge_results(results)
    
    def query_log_compatible(self, intent: str, query: str):
        """Maintain query-log.sh compatibility"""
        # Log in original format
        with open("successful_patterns.log", "a") as f:
            f.write(f"Intent: {intent[:140]}\n")
            f.write(f"Query: {query}\n")
            f.write("---\n")
```

## Feature Comparison Matrix

| Feature | Virtual Ontology | Virtual Twin | Migration Path |
|---------|-----------------|--------------|----------------|
| **Natural Language SQL** | ✅ Core feature | ✅ Preserved | No change needed |
| **Ontology Mapping** | ✅ YAML-based | ✅ Extended with RDF | Import YAML → RDF |
| **Query Logging** | ✅ query-log.sh | ✅ Enhanced tracking | Keep script, add API |
| **Real-time Data** | ❌ Batch queries | ✅ Live monitoring | Add sync_monitor |
| **Predictive Analysis** | ❌ Historical only | ✅ Simulation | Add simulation_runner |
| **Optimization** | ❌ Not available | ✅ Multi-objective | Add optimization_engine |
| **Financial Analysis** | ⚠️ Basic SQL | ✅ Monte Carlo ROI | Add cost_calculator |
| **API Access** | ❌ CLI only | ✅ GraphQL | Add api/graphql |
| **Visualizations** | ❌ External tools | ✅ Plotly built-in | Add twin/visualization |
| **Standards** | ❌ Custom ontology | ✅ ISO 23247, W3C | Map to standards |

## Migration Validation

### Testing Strategy

```python
# tests/test_migration.py
import unittest

class TestMigration(unittest.TestCase):
    def test_original_queries_work(self):
        """Ensure original virtual ontology queries still function"""
        query = "What is the average OEE for LINE1?"
        
        # Original method
        original_result = execute_sql_query(query)
        
        # Twin method
        twin_result = twin.process_query(query)
        
        # Results should be consistent
        self.assertAlmostEqual(
            original_result['oee'],
            twin_result['kpi_summary']['mean_oee'],
            delta=0.01
        )
    
    def test_query_log_compatibility(self):
        """Verify query-log.sh still works"""
        import subprocess
        result = subprocess.run(
            ["./query-log.sh", "What is current OEE?"],
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)
    
    def test_database_integrity(self):
        """Ensure original data unchanged"""
        conn = sqlite3.connect("data/mes_database.db")
        
        # Check original tables exist
        cursor = conn.execute(
            "SELECT COUNT(*) FROM mesdata"
        )
        count = cursor.fetchone()[0]
        self.assertEqual(count, 36252)  # Original record count
```

## Common Migration Scenarios

### Scenario 1: Minimal Migration
**Goal**: Add twin capabilities without changing existing system

```python
# Minimal changes - just add twin as supplementary
twin = VirtualTwin("factory")
twin.import_from_ontology("ontology/ontology_spec.yaml")

# Use alongside existing queries
sql_result = query_database(sql)
twin_result = twin.enhance_with_prediction(sql_result)
```

### Scenario 2: Full Migration
**Goal**: Complete transition to twin system

```python
# Full migration - replace core with twin
# 1. Import all ontology concepts
migrator = OntologyMigrator()
migrator.convert_to_twin()

# 2. Switch query interface
app.route("/query", twin_api.handle_query)

# 3. Enable all features
twin.enable_feature("optimization")
twin.enable_feature("real_time_sync")
twin.enable_feature("graphql_api")
```

### Scenario 3: Hybrid Approach
**Goal**: Run both systems in parallel

```python
# Hybrid - best of both worlds
class HybridSystem:
    def process_request(self, query: str):
        # Classify query type
        if self.is_simple_query(query):
            # Use original for simple SQL
            return self.ontology.execute(query)
        elif self.needs_prediction(query):
            # Use twin for advanced
            return self.twin.simulate(query)
        else:
            # Use both and compare
            return self.ensemble_result(query)
```

## Rollback Strategy

If issues arise during migration:

```bash
# 1. Stop twin services
systemctl stop twin-api

# 2. Restore database
cp data/mes_database_backup.db data/mes_database.db

# 3. Revert code
git checkout main

# 4. Restart original system
./query-log.sh "Test query"
```

## Performance Considerations

### Resource Requirements

| Component | Virtual Ontology | Virtual Twin | Increase |
|-----------|-----------------|--------------|----------|
| **Memory** | ~100 MB | ~500 MB | 5x |
| **CPU** | Minimal | Moderate (simulations) | 10x peak |
| **Storage** | ~50 MB | ~500 MB | 10x |
| **Network** | None | Optional (API) | +API traffic |

### Optimization Tips

1. **Database Indexing**
```sql
-- Add indexes for twin queries
CREATE INDEX idx_twin_runs_timestamp ON twin_runs(timestamp);
CREATE INDEX idx_simulation_data_run ON simulation_data(run_id);
```

2. **Caching Strategy**
```python
# Cache frequent queries
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_kpis(equipment_id: str):
    return twin.get_kpis(equipment_id)
```

3. **Async Operations**
```python
# Use async for parallel processing
async def process_batch():
    tasks = [twin.process(item) for item in batch]
    return await asyncio.gather(*tasks)
```

## Migration Timeline

### Week 1-2: Planning & Preparation
- Backup existing system
- Review migration guide
- Set up development environment
- Install dependencies

### Week 3-4: Core Migration
- Add twin tables to database
- Implement bridge module
- Test backward compatibility
- Deploy twin_ontology module

### Week 5-6: Feature Addition
- Enable simulation runner
- Add optimization engine
- Implement cost calculator
- Test with real data

### Week 7-8: API & Visualization
- Deploy GraphQL API
- Add visualization suite
- Create dashboards
- User training

### Week 9-10: Testing & Optimization
- Performance testing
- User acceptance testing
- Documentation update
- Go-live preparation

## Success Metrics

Track these metrics to validate successful migration:

1. **Functional Metrics**
   - ✅ All original queries still work
   - ✅ New twin features accessible
   - ✅ API response time < 100ms
   - ✅ Simulation accuracy > 95%

2. **Performance Metrics**
   - ✅ Query performance maintained
   - ✅ Memory usage < 1GB
   - ✅ CPU usage reasonable
   - ✅ Database size manageable

3. **Business Metrics**
   - ✅ OEE improvement identified
   - ✅ ROI calculations available
   - ✅ User adoption > 80%
   - ✅ Decision time reduced

## Troubleshooting

### Common Issues

1. **Import Errors**
```python
# Fix: Update Python path
import sys
sys.path.append('/path/to/virtual-ontology')
```

2. **Database Lock**
```python
# Fix: Use connection pooling
from sqlalchemy.pool import StaticPool
engine = create_engine('sqlite:///data/mes_database.db',
                      connect_args={'check_same_thread': False},
                      poolclass=StaticPool)
```

3. **Memory Issues**
```python
# Fix: Batch processing
for batch in chunks(data, size=1000):
    process_batch(batch)
```

## Conclusion

The migration from Virtual Ontology to Virtual Twin represents an evolution, not a replacement. The original semantic SQL generation capabilities are preserved and enhanced with:

- Real-time monitoring and simulation
- Multi-objective optimization
- Financial impact analysis
- Standards compliance (ISO 23247)
- Modern API (GraphQL)
- Interactive visualizations

The migration can be done gradually, maintaining full backward compatibility while adding powerful new capabilities for digital twin operations.

---

*For additional support during migration, refer to the implementation documentation or contact the development team.*