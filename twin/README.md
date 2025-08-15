# Virtual Twin Manufacturing Intelligence Platform

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Database Management](#database-management)
- [Core Workflow](#core-workflow)
- [Module Details](#module-details)
- [Database Storage Structure](#database-storage-structure)
- [Configuration](#configuration)
- [API Integration](#api-integration)
- [Quick Start Examples](#quick-start-examples)

## Overview

The Virtual Twin is a manufacturing digital twin system that enables:
- **Predictive Simulation**: Test "what-if" scenarios with different operational parameters
- **Multi-Objective Optimization**: Find optimal parameter configurations using evolutionary algorithms
- **Intelligent Recommendations**: Get actionable insights for specific business objectives
- **Financial Impact Analysis**: Calculate ROI and cost implications of changes
- **Real-time State Tracking**: Monitor and track the virtual twin's state over time

### Key Concepts

**Digital Twin**: A virtual replica of the manufacturing system that mirrors real production behavior and enables predictive analytics.

**Actionable Parameters**: Five key tunable parameters that affect manufacturing performance:
1. `micro_stop_probability` (0.3-1.5): Equipment reliability multiplier
2. `performance_factor` (0.7-1.3): Operational excellence multiplier
3. `scrap_multiplier` (0.5-1.5): Quality control effectiveness
4. `material_reliability` (0.5-1.2): Supply chain reliability
5. `cascade_sensitivity` (0.5-2.0): Line coupling effectiveness

**Scaling Approach**: All parameters are multipliers where 1.0 = baseline production performance.

## Architecture

```
Virtual Twin System Architecture
================================

┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│         (Claude Code / API / Direct Python Access)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TWIN MODULE LAYERS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           ANALYSIS & OPTIMIZATION LAYER             │  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────────┐           │  │
│  │  │Optimization  │  │ Recommendation   │           │  │
│  │  │Engine        │  │ Engine           │           │  │
│  │  │(scipy DE)    │  │ (pymoo NSGA-II)  │           │  │
│  │  └──────────────┘  └──────────────────┘           │  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────────┐           │  │
│  │  │Cost Impact   │  │ Line Coupling    │           │  │
│  │  │Calculator    │  │ Model            │           │  │
│  │  │(PyMC Bayes)  │  │ (Cascade sim)    │           │  │
│  │  └──────────────┘  └──────────────────┘           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              SIMULATION CORE LAYER                  │  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────────┐           │  │
│  │  │Simulation    │  │ Actionable       │           │  │
│  │  │Runner        │  │ Parameters       │           │  │
│  │  └──────────────┘  └──────────────────┘           │  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────────┐           │  │
│  │  │Twin State    │  │ Config           │           │  │
│  │  │Manager       │  │ Transformer      │           │  │
│  │  └──────────────┘  └──────────────────┘           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │             DATA GENERATION LAYER                   │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────┐          │  │
│  │  │         Generator Module              │          │  │
│  │  │   (Synthetic MES Data Generation)     │          │  │
│  │  └──────────────────────────────────────┘          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            INFRASTRUCTURE LAYER                     │  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────────┐           │  │
│  │  │Config        │  │ Schema           │           │  │
│  │  │Manager       │  │ Manager          │           │  │
│  │  └──────────────┘  └──────────────────┘           │  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────────┐           │  │
│  │  │Config        │  │ Sync Health      │           │  │
│  │  │Loader        │  │ Monitor          │           │  │
│  │  └──────────────┘  └──────────────────┘           │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                           │
│                  (SQLite: mes_database.db)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Historical Data        │  Twin Operations Data            │
│  ─────────────          │  ──────────────────              │
│  • mes_data             │  • simulation_data               │
│  • equipment_metadata   │  • twin_runs                     │
│  • product_master       │  • parameter_history             │
│  • downtime_reasons     │  • optimization_results          │
│                         │  • recommendations               │
│                         │  • twin_state                    │
│                         │  • simulation_configs            │
│                         │  • confidence_tracking           │
│                         │  • kpi_results                  │
└─────────────────────────────────────────────────────────────┘
```

## Database Management

### 1. Pristine Reset (Complete Rebuild)

Reset the database to a completely clean state:

```bash
# Reset with backup (recommended)
python api/database_setup.py reset

# Reset without backup (for CI/CD)
python api/database_setup.py reset --no-backup
```

**What happens during reset:**
1. Creates backup of current database (unless --no-backup)
2. Drops ALL tables (complete cleanup)
3. Recreates schema from ontology definitions
4. Initializes equipment metadata
5. Clears file-based configs from `twin/configs/`
6. Resets query logs in `learning_history/`

### 2. Initialize with Baseline Data

After reset, populate with manufacturing data:

```bash
# Initialize fresh database with sample data
python api/database_setup.py init
```

Or programmatically:

```python
from twin import SimulationRunner

# This will generate baseline MES data
runner = SimulationRunner()
baseline = runner.create_baseline(duration_days=30)
```

### 3. Database Verification

Check database integrity:

```bash
# Basic verification
python api/database_setup.py verify

# Detailed verification with schema validation
python api/database_setup.py verify --detailed
```

## Core Workflow

### Typical Usage Flow

```
1. Reset/Initialize Database
        ↓
2. Generate Baseline Data
        ↓
3. Run Baseline Simulation
        ↓
4. Optimize Parameters
        ↓
5. Get Recommendations
        ↓
6. Run What-If Scenarios
        ↓
7. Calculate Financial Impact
        ↓
8. Track State Changes
```

### Detailed Workflow Example

```python
import sys
sys.path.insert(0, '/path/to/virtual-ontology')
from twin import SimulationRunner, ActionableParameters, RecommendationEngine

# Step 1: Initialize and create baseline
runner = SimulationRunner(verbose=False)
baseline = runner.create_baseline(duration_days=7, seed=42)
print(f"Baseline OEE: {baseline.kpi_summary['mean_oee']:.1f}%")

# Step 2: Run optimization for specific objective
engine = RecommendationEngine()
result = engine.recommend_for_scenario("maximize_oee")

# Step 3: Apply recommended parameters
params = ActionableParameters()
for param, value in result['recommended_parameters'].items():
    params.set_value(param, value)

# Step 4: Run simulation with optimized parameters
optimized = runner.run_simulation(
    parameters=params,
    parent_run_id=baseline.run_id,
    duration_days=7,
    notes="Optimized for maximum OEE"
)

# Step 5: Compare results
improvement = optimized.kpi_summary['mean_oee'] - baseline.kpi_summary['mean_oee']
print(f"OEE Improvement: {improvement:.1f} percentage points")
```

## Module Details

### SimulationRunner
**Purpose**: Execute simulations with specified parameters

```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)
params = ActionableParameters()
params.set_value("micro_stop_probability", 0.8)  # 20% improvement

result = runner.run_simulation(
    parameters=params,
    duration_days=7,
    seed=42,
    notes="Testing maintenance improvements"
)
```

**Key Methods**:
- `create_baseline()`: Generate baseline simulation
- `run_simulation()`: Execute simulation with parameters
- `run_monte_carlo_simulation()`: Uncertainty analysis
- `compare_runs()`: Compare two simulation runs

### OptimizationEngine
**Purpose**: Single/multi-objective optimization using differential evolution

```python
from twin import OptimizationEngine, ActionableParameters

optimizer = OptimizationEngine(verbose=False)
params = ActionableParameters()

# Single objective
result = optimizer.optimize_single_objective(
    parameters=params,
    objective="oee",
    direction="maximize",
    population_size=20,
    generations=50
)

# Multi-objective
result = optimizer.optimize_multi_objective(
    parameters=params,
    objectives=[
        {"name": "oee", "direction": "maximize", "weight": 0.6},
        {"name": "energy", "direction": "minimize", "weight": 0.4}
    ]
)
```

### RecommendationEngine
**Purpose**: Generate scenario-based recommendations using NSGA-II

```python
from twin import RecommendationEngine

engine = RecommendationEngine()

# Get recommendations for specific scenario
result = engine.recommend_for_scenario("maximize_oee")

# Or with custom scenario
result = engine.recommend_for_scenario(
    "balance energy and throughput",
    population_size=50,
    generations=100
)

# Access results
params = result['recommended_parameters']
improvements = result['expected_improvements']
implementation = result['implementation_steps']
```

**Supported Scenarios**:
- `maximize_oee`: Overall equipment effectiveness
- `minimize_energy`: Energy consumption
- `maximize_quality`: Product quality
- `maximize_throughput`: Production output
- `minimize_cost`: Operational costs

### TwinState
**Purpose**: Track and manage the virtual twin's state over time

```python
from twin import TwinStateManager

state_manager = TwinStateManager()

# Get current state
current_state = state_manager.get_current_state()

# Track parameter changes
state_manager.track_parameter_change(
    parameter_name="micro_stop_probability",
    old_value=1.0,
    new_value=0.8,
    run_id="sim-123",
    impact_assessment={"oee_change": 5.2}
)

# Get improvement trends
trends = state_manager.get_improvement_trends(
    metric="oee",
    last_n_runs=10
)
```

## Database Storage Structure

### Core MES Tables (Historical Data)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `mes_data` | Production data | timestamp, line, equipment, oee, units_produced |
| `equipment_metadata` | Equipment definitions | equipment_id, type, line, capacity |
| `product_master` | Product specifications | sku, name, target_rate, cost |
| `downtime_reasons` | Downtime categorization | reason_code, description, category |

### Twin Operation Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `simulation_data` | Simulation results | run_id, timestamp, kpi values |
| `twin_runs` | Run metadata | run_id, parent_run_id, parameters, created_at |
| `parameter_history` | Parameter changes | parameter, old_value, new_value, timestamp |
| `optimization_results` | Optimization outcomes | optimization_id, objectives, best_parameters |
| `recommendations` | Generated recommendations | recommendation_id, scenario, parameters, expected_impact |
| `twin_state` | State snapshots | state_id, timestamp, parameters, kpis |
| `simulation_configs` | Config storage | config_id, run_id, config_json, hash |
| `confidence_tracking` | Statistical validation | run_id, confidence_level, intervals |
| `kpi_results` | KPI calculations | run_id, kpi_name, value, timestamp |

### Data Relationships

```
twin_runs (parent)
    ├── simulation_data (1:many)
    ├── parameter_history (1:many)
    ├── kpi_results (1:many)
    └── simulation_configs (1:1)

optimization_results (parent)
    └── recommendations (1:many)

twin_state (independent snapshots)
    └── tracks all parameter values at points in time
```

## Configuration

### Two-File Configuration System

1. **`config/generator.yaml`** - Data generation parameters
   - Actionable parameters definitions
   - Equipment specifications
   - Product definitions
   - Anomaly patterns

2. **`config/system.yaml`** - System operational settings
   - Database configuration
   - Module-specific settings
   - Optimization parameters
   - Visualization settings

### Loading Configuration

```python
from twin.config_loader import ConfigLoader

# Load configuration
config = ConfigLoader()

# Access specific values
db_path = config.get("database.path")
param_config = config.get_parameter_config("micro_stop_probability")
module_config = config.get_module_config("optimization_engine")
```

## API Integration

### Query Twin Tables via API

```bash
# Using curl
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM twin_runs ORDER BY created_at DESC LIMIT 5"}'

# Using query-log.sh for logged queries
echo '{"sql": "SELECT * FROM optimization_results WHERE objective = \"oee\""}' | \
./query-log.sh POST /query -d @-
```

### API Status Check

```bash
./api.sh status

# Returns:
# - Database size and statistics
# - Table row counts
# - Data freshness metrics
# - Twin module statistics
```

## Quick Start Examples

### Example 1: Basic What-If Analysis

```python
from twin import SimulationRunner, ActionableParameters

# Initialize
runner = SimulationRunner(verbose=False)
params = ActionableParameters()

# Adjust parameters (as multipliers of baseline)
params.micro_stop_probability = 0.8  # 20% reduction in micro-stops
params.performance_factor = 1.1       # 10% performance improvement

# Run simulation
result = runner.run_simulation(params, duration_days=7)

# View results
print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")
print(f"Total Good Units: {result.kpi_summary['total_good_units']:,}")
```

### Example 2: Find Optimal Parameters

```python
from twin import RecommendationEngine

engine = RecommendationEngine()

# Get optimal parameters for OEE
result = engine.recommend_for_scenario("maximize_oee")

print("Recommended Changes:")
for param, value in result['recommended_parameters'].items():
    print(f"  Set {param} to {value:.3f}")

print(f"\nExpected OEE Improvement: {result['expected_improvements']['oee_improvement']*100:.1f}%")
```

### Example 3: Monte Carlo Uncertainty Analysis

```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)
params = ActionableParameters()

# Define uncertainty ranges
uncertainty = {
    "micro_stop_probability": (-0.1, 0.1),  # ±10% variation
    "performance_factor": (-0.05, 0.05),    # ±5% variation
}

# Run Monte Carlo
mc_results = runner.run_monte_carlo_simulation(
    parameters=params,
    uncertainty_ranges=uncertainty,
    n_simulations=50,
    duration_days=7
)

# View statistics
print(f"Mean OEE: {mc_results['statistics']['mean_oee_mean']:.1f}%")
print(f"95% CI: {mc_results['confidence_intervals']['mean_oee']}")
```

### Example 4: Financial Impact Calculation

```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)

# Run baseline and improved scenarios
baseline = runner.create_baseline(duration_days=7)
params = ActionableParameters()
params.micro_stop_probability = 0.7  # 30% improvement

improved = runner.run_simulation(params, duration_days=7)

# Calculate financial impact
daily_revenue = 500000  # Example daily revenue
oee_improvement = improved.kpi_summary['mean_oee'] - baseline.kpi_summary['mean_oee']
annual_impact = daily_revenue * 365 * (oee_improvement / 100)

print(f"OEE Improvement: {oee_improvement:.1f} percentage points")
print(f"Annual Revenue Impact: ${annual_impact:,.0f}")
```

## Advanced Features

### State Persistence
The twin maintains state across sessions through the database, allowing for:
- Continuous improvement tracking
- Historical trend analysis
- Change impact assessment

### Lineage Tracking
All simulations maintain parent-child relationships, enabling:
- Traceability of parameter changes
- Comparison across generations
- Rollback capabilities

### Configuration Management
Configurations are stored in the database with:
- Content-based deduplication
- Version tracking
- Audit trail

## Troubleshooting

### Common Issues

**Database locked error**
```bash
# Kill any hanging processes
pkill -f "python.*database_setup"
# Reset database
python api/database_setup.py reset
```

**Import errors**
```python
# Always set Python path
import sys
sys.path.insert(0, '/path/to/virtual-ontology')
```

**No data after reset**
```bash
# Initialize with sample data
python api/database_setup.py init
```

## Best Practices

1. **Always reset to pristine** before major testing
2. **Use seeds** for reproducible simulations
3. **Track lineage** with parent_run_id
4. **Store notes** with each simulation for context
5. **Use verbose=False** in production for performance
6. **Batch simulations** using ThreadPoolExecutor for parallel runs
7. **Monitor sync health** for data freshness

## Further Documentation

- **API Reference**: See Sphinx docs at `docs/build/html/index.html`
- **Configuration Guide**: `docs/source/guides/configuration.rst`
- **Database Integration**: `docs/DATABASE_INTEGRATION.md`
- **System Architecture**: `/SYSTEM_ARCHITECTURE.md`

## Support

For issues or questions:
1. Check the integration tests: `python twin/test_integration.py`
2. Verify database: `python api/database_setup.py verify --detailed`
3. Review logs: `tail -f logs/api.log`