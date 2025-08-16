# Virtual Twin System Architecture

## Overview

The Virtual Twin system is an LLM-orchestrated manufacturing intelligence platform that combines historical data analysis with predictive simulation and optimization. It follows the "Natural Language REPL" pattern where an LLM (Claude Code) acts as the intelligent interface between users and the system's Python modules.

## Core Architecture Principles

1. **LLM as Primary Interface**: The system is designed for LLM orchestration, not traditional UI
2. **Python-First Implementation**: All capabilities exposed as Python modules
3. **Separation of Concerns**: Analysis (read-only) vs Operations (read-write)
4. **Complete Traceability**: All operations logged for reproducibility
5. **Virtual Ontology Pattern**: Natural language → SQL/Python → Results → Insights
6. **Layered Ontology Architecture**: Twin extends base MES without replacement
7. **Virtual Sensor Abstraction**: Derive observations from production data, not synthetic generation

## System Layers

```
┌─────────────────────────────────────────────────────────┐
│                    User (Natural Language)              │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 LLM (Claude Code)                       │
│         Natural Language REPL & Orchestrator            │
└─────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│   Historical Analysis    │   │    Twin Operations       │
│      (Read-Only)         │   │     (Read-Write)         │
├──────────────────────────┤   ├──────────────────────────┤
│   query-log.sh           │   │   Python Modules:        │
│   ↓                      │   │   - SimulationRunner     │
│   API Server (api.sh)    │   │   - VirtualSensors (6)   │
│   ↓                      │   │   - OptimizationEngine   │
│   SELECT only            │   │   - RecommendationEngine │
└──────────────────────────┘   └──────────────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 SQLite Database                         │
│               data/mes_database.db                      │
│          MES Tables + Twin Tables + Sensor Data         │
└─────────────────────────────────────────────────────────┘
```

## Ontology Architecture

### Layered Design

The system uses a layered ontology architecture where the Virtual Twin layer extends (not replaces) the base MES ontology:

```
┌─────────────────────────────────────┐
│     Virtual Twin Layer              │
│  - VirtualSensors (6 types)         │
│  - SimulationRuns                   │
│  - ActionableParameters (5 levers)  │
│  - TwinState & Sync                 │
└─────────────────────────────────────┘
              ↓ extends/observes
┌─────────────────────────────────────┐
│     Base MES Layer                  │
│  - Equipment (Filler, Packer, etc.) │
│  - Production Data                  │
│  - Downtime Events                  │
│  - Products/SKUs                    │
└─────────────────────────────────────┘
              ↓ describes
┌─────────────────────────────────────┐
│   Physical Manufacturing Data       │
└─────────────────────────────────────┘
```

### Virtual Sensor Layer

Virtual sensors observe and derive metrics from MES production data rather than generating synthetic readings:

1. **PowerMeterSensor**: Derives energy consumption from production patterns (confidence: 0.95)
2. **ThroughputSensor**: Observes production rate vs target efficiency (confidence: 1.0)
3. **DefectRateSensor**: Observes quality through scrap patterns (confidence: 1.0)
4. **BottleneckDetector**: Identifies production bottlenecks from OEE patterns (confidence: 0.8)
5. **LineCouplingMonitor**: Monitors equipment coupling and cascade effects (confidence: 0.9)
6. **DowntimePatternSensor**: Analyzes downtime patterns and trends (confidence: 1.0)

Confidence levels are configurable in `twin/config/system.yaml` under `virtual_sensors.confidence_levels`.

### Three-Layer Data Architecture

```
Raw Layer (Facts) → Virtual Layer (Observations) → Analytics Layer (Insights)
    mes_data     →    sensor_data              →    kpi_results
```

## Data Flow Patterns

### Pattern 1: Historical Analysis
```
User: "What was OEE last week?"
    ↓
LLM interprets query
    ↓
Creates SQL: SELECT AVG(oee_score) FROM mes_data WHERE...
    ↓
Executes via query-log.sh
    ↓
API server queries database (read-only)
    ↓
Results logged to query_logs.json
    ↓
LLM interprets results for user
```

### Pattern 2: Predictive Simulation
```
User: "What if we reduce micro-stops by 30%?"
    ↓
LLM interprets as simulation request
    ↓
Python: SimulationRunner with adjusted parameters
    ↓
Direct SQLite connection (read-write)
    ↓
Generates synthetic data → simulation_data table
    ↓
Stores run metadata → twin_runs table
    ↓
LLM explains impact to user
```

### Pattern 3: Optimization
```
User: "Find the best balance between energy and throughput"
    ↓
LLM interprets as multi-objective optimization
    ↓
Python: RecommendationEngine (pymoo NSGA-II algorithm)
    ↓
Runs multiple simulations internally
    ↓
Stores Pareto front → recommendations table
    ↓
LLM explains trade-offs to user
```

## Module Architecture

### Core Orchestration
- **`twin/__init__.py`**: Module exports and public API (v1.2.0)
  - Core: SimulationRunner, ActionableParameters, TwinStateManager
  - Analysis: OptimizationEngine, RecommendationEngine, CostImpactCalculator
  - Support: SyncHealthMonitor, LineCoupling
  - Generator: Integrated data generator module
  - **Enhanced with pymoo and PyMC libraries for robust scientific computing**

### Simulation & Prediction
- **`SimulationRunner`**: Manages digital twin simulations
  - Generates synthetic manufacturing data with custom configurations
  - Integrates virtual sensors to derive observations from simulated data
  - Tracks full provenance (twin_runs table)
  - **Enhanced Monte Carlo wrapper** with parallel simulation support
  - Batch uncertainty analysis with statistical aggregation
  - Parameter sensitivity analysis
  - Uses integrated generator module (no external dependencies)

### Optimization Modules
- **`OptimizationEngine`**: scipy-based differential evolution
  - Single-objective or weighted multi-objective
  - Fast convergence for feasibility checks
  - Good for constrained problems

- **`RecommendationEngine`**: **pymoo-based NSGA-II implementation**
  - True multi-objective optimization with pymoo's proven algorithms
  - Finds Pareto-optimal solutions with hypervolume indicators
  - Advanced genetic operators (SBX crossover, PM mutation)
  - Constraint handling and feasibility checking
  - Visualization of Pareto fronts
  - Includes scenario mapping and confidence scoring
  - Stores recommendations with expected improvements

### Analysis & Intelligence
- **`CostImpactCalculator`**: **PyMC-based Bayesian financial analysis**
  - Bayesian Monte Carlo ROI calculations using MCMC sampling
  - Proper uncertainty quantification with credible intervals
  - Probabilistic modeling of KPI improvements
  - Advanced diagnostics (R-hat, ESS) for convergence
  - Payback period estimation with confidence bounds

### Parameters & State
- **`ActionableParameters`**: 5 tunable parameters (scaling approach, 1.0 = baseline)
  1. `micro_stop_probability` (0.3-1.5): Maintenance effectiveness multiplier
  2. `performance_factor` (0.7-1.3): Operational excellence multiplier
  3. `scrap_multiplier` (0.5-1.5): Quality control effectiveness
  4. `material_reliability` (0.5-1.2): Supply chain reliability multiplier
  5. `cascade_sensitivity` (0.5-2.0): Line decoupling effectiveness

### Virtual Sensors
- **`VirtualSensorObserver`**: Orchestrates all virtual sensors
  - Processes production data to generate sensor observations
  - Stores observations in sensor_data table
  - Configurable confidence levels per sensor type
  - No synthetic data generation - only derives from existing data

- **`TwinStateManager`**: Tracks current configuration
  - Active parameters
  - Baseline references
  - Applied recommendations

### Configuration Management
- **`ConfigTransformer`**: Transforms parameters to generator configurations
  - Maps ActionableParameters to mes_data_config.json structure
  - Applies parameter changes to anomaly injection patterns
  - Scales equipment efficiency and quality rates
  
- **`ConfigValidator`**: Validates configurations before simulation
  - Ensures parameter changes are correctly applied
  - Validates probability ranges (0.0-1.0)
  - Checks scrap rates and efficiency bounds
  - Provides detailed error and warning reports

## Database Access Patterns

### Three Access Methods

1. **API + query-log.sh** (Historical Analysis)
   - Read-only access to `mes_data`
   - All queries logged to `query_logs.json`
   - Goes through API server for control
   - Used for: Exploratory analysis, baseline metrics

2. **Direct SQLite** (Twin Operations)
   ```python
   with sqlite3.connect(self.db_path) as conn:
       conn.execute("INSERT INTO twin_runs ...")
   ```
   - Full read-write access
   - Direct connection, no API overhead
   - Transaction support
   - Used for: Simulations, optimization, state management

3. **SQLAlchemy + Pandas** (Bulk Operations)
   ```python
   engine = create_engine(f"sqlite:///{self.db_path}")
   df = pd.read_sql_query("SELECT * FROM ...", engine)
   ```
   - Efficient for large datasets
   - DataFrame operations
   - Used for: KPI calculations, data analysis

### Access Matrix by Component

| Component | Access Method | Tables | Operations |
|-----------|--------------|---------|------------|
| query-log.sh | API Server | mes_data | SELECT only |
| SimulationRunner | Direct SQLite | twin_runs, simulation_data, parameter_history | All |
| OptimizationEngine | Via SimulationRunner | optimization_results | All |
| RecommendationEngine | Direct SQLite | recommendations, twin_runs | All |
| CostImpactCalculator | Direct SQLite | mes_data, twin_runs | SELECT only |
| TwinStateManager | Direct SQLite | twin_state | All |

## LLM Integration

### Decision Flow
```
User Query
    ↓
LLM interprets intent:
    ├── "What is..." → SQL query via query-log.sh
    ├── "What if..." → SimulationRunner
    ├── "Optimize..." → OptimizationEngine or RecommendationEngine
    ├── "ROI of..." → CostImpactCalculator
    └── "Why..." → SQL analysis + root cause logic
    ↓
Execute appropriate module(s)
    ↓
Interpret results in business terms
```

### Module Selection Logic

The LLM chooses modules based on:

1. **Intent Detection**: Keywords and patterns in user query
2. **Context**: Current state, available data, past operations
3. **Objectives**: Single vs multi-objective needs
4. **Constraints**: Hard limits vs soft preferences

### Natural Language Patterns

| User Says | LLM Uses | Why |
|-----------|----------|-----|
| "What's current OEE?" | query-log.sh | Historical data query |
| "What if we reduce X?" | SimulationRunner | Predictive simulation |
| "Find the best..." | OptimizationEngine | Single objective |
| "Balance A and B" | RecommendationEngine | Multi-objective |
| "What's the ROI?" | CostImpactCalculator | Financial analysis |
| "Why is X happening?" | SQL analysis | Root cause analysis |

## File Structure

```
virtual-ontology/
├── api.sh                    # SQL API server management
├── query-log.sh             # SQL query execution & logging
├── SYSTEM_PROMPT.md         # Unified LLM instructions
├── ontology/                   # Ontology specifications
│   ├── ontology_spec.yaml      # MES business concepts
│   ├── database_schema.yaml    # MES data structure
│   ├── twin_ontology_spec.yaml # Twin layer concepts
│   ├── twin_database_schema.yaml # Twin data structure
│   └── README.md               # Ontology documentation
├── data/
│   ├── mes_database.db         # SQLite database (18 tables)
│   ├── mes_data_sample.csv     # Sample data for import
│   ├── mes_data_with_kpis.csv  # Data with calculated KPIs
│   ├── baseline_config.json    # Base configuration
│   └── simulation_configs/     # Archived config files
│       └── archive/            # Historical config JSONs
├── twin/
│   ├── __init__.py              # Module exports and API (v1.3.0)
│   ├── generator.py             # Integrated data generator
│   ├── virtual_sensors.py       # Virtual sensor layer (6 sensor types)
│   ├── simulation_runner.py     # Digital twin simulation + virtual sensors
│   ├── optimization_engine.py   # scipy-based optimization
│   ├── recommendation_engine.py # pymoo NSGA-II multi-objective
│   ├── config_loader.py         # Multi-config loader
│   ├── config_manager.py        # Configuration storage manager
│   ├── config_transformer.py    # Parameter to config transformer
│   ├── config_validator.py      # Configuration validation layer
│   ├── actionable_parameters.py # Parameter definitions
│   ├── cost_impact_calculator.py # PyMC Bayesian financial analysis
│   ├── twin_state.py            # State management
│   ├── line_coupling_model.py   # Production line interactions
│   ├── sync_health.py          # Synchronization monitoring
│   ├── config/                  # Configuration files (NEW)
│   │   ├── generator.yaml      # Generator configuration
│   │   ├── system.yaml         # System configuration
│   │   └── defaults.yaml       # Legacy config (deprecated)
│   ├── API.md                  # Module API documentation
│   ├── README.md               # Module overview
│   ├── docs/                   # Twin documentation
│   │   ├── PATTERNS_REFERENCE.md # Error-free code patterns
│   │   └── EXAMPLES.md         # Usage examples
│   └── visualization/          # Plotting utilities
├── api/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database connection management
│   ├── models.py               # SQLModel definitions
│   ├── database_endpoints.py   # Database management endpoints
│   ├── simulation_endpoints.py # Simulation API endpoints
│   └── database_setup.py       # Database initialization
├── scripts/                    # One-time setup scripts (completed)
│   ├── init_twin_database.py   # Initialize twin tables
│   └── migrate_configs.py      # Config migration script
├── SYSTEM_ARCHITECTURE.md      # This document (root directory)
├── DATABASE_AND_API.md         # Database schema and API endpoints (root directory)
├── templates/                   # Ontology and prompt templates
│   ├── ontology_spec_template.yaml
│   └── prompt_engineering_template.md
├── reference/                   # Archived documentation
│   ├── sys_prompt.md           # Original system prompt
│   └── twin_sys_prompt.md      # Twin-specific prompt
├── learning_history/            # System learning and memory
│   └── query_logs.json         # SQL query history
└── logs/
    └── api.log                 # API server logs
```

## Logging & Traceability

### Three Log Types

1. **learning_history/query_logs.json**: SQL queries and responses
   - Every query through query-log.sh
   - Full request/response captured
   - Enables query pattern learning

2. **Database audit trails**: Permanent operation records
   - `twin_runs`: All simulation metadata and results
   - `parameter_history`: Complete parameter change audit
   - `simulation_configs`: Deduplicated configuration storage

3. **API logs**: Server operation logs
   - `logs/api.log`: FastAPI server logs
   - Request/response tracking
   - Error logging and debugging

## System Constraints & Limitations

### Technical Constraints
- SQLite database (no concurrent writes)
- API limited to SELECT queries only
- No real-time data streaming
- Single-machine deployment

### Design Decisions
- No traditional UI (LLM is the interface)
- Python-first (no REST API for twin operations)
- Synchronous processing (no job queues)
- File-based logging (not centralized)

## Evolution Path

### Current State (v1.3.0 - Virtual Sensor Layer)
- LLM-orchestrated Python modules
- **Virtual sensor abstraction** - 6 sensor types deriving observations from production data
- **pymoo** for robust multi-objective optimization (NSGA-II, hypervolume, IGD)
- **PyMC** for Bayesian probabilistic modeling and MCMC sampling
- Enhanced Monte Carlo simulation with parallel execution support
- Integrated data generator as part of twin module
- Dual configuration architecture (generator.yaml, system.yaml)
- SQLite database with api.sh as primary interface
- Energy no longer in raw data tables - derived by virtual sensors
- Single-machine deployment

### Recent Enhancements (v1.3.0)
- ✅ **Virtual sensor layer** - 6 sensor types observe and derive metrics from production data
- ✅ **Removed energy from raw data** - Energy now derived by PowerMeterSensor
- ✅ **Configurable confidence levels** - Per-sensor confidence in system.yaml
- ✅ **Three-layer data architecture** - Raw facts → Virtual observations → Analytics insights
- ✅ **Database migration support** - Scripts to remove energy columns from existing databases

### Previous Enhancements (v1.2.0)
- ✅ **Integrated data generator into twin module** - No more external script dependency
- ✅ **Separated configurations** - generator.yaml for data generation, system.yaml for twin settings
- ✅ **Scaling parameter approach** - All parameters use 1.0 = baseline for intuitive tuning

### Previous Enhancements (v1.1.0)
- ✅ Replaced custom NSGA-II with pymoo's proven implementation
- ✅ Integrated PyMC for Bayesian uncertainty quantification in ROI
- ✅ Added parallel Monte Carlo simulation capability
- ✅ Enhanced parameter sensitivity analysis
- ✅ Improved convergence diagnostics (R-hat, ESS)

### Potential Future Enhancements
- Read from twin_operations.jsonl for learning
- Time-series database for simulation data
- Distributed simulation runners
- Real-time data integration
- GPU acceleration for pymoo optimization
- Advanced PyMC models with hierarchical priors

## Key Insights

1. **LLM-Centric Design**: The system assumes Claude Code as orchestrator, not human users
2. **Separation of Analysis and Operations**: Different access patterns for different needs
3. **Traceability Over Performance**: Every operation logged for audit and learning
4. **Python Over APIs**: Direct module access for twin operations, REST for queries
5. **Pragmatic Simplicity**: SQLite and files instead of complex infrastructure
6. **Ontology-Driven**: YAML ontologies define business concepts and data structures
7. **Configuration as Data**: Configs stored in database, not files, with deduplication
8. **Scientific Computing Libraries**: pymoo and PyMC provide proven algorithms over custom implementations
9. **Bayesian Approach**: Proper uncertainty quantification through probabilistic modeling

## Success Metrics

### POC Success Criteria
The Virtual Twin POC succeeds if it can demonstrate these core capabilities:

- ✅ **Answer**: "What's the financial impact of reducing micro-stops by 30%?"
- ✅ **Recommend**: "Best parameters for maximizing OEE" with Pareto trade-offs (pymoo NSGA-II)
- ✅ **Explain**: "Why Line 2 outperforms Line 1"
- ✅ **Validate**: Show reproducible results with Bayesian credible intervals (PyMC)
- ✅ **Demonstrate**: All interactions through conversational natural language
- ✅ **Compute**: Bayesian ROI via PyMC MCMC (e.g., "$45K with 95% CI: $40K-$50K")

### Operational Metrics
To measure the effectiveness of the Virtual Twin system, track these KPIs:

- **Query Success Rate**: Target >90% successful query executions
- **Simulation Accuracy**: Compare predictions to actual outcomes (target <10% deviation)
- **Recommendation Adoption**: Percentage of recommendations implemented (target >60%)
- **Parameter Optimization**: Improvement in KPIs after optimization (target >5% OEE gain)

### Business Impact
- **Time to Insight**: Reduce analysis time from hours to minutes (target <5 min)
- **ROI Achievement**: Track actual vs predicted savings (target >80% accuracy)
- **Downtime Reduction**: Measure decrease in unplanned downtime (target -20%)
- **Energy Efficiency**: Track energy consumption improvements (target -15%)

### System Performance
- **Response Time**: API query response <2 seconds
- **Simulation Speed**: Complete simulation in <30 seconds
- **Database Growth**: Monitor storage efficiency (<100MB/month)
- **Uptime**: System availability >99%

### User Adoption
- **Daily Active Queries**: Number of unique queries per day
- **Feature Utilization**: Usage of simulation vs optimization vs recommendations
- **Learning Curve**: Time for new users to get productive (target <1 week)
- **User Satisfaction**: Feedback on insights quality and relevance

### Workflow Success Metrics
- **Discovery**: Baseline metrics established within 3-5 queries
- **Simulation**: What-if scenarios run for each major finding
- **Optimization**: Pareto front generated for multi-objective goals
- **Impact**: Financial ROI calculated for all recommendations
- **Action**: Specific parameter changes with expected outcomes

## References

- [Database and API Documentation](DATABASE_AND_API.md) - Database schema and API endpoints
- [Usage Examples](twin/docs/EXAMPLES.md) - Example conversations and patterns
- [System Prompt](SYSTEM_PROMPT.md) - Unified LLM instructions for full workflow
- [Twin Module Documentation](../twin/README.md) - Twin module capabilities