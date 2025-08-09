# Virtual Twin API Reference

## Overview

This document provides a complete reference for all APIs in the Virtual Twin system, including Python APIs, GraphQL endpoints, and REST interfaces.

## Python API Reference

### Core Modules

#### `twin.twin_ontology`

##### Class: `VirtualTwin`

Main digital twin orchestrator class.

```python
class VirtualTwin:
    def __init__(self, twin_id: str, description: str = None)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `add_equipment` | `equipment_id: str`<br>`equipment_type: str`<br>`line: str` | `None` | Add equipment to twin |
| `add_sensor` | `sensor_id: str`<br>`observable_property: str`<br>`unit: str`<br>`equipment_id: str` | `None` | Add sensor to equipment |
| `update_state` | `equipment_id: str`<br>`new_state: EquipmentState` | `bool` | Update equipment state |
| `get_current_state` | `equipment_id: str` | `EquipmentState` | Get current equipment state |
| `start_sync` | `interval: int = 60` | `None` | Start real-time sync |
| `stop_sync` | | `None` | Stop real-time sync |
| `get_graph` | | `Graph` | Get RDF graph representation |

##### Class: `EquipmentState`

```python
class EquipmentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    ERROR = "error"
```

##### Class: `SensorObservation`

```python
class SensorObservation:
    def __init__(self, 
                 sensor_id: str,
                 value: float,
                 unit: str,
                 timestamp: datetime,
                 quality: float = 1.0)
```

---

#### `twin.actionable_parameters`

##### Class: `ActionableParameters`

Manages configurable parameters with validation.

```python
class ActionableParameters:
    def __init__(self)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `set_parameter` | `name: str`<br>`value: float` | `bool` | Set parameter value with validation |
| `get_parameter` | `name: str` | `float` | Get current parameter value |
| `get_all_parameters` | | `Dict[str, float]` | Get all parameter values |
| `validate_parameter` | `name: str`<br>`value: float` | `bool` | Validate parameter against constraints |
| `get_impact` | `name: str` | `Dict[str, float]` | Get parameter impact on KPIs |
| `reset_to_defaults` | | `None` | Reset all parameters to defaults |

**Parameter Definitions:**

| Parameter | Range | Default | Unit | Impact |
|-----------|-------|---------|------|--------|
| `micro_stop_probability` | 0.001-0.2 | 0.05 | probability | Availability (-) |
| `performance_factor` | 0.7-1.0 | 0.85 | ratio | Performance (+) |
| `scrap_multiplier` | 0.8-1.2 | 1.0 | multiplier | Quality (-) |
| `material_reliability` | 0.9-0.99 | 0.95 | probability | Availability (+) |
| `energy_cost_per_kwh` | 0.05-0.25 | 0.12 | $/kWh | Cost (-) |
| `labor_cost_per_hour` | 15-50 | 25 | $/hour | Cost (-) |
| `cascade_sensitivity` | 0.1-0.9 | 0.3 | ratio | Cascade effects |

---

#### `twin.simulation_runner`

##### Class: `SimulationRunner`

Executes simulations with provenance tracking.

```python
class SimulationRunner:
    def __init__(self, db_path: str = "data/mes_database.db")
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `run_simulation` | `run_type: RunType`<br>`duration: int`<br>`config: Dict`<br>`**kwargs` | `Dict[str, Any]` | Execute simulation |
| `get_run_results` | `run_id: str` | `Dict[str, Any]` | Retrieve simulation results |
| `get_kpi_summary` | `run_id: str` | `Dict[str, float]` | Get KPI summary for run |
| `compare_runs` | `run_id1: str`<br>`run_id2: str` | `Dict[str, Any]` | Compare two simulation runs |
| `get_provenance` | `run_id: str` | `List[Dict]` | Get provenance records |
| `cleanup_old_runs` | `days: int = 30` | `int` | Remove old simulation data |

##### Enum: `RunType`

```python
class RunType(Enum):
    BASELINE = "baseline"
    SCENARIO = "scenario"  
    OPTIMIZATION = "optimization"
    MONTE_CARLO = "monte_carlo"
```

**Simulation Result Structure:**

```python
{
    "run_id": str,
    "run_type": RunType,
    "status": str,  # "completed", "failed", "running"
    "timestamp": datetime,
    "config": Dict[str, float],
    "kpi_summary": {
        "mean_oee": float,
        "mean_availability": float,
        "mean_performance": float,
        "mean_quality": float,
        "total_production": int,
        "total_good_units": int,
        "total_downtime_minutes": float,
        "energy_consumption": float
    },
    "confidence_intervals": Dict,  # For Monte Carlo
    "optimization_result": Dict,   # For optimization
    "provenance": List[Dict]
}
```

---

#### `twin.optimization_engine`

##### Class: `OptimizationEngine`

Multi-objective optimization using NSGA-II.

```python
class OptimizationEngine:
    def __init__(self, runner: SimulationRunner = None)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `optimize` | `objectives: List[str]`<br>`constraints: List[str]`<br>`n_generations: int`<br>`population_size: int` | `Dict[str, Any]` | Run full optimization |
| `quick_optimize` | `current_kpis: Dict`<br>`target_oee: float`<br>`max_time: int` | `Dict[str, Any]` | Quick optimization with time limit |
| `evaluate_solution` | `config: Dict[str, float]` | `Dict[str, float]` | Evaluate single configuration |
| `get_pareto_front` | `results: List[Dict]` | `List[Dict]` | Extract Pareto-optimal solutions |

**Optimization Result Structure:**

```python
{
    "pareto_front": List[Dict],
    "best_configuration": Dict[str, float],
    "convergence_history": List[float],
    "total_evaluations": int,
    "computation_time": float
}
```

---

#### `twin.recommendation_engine`

##### Class: `RecommendationEngine`

AI-powered recommendation generation.

```python
class RecommendationEngine:
    def __init__(self)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `generate_recommendation` | `scenario: str`<br>`data: Dict` | `Recommendation` | Generate contextual recommendation |
| `quick_wins` | `metric: str`<br>`current_value: float` | `List[str]` | Get quick improvement actions |
| `diagnose_issue` | `symptoms: Dict` | `Dict[str, Any]` | Root cause analysis |
| `prioritize_actions` | `recommendations: List` | `List[Recommendation]` | Prioritize by impact/effort |

**Recommendation Structure:**

```python
class Recommendation:
    recommendation_id: str
    scenario: str
    parameter_changes: Dict[str, float]
    expected_impact: Dict[str, float]
    confidence: float
    implementation_effort: str  # "low", "medium", "high"
    payback_weeks: float
    risk_level: str  # "low", "medium", "high"
```

---

#### `twin.cost_impact_calculator`

##### Class: `CostImpactCalculator`

Financial impact analysis with Monte Carlo.

```python
class CostImpactCalculator:
    def __init__(self, simulation_runner: SimulationRunner)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `calculate_roi` | `baseline_run_id: str`<br>`improved_run_id: str`<br>`n_simulations: int` | `Dict[str, Any]` | Calculate ROI with confidence |
| `estimate_savings` | `kpi_improvement: Dict` | `float` | Estimate weekly savings |
| `calculate_payback` | `investment: float`<br>`weekly_savings: float` | `float` | Calculate payback period |
| `sensitivity_analysis` | `base_case: Dict` | `Dict[str, float]` | Parameter sensitivity on ROI |

**ROI Result Structure:**

```python
{
    "implementation_cost": float,
    "weekly_savings": {
        "mean": float,
        "std": float,
        "confidence_interval": (float, float)
    },
    "payback_weeks": {
        "mean": float,
        "std": float,
        "confidence_interval": (float, float)
    },
    "npv": {
        "mean": float,
        "std": float,
        "confidence_interval": (float, float),
        "probability_positive": float
    },
    "roi_percentage": {
        "mean": float,
        "std": float,
        "confidence_interval": (float, float)
    },
    "annual_benefit": {
        "mean": float,
        "confidence_interval": (float, float)
    }
}
```

---

#### `twin.natural_language_patterns`

##### Class: `NaturalLanguageProcessor`

Process natural language queries.

```python
class NaturalLanguageProcessor:
    def __init__(self)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `classify_intent` | `query: str` | `IntentType` | Classify query intent |
| `extract_entities` | `query: str` | `Dict[str, Any]` | Extract entities from query |
| `process_query` | `query: str`<br>`twin: VirtualTwin` | `Dict[str, Any]` | Process complete query |
| `generate_response` | `intent: IntentType`<br>`data: Dict` | `str` | Generate natural language response |

##### Enum: `IntentType`

```python
class IntentType(Enum):
    STATUS = "status"
    TREND = "trend"
    COMPARISON = "comparison"
    PREDICTION = "prediction"
    OPTIMIZATION = "optimization"
    ROOT_CAUSE = "root_cause"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"
```

---

### Visualization Module

#### `twin.visualization.pareto_plots`

```python
def create_pareto_plot(
    run_ids: List[str],
    objectives: List[str],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create interactive Pareto front visualization"""
```

#### `twin.visualization.time_series`

```python
def plot_kpi_trends(
    run_ids: List[str],
    kpis: List[str],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create time series plot with confidence bands"""
```

#### `twin.visualization.heatmaps`

```python
def create_sensitivity_heatmap(
    run_ids: List[str],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create parameter sensitivity heatmap"""
```

#### `twin.visualization.financial_plots`

```python
def plot_roi_distribution(
    roi_summary: Dict[str, Any]
) -> go.Figure:
    """Create ROI distribution with confidence intervals"""
```

---

## GraphQL API Reference

### Endpoint

```
URL: http://localhost:8000/graphql
WebSocket: ws://localhost:8000/graphql
```

### Schema Types

#### Object Types

##### `TwinRun`
```graphql
type TwinRun {
    runId: String!
    runType: RunType!
    status: String!
    timestamp: DateTime!
    seed: Int!
    generatorVersion: String!
    configDelta: JSON
    kpiSummary: KPISummary
    optimizationResult: OptimizationResult
}
```

##### `KPISummary`
```graphql
type KPISummary {
    meanOee: Float!
    meanAvailability: Float!
    meanPerformance: Float!
    meanQuality: Float!
    totalProduction: Int!
    totalGoodUnits: Int!
    totalDowntimeMinutes: Float!
    energyConsumption: Float!
}
```

##### `Recommendation`
```graphql
type Recommendation {
    recommendationId: String!
    scenario: String!
    parameterChanges: JSON!
    expectedImpact: JSON!
    confidence: Float!
    implementationEffort: String!
    paybackWeeks: Float!
    riskLevel: String!
    expectedOee: Float
    expectedSavings: Float
}
```

##### `SyncHealthReport`
```graphql
type SyncHealthReport {
    equipmentId: String!
    health: Float!
    lastUpdate: DateTime!
    alerts: [String!]!
    metrics: JSON
}
```

##### `PlotResult`
```graphql
type PlotResult {
    plotJson: String!
    plotHtml: String!
    plotType: String!
    metadata: JSON
    exportUrl: String
}
```

#### Input Types

##### `SimulationInput`
```graphql
input SimulationInput {
    runType: RunType!
    duration: Int = 100
    objectives: [String!]
    constraints: [String!]
    config: JSON
}
```

##### `ParameterInput`
```graphql
input ParameterInput {
    micro_stop_probability: Float
    performance_factor: Float
    scrap_multiplier: Float
    material_reliability: Float
    energy_cost_per_kwh: Float
    labor_cost_per_hour: Float
    cascade_sensitivity: Float
}
```

#### Enum Types

##### `RunType`
```graphql
enum RunType {
    BASELINE
    SCENARIO
    OPTIMIZATION
    MONTE_CARLO
}
```

### Queries

#### `healthCheck`
```graphql
query HealthCheck {
    healthCheck: String!
}
```

#### `getRuns`
```graphql
query GetRuns($limit: Int, $runType: RunType) {
    getRuns(limit: $limit, runType: $runType): [TwinRun!]!
}
```

#### `getRun`
```graphql
query GetRun($runId: String!) {
    getRun(runId: $runId): TwinRun
}
```

#### `getRecommendations`
```graphql
query GetRecommendations($scenario: String!) {
    getRecommendations(scenario: $scenario): [Recommendation!]!
}
```

#### `getSyncHealth`
```graphql
query GetSyncHealth {
    getSyncHealth: [SyncHealthReport!]!
}
```

#### `visualization`
```graphql
query Visualization {
    visualization {
        generateParetoPlot(runIds: [String!]!, objectives: [String!]!): PlotResult!
        generateTimeSeries(runId: String!, kpis: [String!]!): PlotResult!
        generateSensitivityHeatmap(runIds: [String!]!): PlotResult!
        generateRoiPlot(baselineId: String!, improvedId: String!): PlotResult!
    }
}
```

### Mutations

#### `runSimulation`
```graphql
mutation RunSimulation($config: SimulationInput!) {
    runSimulation(config: $config): TwinRun!
}
```

#### `updateParameters`
```graphql
mutation UpdateParameters($changes: ParameterInput!) {
    updateParameters(changes: $changes): [ParameterUpdate!]!
}
```

#### `applyRecommendation`
```graphql
mutation ApplyRecommendation($recommendationId: String!) {
    applyRecommendation(recommendationId: $recommendationId): ApplyResult!
}
```

#### `calculateRoi`
```graphql
mutation CalculateROI($baselineId: String!, $improvedId: String!) {
    calculateRoi(baselineId: $baselineId, improvedId: $improvedId): ROIResult!
}
```

### Subscriptions

#### `syncHealthUpdates`
```graphql
subscription SyncHealthUpdates {
    syncHealthUpdates: [SyncHealthReport!]!
}
```

#### `simulationProgress`
```graphql
subscription SimulationProgress($runId: String!) {
    simulationProgress(runId: $runId): SimulationProgress!
}
```

### Example GraphQL Requests

#### Complete Optimization Flow
```graphql
# 1. Run baseline
mutation RunBaseline {
    runSimulation(config: {
        runType: BASELINE,
        duration: 100
    }) {
        runId
        kpiSummary {
            meanOee
        }
    }
}

# 2. Run optimization
mutation RunOptimization {
    runSimulation(config: {
        runType: OPTIMIZATION,
        objectives: ["oee", "energy"],
        constraints: ["quality >= 0.95"]
    }) {
        runId
        optimizationResult {
            paretoFront
            bestConfigurations
        }
    }
}

# 3. Calculate ROI
mutation CalculateROI {
    calculateRoi(
        baselineId: "baseline-001",
        improvedId: "opt-001"
    ) {
        weeklyBenefit
        paybackWeeks
        npv
        confidence
    }
}

# 4. Generate visualization
query GenerateVisualization {
    visualization {
        generateParetoPlot(
            runIds: ["opt-001"],
            objectives: ["oee", "energy"]
        ) {
            plotHtml
        }
    }
}
```

---

## Database Schema

### Tables

#### `twin_runs`
| Column | Type | Description |
|--------|------|-------------|
| `run_id` | TEXT PRIMARY KEY | Unique run identifier |
| `run_type` | TEXT | Type of simulation run |
| `status` | TEXT | Run status |
| `timestamp` | TIMESTAMP | Run timestamp |
| `seed` | INTEGER | Random seed |
| `generator_version` | TEXT | Generator version |
| `config_delta_json` | TEXT | Configuration JSON |
| `kpi_summary_json` | TEXT | KPI summary JSON |
| `optimization_result_json` | TEXT | Optimization results JSON |

#### `simulation_data`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Record ID |
| `run_id` | TEXT | Foreign key to twin_runs |
| `timestamp` | TIMESTAMP | Data timestamp |
| `equipment_id` | TEXT | Equipment identifier |
| `state` | TEXT | Equipment state |
| `oee` | REAL | Overall Equipment Effectiveness |
| `availability` | REAL | Availability metric |
| `performance` | REAL | Performance metric |
| `quality` | REAL | Quality metric |
| `production_count` | INTEGER | Production count |
| `good_count` | INTEGER | Good units count |
| `defect_count` | INTEGER | Defect count |
| `downtime_minutes` | REAL | Downtime in minutes |
| `energy_kwh` | REAL | Energy consumption |

#### `optimization_results`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Record ID |
| `run_id` | TEXT | Foreign key to twin_runs |
| `generation` | INTEGER | Generation number |
| `solution_index` | INTEGER | Solution index |
| `objectives_json` | TEXT | Objective values JSON |
| `parameters_json` | TEXT | Parameter values JSON |
| `is_pareto` | BOOLEAN | Is Pareto-optimal |

#### `provenance_records`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Record ID |
| `run_id` | TEXT | Foreign key to twin_runs |
| `activity_id` | TEXT | PROV activity ID |
| `activity_type` | TEXT | Type of activity |
| `agent` | TEXT | Agent performing activity |
| `timestamp` | TIMESTAMP | Activity timestamp |
| `inputs_json` | TEXT | Input entities JSON |
| `outputs_json` | TEXT | Output entities JSON |
| `attributes_json` | TEXT | Additional attributes JSON |

---

## Error Codes and Handling

### Error Code Reference

| Code | Type | Description | Resolution |
|------|------|-------------|------------|
| `E001` | Validation | Invalid parameter value | Check parameter ranges |
| `E002` | Validation | Missing required field | Provide all required fields |
| `E003` | Database | Connection failed | Check database path |
| `E004` | Database | Query failed | Check query syntax |
| `E005` | Simulation | Simulation failed | Check configuration |
| `E006` | Simulation | Optimization timeout | Increase time limit |
| `E007` | API | GraphQL query error | Check query syntax |
| `E008` | API | Subscription failed | Check WebSocket connection |
| `E009` | Visualization | Plot generation failed | Check data availability |
| `E010` | System | Out of memory | Reduce simulation size |

### Error Handling Examples

```python
# Python error handling
try:
    result = runner.run_simulation(
        run_type=RunType.OPTIMIZATION,
        duration=100
    )
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    # Handle validation error
except SimulationError as e:
    logger.error(f"Simulation failed: {e}")
    # Handle simulation error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle unexpected error
```

```graphql
# GraphQL error handling
mutation RunSimulation {
    runSimulation(config: {...}) {
        ... on TwinRun {
            runId
            status
        }
        ... on Error {
            code
            message
        }
    }
}
```

---

## Rate Limiting and Quotas

### API Limits

| Endpoint | Rate Limit | Burst | Notes |
|----------|------------|-------|-------|
| GraphQL Query | 100/min | 10 | Per client |
| GraphQL Mutation | 20/min | 5 | Per client |
| GraphQL Subscription | 10 concurrent | - | Per client |
| Simulation | 10/hour | 2 | Per user |
| Optimization | 5/hour | 1 | Per user |

### Resource Quotas

| Resource | Limit | Notes |
|----------|-------|-------|
| Simulation Duration | 10,000 steps | Per run |
| Optimization Generations | 100 | Per run |
| Monte Carlo Iterations | 10,000 | Per run |
| Database Storage | 10 GB | Per instance |
| Concurrent Users | 100 | Per instance |

---

## Versioning

### API Version

Current API Version: `1.0.0`

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Current | Initial release |

### Deprecation Policy

- Features are deprecated with 3 months notice
- Deprecated features remain functional for 6 months
- Breaking changes require major version increment

---

## Security

### Authentication

```python
# API key authentication
headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}
```

### Authorization

| Role | Permissions |
|------|------------|
| `viewer` | Read-only access |
| `operator` | Run simulations |
| `admin` | Full access |

### Data Privacy

- All data encrypted at rest
- TLS 1.3 for data in transit
- PII data anonymization available
- Audit logging for all operations

---

*This API reference is automatically generated from the source code. For the latest updates, refer to the inline documentation.*