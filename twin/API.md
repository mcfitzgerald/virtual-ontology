# Virtual Twin API Reference

Complete API documentation for the Virtual Twin module.

## Core Components

### SimulationRunner

Main class for executing simulations and managing runs.

```python
class SimulationRunner(db_path: str = "data/mes_database.db")
```

#### Methods

##### run_simulation
```python
def run_simulation(
    parameters: ActionableParameters,
    parent_run_id: Optional[str] = None,
    seed: Optional[int] = None,
    duration_days: int = 7,
    notes: Optional[str] = None
) -> SimulationRun
```
Execute a simulation with specified parameters.

**Parameters:**
- `parameters`: ActionableParameters object with configuration
- `parent_run_id`: Optional parent run for lineage tracking
- `seed`: Random seed for reproducibility
- `duration_days`: Simulation duration (1-30 days)
- `notes`: Optional description

**Returns:** SimulationRun object with results

##### create_baseline
```python
def create_baseline(
    seed: int = 42,
    duration_days: int = 7,
    notes: Optional[str] = None
) -> SimulationRun
```
Create a baseline simulation with default parameters.

##### compare_runs
```python
def compare_runs(run_ids: List[str]) -> Dict[str, Any]
```
Compare multiple simulation runs.

**Returns:** Dictionary with KPI comparisons and parameter differences

##### get_run_lineage
```python
def get_run_lineage(run_id: str) -> List[SimulationRun]
```
Get complete lineage (ancestors and descendants) of a run.

---

### ActionableParameters

Manages simulation parameters with validation and bounds.

```python
class ActionableParameters()
```

#### Methods

##### set_value
```python
def set_value(parameter_name: str, value: float) -> None
```
Set a parameter value with validation.

**Parameters:**
- `parameter_name`: Name of parameter to set
- `value`: New value (must be within bounds)

**Raises:** ValueError if value outside bounds

##### get_value
```python
def get_value(parameter_name: str) -> float
```
Get current value of a parameter.

##### get_all_values
```python
def get_all_values() -> Dict[str, float]
```
Get all parameter values as dictionary.

##### reset
```python
def reset(parameter_name: Optional[str] = None) -> None
```
Reset parameter(s) to default values.

#### Available Parameters

| Parameter | Default | Bounds | Description |
|-----------|---------|--------|-------------|
| micro_stop_probability | 0.10 | [0.0, 1.0] | Likelihood of brief stops |
| performance_factor | 0.85 | [0.5, 1.0] | Speed/efficiency multiplier |
| scrap_multiplier | 1.0 | [0.5, 2.0] | Quality/scrap adjustment |
| material_reliability | 0.85 | [0.5, 1.0] | Supply chain reliability |
| cascade_sensitivity | 0.3 | [0.0, 1.0] | Downstream impact strength |

---

## Analysis Components

### OptimizationEngine

Multi-objective optimization using NSGA-II algorithm.

```python
class OptimizationEngine(db_path: str = "data/mes_database.db")
```

#### Methods

##### run_optimization
```python
def run_optimization(
    objectives: List[str],
    directions: List[str],
    population_size: int = 50,
    n_generations: int = 20,
    constraints: Optional[Dict] = None
) -> Dict[str, Any]
```
Run multi-objective optimization.

**Parameters:**
- `objectives`: List of KPIs to optimize (e.g., ["mean_oee", "energy_per_unit"])
- `directions`: Optimization direction for each ("maximize" or "minimize")
- `population_size`: Size of solution population
- `n_generations`: Number of evolutionary generations
- `constraints`: Optional parameter constraints

**Returns:** Dictionary with Pareto front solutions

##### evaluate_configuration
```python
def evaluate_configuration(config: Dict[str, float]) -> Dict[str, float]
```
Evaluate a single configuration.

**Returns:** Dictionary of KPI values

---

### RecommendationEngine

Generate scenario-based parameter recommendations.

```python
class RecommendationEngine(db_path: str = "data/mes_database.db")
```

#### Methods

##### recommend_for_oee_improvement
```python
def recommend_for_oee_improvement(baseline_run_id: Optional[str] = None) -> List[Dict]
```
Generate recommendations to improve OEE.

**Returns:** List of parameter recommendations with expected impacts

##### recommend_for_downtime_reduction
```python
def recommend_for_downtime_reduction() -> List[Dict]
```
Generate recommendations to reduce downtime.

##### recommend_for_quality_improvement
```python
def recommend_for_quality_improvement() -> List[Dict]
```
Generate recommendations to improve quality.

##### recommend_for_energy_efficiency
```python
def recommend_for_energy_efficiency() -> List[Dict]
```
Generate recommendations for energy efficiency.

##### multi_objective_optimization
```python
def multi_objective_optimization(
    objectives: List[str] = ["mean_oee", "downtime_percentage"],
    population_size: int = 50,
    n_generations: int = 20
) -> List[Dict]
```
Find Pareto-optimal configurations.

---

### CostImpactCalculator

Calculate financial impacts of parameter changes.

```python
class CostImpactCalculator(
    hourly_revenue_per_unit: float = 2.50,
    hourly_operating_cost: float = 1000.0
)
```

#### Methods

##### calculate_financial_impact
```python
def calculate_financial_impact(
    baseline_kpis: Dict[str, float],
    scenario_kpis: Dict[str, float],
    duration_days: int = 30
) -> Dict[str, float]
```
Calculate financial impact of KPI changes.

**Returns:** Dictionary with:
- `revenue_impact`: Change in revenue
- `cost_impact`: Change in costs
- `net_impact`: Net financial impact
- `roi_percentage`: Return on investment

##### calculate_roi
```python
def calculate_roi(
    net_benefit: float,
    implementation_cost: float
) -> float
```
Calculate return on investment percentage.

---

## Support Components

### DisambiguationHelper

Natural language query interpretation and entity resolution.

```python
class DisambiguationHelper(db_path: str = "data/mes_database.db")
```

#### Methods

##### get_query_context
```python
def get_query_context(query: str) -> Dict[str, Any]
```
Provide context to help interpret a query.

**Returns:** Dictionary with:
- `entities`: Identified entities (lines, equipment, etc.)
- `timeframe`: Temporal references
- `parameter_hints`: Likely relevant parameters
- `suggested_clarifications`: Questions to ask user

##### resolve_entity
```python
def resolve_entity(entity_type: str, entity_ref: str) -> Optional[str]
```
Resolve entity reference to canonical form.

**Parameters:**
- `entity_type`: Type of entity ("line", "equipment", "shift")
- `entity_ref`: Reference string from query

**Returns:** Canonical entity ID or None if ambiguous

---

### TwinStateManager

Track and manage virtual twin state.

```python
class TwinStateManager(db_path: str = "data/mes_database.db")
```

#### Methods

##### update_state
```python
def update_state(
    entity_id: str,
    state_data: Dict[str, Any],
    source_run_id: Optional[str] = None
) -> None
```
Update state for an entity.

##### get_state
```python
def get_state(entity_id: str) -> Optional[Dict[str, Any]]
```
Get current state of an entity.

##### get_state_history
```python
def get_state_history(
    entity_id: str,
    hours: int = 24
) -> List[Dict[str, Any]]
```
Get historical state data.

---

### SyncHealthMonitor

Monitor synchronization health between physical and virtual systems.

```python
class SyncHealthMonitor(db_path: str = "data/mes_database.db")
```

#### Methods

##### update_sync_metadata
```python
def update_sync_metadata(
    entity_id: str,
    entity_type: str,
    data: Dict[str, Any],
    source_run_id: Optional[str] = None,
    sync_interval_minutes: int = 5
) -> None
```
Update synchronization metadata for an entity.

##### get_sync_health
```python
def get_sync_health(entity_id: Optional[str] = None) -> List[SyncHealth]
```
Get synchronization health status.

##### get_health_summary
```python
def get_health_summary() -> Dict[str, Any]
```
Get overall health summary statistics.

---

### LineCouplingModel

Model interactions between production lines.

```python
class LineCouplingModel(base_coupling_strength: float = 0.3)
```

#### Methods

##### calculate_impact
```python
def calculate_impact(
    source_line: str,
    target_line: str,
    source_performance: float,
    sensitivity: float = 0.3
) -> float
```
Calculate performance impact between lines.

**Returns:** Impact factor (0.0 to 1.0)

##### get_coupling_matrix
```python
def get_coupling_matrix() -> np.ndarray
```
Get full coupling matrix for all lines.

---

## Data Classes

### SimulationRun

Data class for simulation run metadata.

```python
@dataclass
class SimulationRun:
    run_id: str
    run_type: str  # "baseline", "simulation", "optimization"
    seed: int
    generator_version: str
    parent_run_id: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    config_delta: Dict[str, Any]
    data_hash: str
    output_path: str
    kpi_summary: Optional[Dict[str, float]]
    notes: Optional[str]
    status: str  # "running", "completed", "failed"
```

### Parameter

Data class for parameter definition.

```python
@dataclass
class Parameter:
    name: str
    default: float
    current: float
    bounds: Tuple[float, float]
    unit: str
    description: str
```

### HealthStatus

Enum for synchronization health status.

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
```

---

## Exceptions

### ParameterValidationError
Raised when parameter value is outside valid bounds.

### SimulationError
Raised when simulation execution fails.

### OptimizationError
Raised when optimization fails to converge.

---

## Configuration Files

### ontology/disambiguation_patterns.yaml

Defines natural language patterns for query interpretation:
- Pattern mappings to operations
- Parameter name translations
- Objective mappings
- Response templates

---

## Database Tables

### twin_runs
Stores simulation run metadata.

### simulation_data
Time-series data from simulations.

### parameter_history
Tracks parameter changes over time.

### simulation_configs
Stores full simulation configurations.

### twin_state
Current state of virtual twin entities.

### sync_health_log
Synchronization health monitoring data.