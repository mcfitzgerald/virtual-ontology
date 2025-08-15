# Virtual Twin Module

Manufacturing Digital Twin Simulation & Optimization Framework

## Overview

The Virtual Twin module provides a comprehensive digital twin framework for manufacturing systems, enabling:

- **What-if Scenario Simulation**: Test parameter changes and predict impacts
- **Multi-objective Optimization**: Find optimal parameter configurations using NSGA-II
- **Intelligent Recommendations**: Get scenario-based improvement suggestions
- **Financial Impact Analysis**: Calculate ROI and cost implications
- **Natural Language Understanding**: Interpret queries using disambiguation patterns
- **Database Integration**: Pristine reset, config storage, unified schema management (v1.3.0)

## Architecture

The module follows a layered architecture:

```
twin/
├── Core Components (Simulation & State)
│   ├── simulation_runner.py      # Execute simulations
│   ├── actionable_parameters.py  # Parameter management
│   ├── twin_state.py            # State tracking
│   ├── config_transformer.py    # Config generation
│   └── config_manager.py        # Config storage
│
├── Analysis Components (Optimization & Recommendations)
│   ├── optimization_engine.py   # Multi-objective optimization
│   ├── recommendation_engine.py # Scenario recommendations
│   └── cost_impact_calculator.py # Financial analysis
│
├── Support Components (Helpers)
│   ├── disambiguation.py        # NLP query interpretation
│   ├── sync_health.py          # Synchronization monitoring
│   └── line_coupling_model.py  # Production line interactions
│
└── visualization/              # Plotting utilities
    ├── time_series.py
    ├── pareto_plots.py
    ├── heatmaps.py
    └── financial_plots.py
```

## Key Concepts

### Actionable Parameters

The system manages 5 key tunable parameters that affect manufacturing performance:

1. **micro_stop_probability** (0.0-1.0): Likelihood of brief equipment stops
2. **performance_factor** (0.5-1.0): Equipment speed/efficiency multiplier
3. **scrap_multiplier** (0.5-2.0): Quality/scrap rate adjustment
4. **material_reliability** (0.5-1.0): Supply chain reliability factor
5. **cascade_sensitivity** (0.0-1.0): Downstream impact propagation strength

### Simulation Runs

Each simulation creates a tracked run with:
- Unique run ID for traceability
- Parent run linkage for lineage tracking
- Parameter configuration deltas
- KPI summaries (OEE, availability, performance, quality)
- Full provenance and audit trail

### Optimization Objectives

The system can optimize for multiple objectives simultaneously:
- **OEE** (Overall Equipment Effectiveness)
- **Energy Efficiency** (kWh per unit)
- **Quality** (Scrap rate minimization)
- **Throughput** (Units per hour)
- **Cost** (Total operational cost)

## Usage Examples

### Basic Simulation

```python
from twin import SimulationRunner, ActionableParameters

# Initialize
runner = SimulationRunner()
params = ActionableParameters()

# Set parameters
params.set_value("micro_stop_probability", 0.05)  # Reduce micro-stops by 50%

# Run simulation
result = runner.run_simulation(
    parameters=params,
    duration_days=7,
    notes="Testing improved maintenance"
)

print(f"OEE: {result.kpi_summary['mean_oee']:.1%}")
```

### Multi-objective Optimization

```python
from twin import OptimizationEngine

engine = OptimizationEngine()

# Find Pareto-optimal solutions
results = engine.run_optimization(
    objectives=["mean_oee", "energy_per_unit"],
    directions=["maximize", "minimize"],
    population_size=50,
    n_generations=20
)

# Results contain non-dominated solutions
for solution in results["pareto_front"]:
    print(f"OEE: {solution['objectives']['mean_oee']:.1%}")
    print(f"Energy: {solution['objectives']['energy_per_unit']:.2f} kWh/unit")
    print(f"Parameters: {solution['parameters']}")
```

### Getting Recommendations

```python
from twin import RecommendationEngine

engine = RecommendationEngine()

# Get recommendations for specific scenario
recommendations = engine.recommend_for_oee_improvement()

for rec in recommendations:
    print(f"{rec['parameter']}: {rec['recommended_value']}")
    print(f"Expected impact: {rec['expected_impact']}")
```

### Natural Language Query Disambiguation

```python
from twin import DisambiguationHelper

helper = DisambiguationHelper()

# Get context for ambiguous query
context = helper.get_query_context("improve quality on the packer")

# Context includes:
# - Identified entities (equipment: PCK)
# - Likely parameters (scrap_multiplier)
# - Suggested clarifications
# - Available timeframes
```

## Integration

### With API

The module is integrated with FastAPI endpoints:
- `/api/simulation/run` - Execute simulations
- `/api/simulation/optimize` - Run optimization
- `/api/simulation/recommend/{scenario}` - Get recommendations

### With Database

All simulation data is persisted to SQLite database:
- `twin_runs` - Simulation metadata and results
- `simulation_data` - Detailed time-series data
- `parameter_history` - Parameter change tracking
- `simulation_configs` - Configuration storage

### With LLM (Claude Code)

The module is designed for Natural Language REPL pattern:
1. LLM interprets user queries
2. Calls appropriate twin functions
3. Interprets and presents results

## Configuration

### Simulation Configuration

Default configurations stored in database:
- Base parameter values
- KPI calculation methods
- Equipment relationships
- Production constraints

## Performance Considerations

- Simulations typically run in 1-5 seconds
- Optimization may take 30-60 seconds for 50 generations
- Database queries optimized with indexes
- Configuration caching reduces redundant loads

## Database Management (v1.3.0)

### Pristine Reset
Reset database to clean state for testing:
```bash
# With backup
python api/database_setup.py reset

# Without backup (CI/CD)
python api/database_setup.py reset --no-backup
```

### Configuration Storage
All configs now stored in database, not files:
```python
from twin.config_manager import ConfigurationManager
manager = ConfigurationManager()
# Configs automatically stored in simulation_configs table
```

### Schema Management
```python
from twin.schema_manager import SchemaManager
manager = SchemaManager()
results = manager.verify_schema()  # Validate database integrity
```

See [Database Integration Guide](docs/DATABASE_INTEGRATION.md) for complete details.

## Testing

Run tests with:
```bash
# Unit tests
pytest tests/test_twin_integration.py
pytest tests/test_complete_workflow.py

# Integration tests (NEW)
python twin/test_integration.py
```

## Dependencies

- numpy: Numerical computations
- pandas: Data manipulation
- scipy: Optimization algorithms
- pyyaml: Configuration parsing
- sqlalchemy: Database ORM
- fastapi: API framework

## Future Enhancements

- [ ] Real-time simulation updates via WebSocket
- [ ] Machine learning for parameter tuning
- [ ] Distributed simulation for larger scenarios
- [ ] Advanced visualization dashboard
- [ ] Integration with external MES systems