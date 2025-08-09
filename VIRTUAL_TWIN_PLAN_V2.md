# Virtual Twin POC - Standards-Compliant Implementation Plan v2

## Executive Summary

A virtual twin that meets ISO 23247, DTC, and NIST definitions through:
- **Representation**: Ontology with SOSA observations and QUDT units
- **Synchronization**: Visible 5-min sync with health monitoring  
- **Interaction**: Diagnose → Predict → Optimize → Prescribe

The magic: Claude Code as a natural language REPL for manufacturing optimization.

## Standards Alignment Proof Table

| Requirement | Our Implementation | Standard Reference |
|------------|-------------------|-------------------|
| Digital Representation | SOSA/SSN observations, QUDT units | ISO 23247 "observable elements" |
| Synchronization | 5-min intervals, sync health panel | DTC "specified frequency/fidelity" |
| Interaction | KPI analysis → simulation → optimization | NIST "observe/diagnose/predict/optimize" |
| Provenance | Run ledger with seed, version, hash | NIST "dependable/controlled" |
| Prescriptive | Multi-objective optimization with constraints | NIST functional classification |

## Phase 1: Standards-Compliant Ontology (Day 1)

### twin_ontology_spec.yaml Structure

```yaml
# QUDT Units with URIs and Quantity Kinds
properties:
  hasGoodUnitsProduced:
    unit: "unit:NUM"  # QUDT URI
    quantityKind: "qudt:Dimensionless"
    
  hasTemperature:
    unit: "unit:DEG_C"
    quantityKind: "qudt:ThermodynamicTemperature"
    
  hasScrapRatio:
    unit: "qudt:Percent"
    quantityKind: "qudt:MassFraction"
    
  hasEnergyPerUnit:
    unit: "unit:KiloW-HR"
    quantityKind: "qudt:Energy"

# SOSA Observation Structure
observations:
  ThroughputObservation:
    sosa:Sensor: "ThroughputSensor"
    sosa:observedProperty: "qudt:VolumetricFlowRate"
    sosa:featureOfInterest: "Equipment"
    sosa:resultTime: "xsd:dateTime"
    sosa:hasResult: "qudt:QuantityValue"

# Synchronization Metadata
sync:
  Equipment:
    interval: "PT5M"  # ISO 8601 duration
    last_update: "2025-08-08T15:35:00Z"
    source: "sim:run-2025-08-01"
    health_status: "HEALTHY"  # HEALTHY | DELAYED | STALE
```

### Virtual Sensors with Proper Semantics

```yaml
virtual_sensors:
  Equipment:
    embeds:
      - sensor_id: "throughput_sensor_{equipment_id}"
        type: "sosa:Sensor"
        observes:
          property: "qudt:VolumetricFlowRate"
          unit: "unit:NUM-PER-MIN"
          quantityKind: "qudt:CountingUnit"
          
      - sensor_id: "quality_sensor_{equipment_id}"
        type: "sosa:Sensor"
        observes:
          property: "qudt:MassFraction"
          unit: "qudt:Percent"
          quantityKind: "qudt:Dimensionless"
          
      - sensor_id: "power_meter_{equipment_id}"
        type: "sosa:Sensor"
        observes:
          property: "qudt:Power"
          unit: "unit:KiloW"
          quantityKind: "qudt:Power"
```

## Phase 2: Actionable Parameters with Bounds & Causality (Day 1-2)

### twin/actionable_parameters.py

```python
from dataclasses import dataclass
from typing import Tuple

@dataclass
class ActionableParameter:
    name: str
    bounds: Tuple[float, float]
    unit: str  # QUDT URI
    causal_effect: str
    invariants: list[str]

PARAMETERS = {
    "micro_stop_probability": ActionableParameter(
        name="Micro-stop Probability",
        bounds=(0.05, 0.50),
        unit="qudt:Probability",
        causal_effect="Reduces availability score",
        invariants=["Cannot exceed equipment failure rate"]
    ),
    "performance_factor": ActionableParameter(
        name="Performance Factor",
        bounds=(0.50, 1.00),
        unit="qudt:Dimensionless",
        causal_effect="Scales actual vs target throughput",
        invariants=["Cannot exceed physical line speed"]
    ),
    "scrap_multiplier": ActionableParameter(
        name="Scrap Rate Multiplier",
        bounds=(1.0, 5.0),
        unit="qudt:Dimensionless",
        causal_effect="Increases defect_rate, reduces quality score",
        invariants=["Total output cannot be negative"]
    ),
    "material_reliability": ActionableParameter(
        name="Material Supply Reliability",
        bounds=(0.50, 1.00),
        unit="qudt:Probability",
        causal_effect="Probability of good material batch",
        invariants=["Affects upstream equipment first"]
    ),
    "cascade_sensitivity": ActionableParameter(
        name="Line Coupling Strength",
        bounds=(0.0, 1.0),
        unit="qudt:Dimensionless",
        causal_effect="Controls blockage/starvation propagation",
        invariants=["Requires buffer model"]
    )
}
```

### Line Coupling Model for Cascades

```python
@dataclass
class LineCoupling:
    """Explicit cascade model with buffers"""
    buffer_capacity: int = 100  # units
    depletion_rate: float = 10  # units/min when upstream stopped
    refill_rate: float = 20  # units/min when upstream running
    
    def calculate_starvation(self, buffer_level: int, upstream_status: str) -> bool:
        """Deterministic starvation logic, not correlation"""
        if upstream_status == "Stopped":
            new_level = buffer_level - self.depletion_rate * 5  # 5-min interval
            if new_level <= 0:
                return True  # Downstream starves
        return False
```

## Phase 3: Run Ledger with Full Provenance (Day 2)

### Database Schema

```sql
-- Run tracking with complete provenance
CREATE TABLE twin_runs (
    run_id TEXT PRIMARY KEY,
    run_type TEXT CHECK(run_type IN ('baseline', 'simulation', 'recommendation')),
    seed INTEGER NOT NULL,
    generator_version TEXT NOT NULL,
    parent_run_id TEXT REFERENCES twin_runs(run_id),
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    config_delta_json TEXT NOT NULL,
    data_hash TEXT NOT NULL,  -- SHA256 of output data
    notes TEXT
);

-- KPI results with evaluation windows
CREATE TABLE kpi_results (
    run_id TEXT REFERENCES twin_runs(run_id),
    entity_id TEXT NOT NULL,
    kpi TEXT NOT NULL,
    value REAL NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    aggregation_method TEXT,  -- 'mean', 'p95', 'min', 'max'
    PRIMARY KEY (run_id, entity_id, kpi, window_start)
);

-- Sync health tracking
CREATE VIEW sync_health AS
SELECT 
    entity_id,
    last_update,
    sync_interval,
    CASE 
        WHEN (julianday('now') - julianday(last_update)) * 24 * 60 <= sync_interval_minutes 
        THEN 'HEALTHY'
        WHEN (julianday('now') - julianday(last_update)) * 24 * 60 <= sync_interval_minutes * 2
        THEN 'DELAYED'
        ELSE 'STALE'
    END as health_status
FROM entity_sync_metadata;
```

## Phase 4: Natural Language with Validation (Day 3)

### Enhanced NL Pattern Mapping

```yaml
patterns:
  - query: "reduce {entity} by {percent}%"
    validation:
      percent: "float(0, 100) → decimal"
      entity: "resolve_to_parameter"
    action: "adjust_parameter"
    
  - query: "optimize for {objective}"
    validation:
      objective: "enum[oee, quality, energy, cost]"
    constraints_prompt: "Specify constraints (e.g., quality >= 95%)"
    action: "multi_objective_optimization"
    
  - query: "what if {improvement}"
    disambiguation:
      "better maintenance": "micro_stop_probability *= 0.5"
      "skilled operators": "performance_factor = 0.95"
      "improved materials": "material_reliability = 0.90"
    action: "simulate_scenario"
```

### Multi-Objective Optimization

```python
def optimize_parameters(
    objective: str,
    constraints: dict,
    eval_window: str = "7d_sliding"
) -> list[Recommendation]:
    """
    Multi-objective optimization with constraints
    
    Objectives:
    - OEE_max: Maximize OEE
    - Cost_min: Minimize operational cost
    - Energy_min: Minimize energy per unit
    
    Constraints:
    - quality >= 0.95
    - throughput >= baseline * 0.9
    - energy_per_unit <= threshold
    """
    
    # Start with Latin Hypercube sampling
    initial_samples = latin_hypercube(n_samples=20, n_params=5)
    
    # Evaluate each sample
    results = []
    for sample in initial_samples:
        run_id = simulate_with_params(sample)
        kpis = evaluate_kpis(run_id, window=eval_window)
        results.append((sample, kpis))
    
    # Switch to Bayesian optimization in promising region
    best_region = identify_best_region(results)
    optimizer = BayesianOptimization(
        bounds=best_region,
        objective=compose_objective(objective, constraints)
    )
    
    # Generate recommendations with confidence
    recommendations = []
    for i in range(3):
        params, expected_value, confidence = optimizer.suggest()
        
        # Validate with multiple seeds
        validation_runs = [simulate_with_params(params, seed=s) for s in range(5)]
        mean_kpi = np.mean([evaluate_kpis(r) for r in validation_runs])
        std_kpi = np.std([evaluate_kpis(r) for r in validation_runs])
        
        recommendations.append(Recommendation(
            params=params,
            expected_improvement=expected_value,
            confidence=confidence,
            validation_mean=mean_kpi,
            validation_std=std_kpi
        ))
    
    return recommendations
```

## Phase 5: GraphQL with Safety (Day 4 - Optional)

### Auto-Generated Schema with Limits

```graphql
# Generated from ontology with safety controls
schema {
  query: Query
  mutation: Mutation
}

type Query {
  # Depth limit: 3, Complexity limit: 100
  equipment(id: ID!): Equipment
  currentState: TwinState!
  syncHealth: SyncHealthReport!
  compareRuns(runIds: [ID!]!): RunComparison!
}

type Mutation {
  # Persisted operations only (hash-pinned)
  simulate(
    parameters: ActionableParametersInput!
    seed: Int!
  ): SimulationResult!
  
  recommend(
    objective: Objective!
    constraints: [Constraint!]
    evalWindow: String! = "7d_sliding"
  ): [Recommendation!]!
}

type SyncHealthReport {
  healthy: Int!
  delayed: Int!
  stale: Int!
  details: [EntitySyncStatus!]!
}
```

## Phase 6: Demo with NIST Classification (Day 5)

### Four-Stage Demo Showing NIST Progression

```python
def demo_nist_progression():
    """Demonstrate progression through NIST twin functions"""
    
    print("=== DESCRIPTIVE (Current State) ===")
    # Query current OEE, bottlenecks, quality
    current_state = query_current_kpis()
    
    print("=== DIAGNOSTIC (Root Cause) ===")
    # Identify why Line 1 underperforms
    root_cause = analyze_performance_gaps()
    
    print("=== PREDICTIVE (What-If) ===")
    # Simulate improvement scenarios
    scenarios = [
        simulate("reduce micro-stops by 30%"),
        simulate("improve operator training"),
        simulate("upgrade material handling")
    ]
    
    print("=== PRESCRIPTIVE (Optimize) ===")
    # Multi-objective optimization
    recommendations = optimize(
        objective="maximize OEE",
        constraints=["quality >= 95%", "energy <= baseline * 1.1"]
    )
    
    # Show confidence via multi-seed validation
    for rec in recommendations:
        print(f"Expected OEE: {rec.mean:.1f}% ± {rec.std:.1f}%")
        print(f"ROI: ${calculate_roi(rec)}/month")
```

### Cost Model for Financial Impact

```python
COST_MODEL = {
    "energy_per_kwh": 0.12,
    "scrap_cost_per_unit": 0.35,  # Material + disposal
    "micro_stop_cost_per_min": 25.00,  # Lost production value
    "labor_cost_per_hour": 35.00
}

def calculate_financial_impact(baseline_run: str, sim_run: str) -> dict:
    """Calculate financial impact with full cost model"""
    baseline_kpis = get_kpis(baseline_run)
    sim_kpis = get_kpis(sim_run)
    
    # Calculate deltas
    scrap_reduction = baseline_kpis.scrap - sim_kpis.scrap
    energy_reduction = baseline_kpis.energy - sim_kpis.energy
    uptime_increase = sim_kpis.availability - baseline_kpis.availability
    
    # Convert to dollars
    savings = {
        "scrap": scrap_reduction * COST_MODEL["scrap_cost_per_unit"],
        "energy": energy_reduction * COST_MODEL["energy_per_kwh"],
        "uptime": uptime_increase * 60 * COST_MODEL["micro_stop_cost_per_min"]
    }
    
    return {
        "weekly_savings": sum(savings.values()),
        "annual_impact": sum(savings.values()) * 52,
        "breakdown": savings
    }
```

## Deliverables

1. **twin_ontology_spec.yaml** - SOSA/QUDT compliant ontology
2. **twin_state.db** - Run ledger with provenance
3. **sync_health_dashboard.py** - Real-time sync monitoring
4. **recommendation_engine.py** - Multi-objective optimization
5. **line_coupling_model.py** - Explicit cascade logic
6. **cost_impact_calculator.py** - Financial validation
7. **TWIN_PROOF.md** - Standards mapping with citations

## Success Criteria

✅ Passes ISO 23247 "observable elements" check (QUDT units)  
✅ Meets DTC synchronization requirement (visible sync health)  
✅ Achieves NIST "prescriptive" classification (optimization)  
✅ Reproducible recommendations (seed + version + hash)  
✅ Financially validated (cost model with ROI)

## What Makes This a True Virtual Twin

- **Not just a simulator**: Full provenance, synchronization proof, standards compliance
- **Not just analytics**: Prescriptive optimization with constraints
- **Not just correlation**: Explicit causal models (line coupling, buffers)
- **Not just academic**: Financial impact with cost model
- **Natural language first**: Claude Code as the interface

This implementation meets or exceeds all virtual twin standards while maintaining the pragmatic, SQL-first philosophy of the original virtual ontology project.