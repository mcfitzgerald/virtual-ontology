# Virtual Twin POC - Natural Language Manufacturing Optimization

## Core Vision

Extend the virtual ontology project to demonstrate a true virtual twin where Claude Code acts as a conversational interface for:
- Understanding current state through semantic queries
- Simulating operational improvements 
- Recommending optimizations via parameter tuning
- All through natural language, no SQL required

The magic is in the natural language REPL pattern:
```
User: "What if we reduced micro-stops by 50%?"
Claude: *adjusts probabilities, runs simulation, returns KPI delta*

User: "Find the optimal cleaning frequency"  
Claude: *explores parameter space, returns recommendation*

User: "Show me cascade failures from upstream equipment"
Claude: *queries twin state with semantic understanding*
```

## What Makes This a True Virtual Twin

This implementation delivers the three pillars of a virtual twin per ISO 23247, DTC, and NIST:

1. **Digital Representation**: Full ontology with SOSA/SSN sensors and QUDT units - a structured, typed model of observable manufacturing elements
2. **Synchronization**: Explicit 5-min sync intervals with visible health monitoring - meets DTC's "synchronized at specified frequency/fidelity" 
3. **Interaction**: Complete NIST arc - Observe → Diagnose → Predict → Optimize → Prescribe, with reproducible provenance

### Standards Alignment Proof

| Requirement | Our Implementation | Standard Reference |
|------------|-------------------|-------------------|
| Digital Representation | SOSA/SSN observations, QUDT units | ISO 23247 "observable elements" |
| Synchronization | 5-min intervals, sync health panel | DTC "specified frequency/fidelity" |
| Interaction | KPI analysis → simulation → optimization | NIST "observe/diagnose/predict/optimize" |
| Provenance | Run ledger with seed, version, hash | NIST "dependable/controlled" |
| Prescriptive | Multi-objective optimization with constraints | NIST functional classification |

## Implementation Phases

### Phase 1: Twin Ontology & Virtual Sensors (Day 1)

**Core Concept**: Extend the existing ontology with virtual sensors that observe equipment state, mapping cleanly to SOSA without adding complexity.

**Virtual Sensor Architecture:**
```yaml
virtual_sensors:
  Equipment:
    embeds:
      # Production sensors
      - ThroughputSensor:
          sensor_id: "throughput_sensor_{equipment_id}"
          type: "sosa:Sensor"
          observes: 
            property: "qudt:VolumetricFlowRate"
            unit: "http://qudt.org/vocab/unit/NUM-PER-MIN"  # Full QUDT URI
            quantityKind: "http://qudt.org/vocab/quantitykind/CountingUnit"
      
      # Quality sensors  
      - QualityInspector:
          sensor_id: "quality_sensor_{equipment_id}"
          type: "sosa:Sensor"
          observes:
            property: "qudt:MassFraction"
            unit: "http://qudt.org/vocab/unit/PERCENT"
            quantityKind: "http://qudt.org/vocab/quantitykind/Dimensionless"
      
      # Efficiency sensors
      - PowerMeter:
          sensor_id: "power_meter_{equipment_id}"
          type: "sosa:Sensor"
          observes:
            property: "qudt:Power"
            unit: "http://qudt.org/vocab/unit/KiloW"
            quantityKind: "http://qudt.org/vocab/quantitykind/Power"
      
      # Flow sensors
      - MaterialFlowSensor:
          observes: ["input_rate", "buffer_level"]
          unit: "http://qudt.org/vocab/unit/NUM"
      
      # Diagnostic sensors
      - VibrationSensor:
          observes: ["vibration_level"]  # proxy for mechanical health
          unit: "http://qudt.org/vocab/unit/MilliM-PER-SEC"
      
      - TemperatureSensor:
          observes: ["operating_temp"]  # affects quality
          unit: "http://qudt.org/vocab/unit/DEG_C"
          quantityKind: "http://qudt.org/vocab/quantitykind/ThermodynamicTemperature"
```

**Synchronization Metadata:**
```yaml
sync:
  Equipment:
    interval: "PT5M"  # ISO 8601 duration
    last_update: "2025-08-08T15:35:00Z"
    source: "sim:run-2025-08-01"
    health_status: "HEALTHY"  # HEALTHY | DELAYED | STALE
```

**Files to create/modify:**
- `ontology/twin_ontology_spec.yaml` - extends base with SOSA/QUDT compliant sensors
- `twin/sync_health.py` - monitors `now - last_update <= sync.interval`

### Phase 2: Actionable Parameters Module (Day 1-2)

**Core Concept**: Define 5 tunable parameters that serve as proxies for real-world improvements - what we can adjust in the simulation to model operational changes.

**The 5 Actionable Parameters:**
```python
@dataclass
class ActionableParameter:
    name: str
    bounds: Tuple[float, float]
    unit: str  # QUDT URI
    causal_effect: str
    invariants: list[str]
```

1. **Micro-stop Probability** (0.05-0.50)
   - Proxy for: Equipment maintenance quality, operator vigilance
   - Causal effect: Reduces availability score
   - Unit: `qudt:Probability`

2. **Performance Factor** (0.50-1.00)
   - Proxy for: Operator skill level, equipment calibration
   - Causal effect: Scales actual vs target throughput
   - Unit: `qudt:Dimensionless`

3. **Scrap Multiplier** (1.0-5.0)
   - Proxy for: Quality control procedures, material handling
   - Causal effect: Increases defect rate, reduces quality score
   - Unit: `qudt:Dimensionless`

4. **Material Reliability** (0.50-1.00)
   - Proxy for: Supply chain coordination, buffer management
   - Causal effect: Probability of good material batch
   - Unit: `qudt:Probability`

5. **Cascade Sensitivity** (0.0-1.0)
   - Proxy for: Line coupling strength, buffer capacity
   - Causal effect: Controls blockage/starvation propagation
   - Unit: `qudt:Dimensionless`

**Line Coupling Model** (explicit causation with probabilistic elements):
```python
@dataclass
class LineCoupling:
    """Explicit cascade model with buffers and stochastic variation"""
    buffer_capacity: int = 100  # units
    depletion_rate: float = 10  # units/min when upstream stopped
    refill_rate: float = 20  # units/min when upstream running
    depletion_noise_std: float = 2.0  # standard deviation for variation
    
    def calculate_starvation(self, buffer_level: int, upstream_status: str, 
                            use_probabilistic: bool = True) -> bool:
        """Hybrid deterministic/stochastic starvation logic"""
        if upstream_status == "Stopped":
            # Add probabilistic noise to depletion rate
            if use_probabilistic:
                actual_depletion = np.random.normal(
                    self.depletion_rate, 
                    self.depletion_noise_std
                )
            else:
                actual_depletion = self.depletion_rate
                
            new_level = buffer_level - actual_depletion * 5  # 5-min interval
            
            if new_level <= 0:
                return True  # Downstream starves
        return False
```

**Files to create:**
- `twin/actionable_parameters.py` - parameter definitions with bounds and causality
- `twin/config_transformer.py` - maps parameters to mes_data_config.json
- `twin/line_coupling_model.py` - explicit cascade logic

**Modify:**
- `synthetic_data_generator/mes_data_generation.py` - accept ActionableParameters overlay

### Phase 3: Simulation Runner with Provenance (Day 2)

**Core Concept**: Every simulation run must be reproducible with complete provenance tracking.

**Run Ledger Schema:**
```sql
-- Complete provenance for trust and reproducibility
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
```

**Sync Health Monitoring:**
```sql
-- Visible synchronization proof
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

**Files to create:**
- `twin/simulation_runner.py` - wraps generator with deterministic seeding
- `twin/twin_state.py` - manages run ledger and provenance
- `twin/sync_health_dashboard.py` - real-time sync monitoring

### Phase 4: Natural Language Patterns & Optimization (Day 3)

**Core Concept**: Map natural language queries to validated, typed operations with smart disambiguation.

**Example Natural Language Interactions:**
```python
# How Claude Code interprets twin queries:

"What's the impact of better maintenance?"
→ reduce micro_stop_probability by 50%
→ run simulation
→ compare OEE: baseline vs simulation
→ return: "OEE improves from 65% to 78% (+$45K/week)"

"Optimize for energy efficiency"
→ objective: minimize energy_per_unit
→ constraint: maintain quality > 95%
→ explore: speed vs power consumption tradeoff
→ recommend: "Reduce throughput to 85% for 20% energy savings"

"Why is Line 2 outperforming others?"
→ query: comparative analysis across lines
→ identify: Line 2 has 50% lower micro-stop probability
→ root cause: better maintenance practices
→ suggest: "Replicate Line 2 maintenance schedule"

"Simulate a skilled operator on night shift"
→ set operator_issues_probability = 0.02 (from 0.12)
→ run 2-week simulation
→ calculate: ROI of training program
→ return: "$8K/month savings justifies $15K training cost"

"Find the bottleneck when running energy drinks"
→ filter: product = 'SKU-2002'
→ aggregate: performance by equipment
→ identify: LINE1-FIL at 65% efficiency
→ diagnose: "Filler is constraining throughput"
```

**Multi-Objective Optimization with Pareto Front:**
```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
import numpy as np

class ManufacturingOptimization(Problem):
    """Multi-objective problem formulation for pymoo"""
    def __init__(self):
        super().__init__(
            n_var=5,  # 5 actionable parameters
            n_obj=3,  # OEE, Cost, Energy
            n_constr=2,  # Quality >= 95%, Throughput >= baseline * 0.9
            xl=[0.05, 0.50, 1.0, 0.50, 0.0],  # Lower bounds
            xu=[0.50, 1.00, 5.0, 1.00, 1.0]   # Upper bounds
        )
    
    def _evaluate(self, x, out, *args, **kwargs):
        # Run simulations for each parameter set
        simulations = [simulate_with_params(params) for params in x]
        
        # Objectives (to minimize: negative OEE, cost, energy)
        out["F"] = np.array([
            [-sim.oee, sim.cost, sim.energy_per_unit] 
            for sim in simulations
        ])
        
        # Constraints (g <= 0 format)
        out["G"] = np.array([
            [0.95 - sim.quality, baseline_throughput * 0.9 - sim.throughput]
            for sim in simulations
        ])

def optimize_parameters(
    objectives: list[str],
    constraints: dict,
    eval_window: str = "7d_sliding"
) -> list[Recommendation]:
    """
    Multi-objective optimization using NSGA-II for Pareto front
    """
    # Initial sampling with Latin Hypercube
    from pymoo.operators.sampling.lhs import LHS
    sampling = LHS()
    
    # Configure NSGA-II algorithm
    algorithm = NSGA2(
        pop_size=40,
        sampling=sampling,
        eliminate_duplicates=True
    )
    
    # Run optimization
    from pymoo.optimize import minimize
    res = minimize(
        ManufacturingOptimization(),
        algorithm,
        termination=('n_gen', 100),
        seed=42,
        verbose=True
    )
    
    # Get Pareto front solutions
    pareto_front = res.X  # Parameter sets
    pareto_values = res.F  # Objective values
    
    # Select top 3 diverse solutions from Pareto front
    recommendations = select_diverse_solutions(pareto_front, n=3)
    
    # Validate with multiple seeds for confidence
    for rec in recommendations:
        validation_runs = [simulate(rec.params, seed=s) for s in range(10)]
        rec.mean_oee = np.mean([r.oee for r in validation_runs])
        rec.std_oee = np.std([r.oee for r in validation_runs])
        rec.confidence = f"{rec.mean_oee:.1f}% ± {rec.std_oee:.1f}%"
    
    return recommendations
```

**Files to create:**
- `twin/nl_patterns.yaml` - query → action mappings with validation
- `twin/recommendation_engine.py` - multi-objective optimization
- `twin/disambiguation.py` - resolves ambiguous queries

### Phase 5: GraphQL Visualization Layer (Day 4 - Optional)

**Core Concept**: Thin GraphQL layer for type-safe visualization, keeping SQL as the source of truth.

**Benefits of GraphQL Layer:**
- Type safety for frontend developers
- Self-documenting API
- Works seamlessly with visualization libraries (D3, Grafana)
- Auto-generated from ontology to maintain consistency

**Schema with Safety Controls:**
```graphql
type VirtualTwin {
  currentState: TwinState!
  simulate(parameters: ActionableParameters!): SimulationResult!
  recommend(objective: Objective!): [Recommendation!]!
  compare(runIds: [ID!]!): Comparison!
  syncHealth: SyncHealthReport!
}

type SyncHealthReport {
  healthy: Int!
  delayed: Int!
  stale: Int!
  details: [EntitySyncStatus!]!
}

# Depth limit: 3, Complexity limit: 100
# Persisted operations only (hash-pinned)
```

**Files to create:**
- `api/graphql_schema.py` - auto-generated from ontology
- `api/graphql_resolvers.py` - thin wrappers around SQL

### Phase 6: Demo & Validation (Day 5)

**Core Concept**: Demonstrate the complete NIST progression from descriptive to prescriptive.

**Demo Flow - NIST Classification Progression:**

```
=== DESCRIPTIVE (Current State) ===
Query: "Show current performance"
→ Current OEE: 65%
→ Bottleneck: LINE1-FIL
→ Major issue: micro-stops (35% probability)

=== DIAGNOSTIC (Root Cause) ===
Query: "Why is Line 1 underperforming?"
→ Micro-stops 2x higher than Line 2
→ Performance degradation on SKU-2002
→ Night shift operator issues

=== PREDICTIVE (What-If Scenarios) ===
Query: "What if we improved maintenance?"
→ Scenario 1: Reduce micro-stops 30% → OEE: 72%
→ Scenario 2: Better operators → OEE: 70%
→ Scenario 3: Upgrade materials → OEE: 68%

=== PRESCRIPTIVE (Optimization) ===
Query: "Optimize for maximum OEE with quality >= 95%"
→ Recommendation 1: Adjust 3 parameters
  - micro_stop_probability: 0.15
  - performance_factor: 0.90
  - scrap_multiplier: 1.2
→ Expected OEE: 82% ± 2.1%
→ Financial impact: +$65K/week
→ ROI: 3-week payback
```

**Cost Model with Probabilistic Financial Validation:**
```python
COST_MODEL = {
    "energy_per_kwh": 0.12,
    "scrap_cost_per_unit": 0.35,
    "micro_stop_cost_per_min": 25.00,
    "labor_cost_per_hour": 35.00
}

def calculate_probabilistic_roi(baseline, optimized, n_simulations=1000):
    """
    Monte Carlo simulation for ROI with uncertainty quantification
    """
    roi_samples = []
    
    for _ in range(n_simulations):
        # Add uncertainty to KPI improvements
        oee_delta = np.random.normal(
            optimized.oee - baseline.oee,
            std=2.0  # 2% standard deviation
        )
        
        # Sample from cost distributions
        energy_cost = np.random.normal(0.12, 0.02)
        scrap_cost = np.random.normal(0.35, 0.05)
        
        # Calculate savings with uncertainty
        weekly_savings = calculate_financial_impact_stochastic(
            baseline, optimized, oee_delta, energy_cost, scrap_cost
        )
        
        # Implementation cost with uncertainty
        implementation_cost = np.random.normal(
            estimate_changes_cost(parameter_deltas),
            std=5000  # $5K standard deviation
        )
        
        # Calculate ROI metrics
        if weekly_savings > 0:
            payback_weeks = implementation_cost / weekly_savings
            annual_benefit = weekly_savings * 52
            npv_3year = calculate_npv_stochastic(
                weekly_savings, implementation_cost, 
                discount_rate=np.random.normal(0.08, 0.01)
            )
        else:
            payback_weeks = np.inf
            annual_benefit = weekly_savings * 52
            npv_3year = -implementation_cost
        
        roi_samples.append({
            "weekly_savings": weekly_savings,
            "payback_weeks": payback_weeks,
            "annual_benefit": annual_benefit,
            "npv_3year": npv_3year
        })
    
    # Calculate statistics
    roi_df = pd.DataFrame(roi_samples)
    
    return {
        "weekly_savings": {
            "mean": roi_df["weekly_savings"].mean(),
            "std": roi_df["weekly_savings"].std(),
            "p5": roi_df["weekly_savings"].quantile(0.05),
            "p95": roi_df["weekly_savings"].quantile(0.95)
        },
        "payback_weeks": {
            "mean": roi_df[roi_df["payback_weeks"] < np.inf]["payback_weeks"].mean(),
            "std": roi_df[roi_df["payback_weeks"] < np.inf]["payback_weeks"].std(),
            "p5": roi_df["payback_weeks"].quantile(0.05),
            "p95": roi_df["payback_weeks"].quantile(0.95)
        },
        "annual_benefit": {
            "mean": roi_df["annual_benefit"].mean(),
            "std": roi_df["annual_benefit"].std(),
            "confidence_interval": (
                roi_df["annual_benefit"].quantile(0.025),
                roi_df["annual_benefit"].quantile(0.975)
            )
        },
        "npv_3year": {
            "mean": roi_df["npv_3year"].mean(),
            "std": roi_df["npv_3year"].std(),
            "probability_positive": (roi_df["npv_3year"] > 0).mean()
        }
    }
```

**Files to create:**
- `twin/demo_scenarios.py` - showcase conversations
- `twin/cost_impact_calculator.py` - financial validation
- `docs/TWIN_PROOF.md` - standards compliance documentation

## Key Simplifications

- **Perfect 5-min data** - No real sync complexity, using deterministic generator
- **Simple run tracking** - No event sourcing or bi-temporal model
- **5 actionable parameters** - Not 50+ config options
- **GraphQL for viz only** - SQL remains core, GraphQL is optional
- **Natural language primary** - Claude Code is the interface

## Success Metrics

The POC succeeds if it can:
- ✅ Answer: "What's the financial impact of reducing micro-stops by 30%?"
- ✅ Recommend: "Best parameters for maximizing OEE" with Pareto trade-offs
- ✅ Explain: "Why Line 2 outperforms Line 1"
- ✅ Validate: Show reproducible results with confidence intervals
- ✅ Demonstrate: All interactions through conversational natural language
- ✅ Compute: Probabilistic ROI via Monte Carlo (e.g., "$45K ± $5K weekly savings")

## Technical Stack

- **Core**: Python, SQLite, existing virtual ontology
- **Simulation**: Modified mes_data_generation.py with ActionableParameters
- **Optimization**: pymoo for Pareto multi-objective (NSGA-II); NumPy for Monte Carlo
- **Standards**: SOSA/SSN for sensors, QUDT for units (full URIs)
- **GraphQL**: Strawberry or Graphene (optional)
- **Visualization**: matplotlib/plotly for demos

## Deliverables

1. **twin_ontology_spec.yaml** - SOSA/QUDT compliant ontology with full URIs
2. **actionable_parameters.py** - The 5 dials with bounds and causality
3. **simulation_runner.py** - Deterministic simulation with provenance
4. **recommendation_engine.py** - Multi-objective Pareto optimization (pymoo/NSGA-II)
5. **line_coupling_model.py** - Explicit cascade logic with probabilistic elements
6. **sync_health_dashboard.py** - Visible synchronization monitoring
7. **cost_impact_calculator.py** - Probabilistic financial validation with Monte Carlo ROI
8. **TWIN_PROOF.md** - Standards mapping with citations

## Timeline

- **Day 1**: Twin ontology with QUDT/SOSA sensors
- **Day 2**: Actionable parameters and simulation runner
- **Day 3**: Natural language patterns and optimization
- **Day 4**: GraphQL layer (optional)
- **Day 5**: Demo scenarios and validation

## Next Steps

1. Review and approve this integrated plan
2. Create twin_ontology_spec.yaml with proper QUDT URIs
3. Build actionable_parameters.py with causal models
4. Modify data generator for parameter overlays
5. Implement simulation runner with full provenance
6. Create demo showing NIST progression

## Why This Approach Works

This implementation delivers a legitimate virtual twin that:
- **Meets standards** without unnecessary complexity (full QUDT URIs, SOSA compliance)
- **Provides value** through actionable Pareto-optimal recommendations
- **Maintains simplicity** with SQL-first architecture
- **Enables interaction** through natural language
- **Proves impact** with probabilistic financial validation (Monte Carlo ROI)

The key insight: Claude Code as a natural language REPL makes the virtual twin accessible to operators without requiring SQL knowledge, while the semantic layer ensures queries are interpreted correctly and simulations are reproducible.

This stays true to the virtual ontology vision while adding the rigor needed for a production-ready virtual twin.