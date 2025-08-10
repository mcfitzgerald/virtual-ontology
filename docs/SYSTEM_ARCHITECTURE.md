# Virtual Twin System Architecture

## Overview

The Virtual Twin system is an LLM-orchestrated manufacturing intelligence platform that combines historical data analysis with predictive simulation and optimization. It follows the "Natural Language REPL" pattern where an LLM (Claude Code) acts as the intelligent interface between users and the system's Python modules.

## Core Architecture Principles

1. **LLM as Primary Interface**: The system is designed for LLM orchestration, not traditional UI
2. **Python-First Implementation**: All capabilities exposed as Python modules
3. **Separation of Concerns**: Analysis (read-only) vs Operations (read-write)
4. **Complete Traceability**: All operations logged for reproducibility
5. **Virtual Ontology Pattern**: Natural language → SQL/Python → Results → Insights

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
│   API Server (api.sh)    │   │   - OptimizationEngine   │
│   ↓                      │   │   - RecommendationEngine │
│   SELECT only            │   │   - CostImpactCalculator │
└──────────────────────────┘   └──────────────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 SQLite Database                         │
│               data/mes_database.db                      │
│                   (17 tables)                           │
└─────────────────────────────────────────────────────────┘
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
Python: RecommendationEngine (NSGA-II algorithm)
    ↓
Runs multiple simulations internally
    ↓
Stores Pareto front → recommendations table
    ↓
LLM explains trade-offs to user
```

## Module Architecture

### Core Orchestration
- **`twin.py`**: Main `VirtualTwin` class that unifies all modules
  - Provides high-level methods: `simulate()`, `optimize()`, `calculate_roi()`
  - Handles workflow: baseline → operation → logging
  - Logs operations to `twin_operations.jsonl` (currently write-only)

### Simulation & Prediction
- **`SimulationRunner`**: Manages digital twin simulations
  - Generates synthetic manufacturing data
  - Tracks full provenance (twin_runs table)
  - Supports Monte Carlo uncertainty analysis

### Optimization Modules
- **`OptimizationEngine`**: scipy-based differential evolution
  - Single-objective or weighted multi-objective
  - Fast convergence for feasibility checks
  - Good for constrained problems

- **`RecommendationEngine`**: NSGA-II genetic algorithm
  - True multi-objective optimization
  - Finds Pareto-optimal solutions
  - Includes scenario mapping and confidence scoring
  - Stores recommendations with expected improvements

### Analysis & Intelligence
- **`DisambiguationHelper`**: Context provider for NLP
  - Entity identification (lines, equipment, products)
  - Timeframe detection
  - Parameter hint mapping
  - Provides context, doesn't make decisions

- **`CostImpactCalculator`**: Financial analysis
  - Monte Carlo ROI calculations
  - Uncertainty quantification
  - Payback period estimation

### Parameters & State
- **`ActionableParameters`**: 5 tunable parameters
  1. `micro_stop_probability` (0.05-0.5): Equipment reliability
  2. `performance_factor` (0.5-1.0): Operator skill/calibration
  3. `scrap_multiplier` (1.0-5.0): Quality control
  4. `material_reliability` (0.5-1.0): Supply chain quality
  5. `cascade_sensitivity` (0.0-1.0): Failure propagation

- **`TwinStateManager`**: Tracks current configuration
  - Active parameters
  - Baseline references
  - Applied recommendations

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
| DisambiguationHelper | Direct SQLite | mes_data, twin_runs | SELECT only |
| CostImpactCalculator | Direct SQLite | mes_data, twin_runs | SELECT only |
| TwinStateManager | Direct SQLite | twin_state | All |

## LLM Integration

### Decision Flow
```
User Query
    ↓
DisambiguationHelper.get_query_context()
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
| "Why is X happening?" | DisambiguationHelper + SQL | Root cause analysis |

## File Structure

```
virtual-ontology/
├── api.sh                    # SQL API server management
├── query-log.sh             # SQL query execution & logging
├── twin.py                  # Main orchestration class
├── data/
│   ├── mes_database.db      # Single SQLite database (18 tables incl. configs)
│   └── simulation_configs/  # Archived config files
│       └── archive/         # Migrated historical configs
├── twin/
│   ├── simulation_runner.py     # Digital twin simulation
│   ├── optimization_engine.py   # scipy-based optimization
│   ├── recommendation_engine.py # NSGA-II multi-objective
│   ├── config_manager.py        # Configuration storage manager
│   ├── config_transformer.py    # Parameter to config transformer
│   ├── disambiguation.py         # NLP context helper
│   ├── actionable_parameters.py # Parameter definitions
│   ├── cost_impact_calculator.py # Financial analysis
│   ├── twin_state.py            # State management
│   └── visualization/           # Plotting utilities
├── api/
│   ├── database_setup.py       # Database initialization
│   └── setup/                  # Setup modules
│       ├── config.json         # Unified configuration
│       ├── twin_tables.py      # Twin table management
│       └── mes_historical.py   # Historical data generation
├── scripts/
│   └── migrate_configs.py      # Config migration script
├── docs/
│   ├── DATABASE_ARCHITECTURE.md    # Database schema details
│   ├── SYSTEM_ARCHITECTURE.md      # This document
│   └── CONFIGURATION_MANAGEMENT.md # Config management guide
├── learning_history/        # System learning and memory
│   ├── query_logs.json      # SQL query history
│   └── twin_operations.jsonl # Twin operation log (write-only)
└── logs/
    └── api.log              # API server logs
```

## Logging & Traceability

### Three Log Types

1. **learning_history/query_logs.json**: SQL queries and responses
   - Every query through query-log.sh
   - Full request/response captured
   - Enables query pattern learning

2. **learning_history/twin_operations.jsonl**: Twin operations (currently write-only)
   - Simulations, optimizations, ROI calculations
   - Intended for operation replay (not yet implemented)
   - JSON Lines format for streaming

3. **Database tables**: Permanent record
   - `twin_runs`: All simulation metadata
   - `parameter_history`: Parameter evolution
   - `recommendations`: All generated recommendations
   - `sync_health_log`: System health tracking

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

### Current State (v1.0)
- LLM-orchestrated Python modules
- SQLite database
- File-based logging
- Single-machine deployment

### Potential Enhancements
- Read from twin_operations.jsonl for learning
- GraphQL subscriptions for real-time updates
- Time-series database for simulation data
- Distributed simulation runners
- Real-time data integration

## Key Insights

1. **LLM-Centric Design**: The system assumes an LLM orchestrator, not human users
2. **Separation of Analysis and Operations**: Different access patterns for different needs
3. **Traceability Over Performance**: Every operation logged for audit and learning
4. **Python Over APIs**: Direct module access instead of REST endpoints
5. **Pragmatic Simplicity**: SQLite and files instead of complex infrastructure

## References

- [Database Architecture](DATABASE_ARCHITECTURE.md) - Detailed database schema
- [Virtual Twin Implementation Plan](../VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md) - Original design
- [System Prompts](../sys_prompt.md, ../twin_sys_prompt.md) - LLM instructions