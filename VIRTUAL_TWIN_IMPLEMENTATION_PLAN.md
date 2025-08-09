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

## Implementation Phases

### Phase 1: Twin Ontology & Sensors (Day 1)

**Files to create/modify:**
- `ontology/twin_ontology_spec.yaml` - extends base with:
  - Virtual sensors (throughput, quality, power, flow, vibration, temperature)
  - SOSA mappings (Equipment→Platform, Sensor→embedded, Event→Observation)
  - QUDT units for all measurements
  - Synchronization metadata (simplified)

**Virtual Sensor Architecture:**
```yaml
virtual_sensors:
  Equipment:
    embeds:
      # Production sensors
      - ThroughputSensor:
          observes: ["units_per_minute", "actual_vs_target_rate"]
          unit: "units/min"
      
      # Quality sensors  
      - QualityInspector:
          observes: ["defect_rate", "scrap_ratio"]
          unit: "percentage"
      
      # Efficiency sensors
      - PowerMeter:
          observes: ["energy_per_unit", "idle_power"]
          unit: "kWh"
      
      # Flow sensors
      - MaterialFlowSensor:
          observes: ["input_rate", "buffer_level"]
          unit: "units"
      
      # Diagnostic sensors
      - VibrationSensor:
          observes: ["vibration_level"]  # proxy for mechanical health
          unit: "mm/s"
      
      - TemperatureSensor:
          observes: ["operating_temp"]  # affects quality
          unit: "celsius"
```

### Phase 2: Actionable Parameters Module (Day 1-2)

**Files to create:**
- `twin/actionable_parameters.py` - defines the 5 tunable dials:
  ```python
  class ActionableParameters:
      micro_stop_probability: float  # 0.05-0.50 (maintenance quality)
      performance_factor: float      # 0.50-1.00 (operator skill)
      scrap_multiplier: float       # 1.0-5.0 (quality procedures)
      material_reliability: float   # 0.50-1.00 (supply chain)
      cascade_sensitivity: float    # 0.0-1.0 (line coupling)
  ```

- `twin/config_transformer.py` - maps parameters to mes_data_config.json

**Modify:**
- `synthetic_data_generator/mes_data_generation.py` - accept ActionableParameters overlay

**Parameter Meanings (as proxies for real improvements):**
1. **Micro-stop Probability** - Proxy for equipment maintenance quality and operator vigilance
2. **Performance Factor** - Proxy for operator skill level and equipment calibration
3. **Scrap Multiplier** - Proxy for quality control procedures and material handling
4. **Material Reliability** - Proxy for supply chain coordination and buffer management
5. **Cascade Sensitivity** - Proxy for line coupling strength and buffer capacity

### Phase 3: Simulation Runner (Day 2)

**Files to create:**
- `twin/simulation_runner.py`:
  - Wraps data generator with parameter overlays
  - Tracks simulation lineage (baseline → sim → results)
  - Ensures deterministic seeding
  - Returns KPI deltas

- `twin/twin_state.py`:
  - Simple state tracking (run_id, timestamp, config_delta, kpis)
  - No bi-temporal complexity
  ```python
  # Simple state layer
  twin_runs(
      run_id,           # unique identifier
      run_type,         # 'baseline' | 'simulation' | 'recommendation'
      timestamp,        # when generated
      config_delta,     # what changed from baseline
      parent_run_id,    # reference to baseline
      kpi_summary       # aggregated results
  )
  ```

### Phase 4: Natural Language Patterns (Day 3)

**Files to create:**
- `twin/nl_patterns.yaml` - maps queries to operations:
  ```yaml
  patterns:
    - query: "reduce micro-stops by {percent}%"
      action: "adjust micro_stop_probability"
      
    - query: "optimize for {objective}"
      action: "run_optimization"
      
    - query: "what if we had better {aspect}"
      action: "simulate_improvement"
      
    - query: "find the bottleneck when running {product}"
      action: "analyze_product_performance"
      
    - query: "simulate a skilled operator on {shift}"
      action: "adjust_operator_parameters"
  ```

- `twin/recommendation_engine.py`:
  - Bayesian optimization over 5 parameters
  - Multi-objective (OEE vs cost vs energy)
  - Returns top 3 recommendations with confidence

**Example Natural Language Interactions:**
```python
# How Claude Code would interpret twin queries:

"What's the impact of better maintenance?"
→ reduce micro_stop_probability by 50%
→ run simulation
→ compare OEE

"Optimize for energy efficiency"
→ explore: speed vs power consumption
→ constraint: maintain quality > 95%
→ recommend: optimal throughput rate

"Why is Line 2 outperforming others?"
→ query: comparative cascade analysis
→ identify: lower micro-stop probability
→ suggest: replicate maintenance practices

"Simulate a skilled operator on night shift"
→ set operator_issues_probability = 0.02
→ run 2-week simulation
→ calculate ROI of training program

"Find the bottleneck when running energy drinks"
→ filter: product = 'SKU-2002'
→ aggregate: performance by equipment
→ identify: LINE1-FIL at 65% efficiency
```

### Phase 5: GraphQL Visualization Layer (Day 4)

**Files to create:**
- `api/graphql_schema.py` - auto-generated from ontology:
  ```graphql
  type VirtualTwin {
    currentState: TwinState!
    simulate(parameters: ActionableParameters!): SimulationResult!
    recommend(objective: Objective!): [Recommendation!]!
    compare(runIds: [ID!]!): Comparison!
  }
  
  type Equipment {
    id: String!
    type: EquipmentType!
    line: ProductionLine!
    currentOEE: Float
    observations(last: Int): [Observation!]
  }
  
  type SimulationRun {
    id: String!
    configDelta: JSON!
    kpis: KPISet!
    recommendations: [Recommendation!]
  }
  ```

- `api/graphql_resolvers.py`:
  - Thin wrappers around SQL queries
  - Calls simulation_runner for mutations
  - Real-time KPI aggregation
  - No new business logic - just visualization

**Benefits of GraphQL Layer:**
- Type safety for frontend developers
- Self-documenting API
- Works great with visualization libraries (D3, Grafana)
- Keeps SQL as source of truth

### Phase 6: Demo & Validation (Day 5)

**Files to create:**
- `twin/demo_scenarios.py` - showcase conversations:
  1. "What's our current bottleneck?" → semantic query
  2. "What if we improved maintenance?" → simulation
  3. "Optimize for cost while maintaining quality" → recommendation
  4. "Compare last 3 simulations" → visualization

- `docs/TWIN_PROOF.md`:
  - Map to ISO 23247 requirements
  - Show representation (ontology), sync (5-min), interaction (simulate/recommend)
  - Include screenshots of natural language interactions
  - Demonstrate KPI improvements from recommendations

**Demo Flow:**
```
1. Baseline Analysis
   → Current OEE: 65%
   → Bottleneck: LINE1-FIL
   → Major issue: micro-stops

2. Simulation
   → "What if we reduced micro-stops by 40%?"
   → Simulated OEE: 78%
   → Financial impact: +$45K/week

3. Optimization
   → "Find optimal parameters for maximum OEE"
   → Recommendation: adjust 3 parameters
   → Expected improvement: 82% OEE

4. Validation
   → Compare baseline vs simulation vs optimal
   → Show confidence intervals
   → Calculate ROI
```

## Key Simplifications

- **Perfect 5-min data** - No real sync complexity, deterministic generator
- **Simple run tracking** - No event sourcing or bi-temporal model
- **5 actionable parameters** - Not 50+ config options
- **GraphQL for viz only** - SQL remains core, GraphQL is optional
- **Natural language primary** - Claude Code is the interface

## Success Metrics

The POC succeeds if it can:
- Answer: "What's the financial impact of reducing micro-stops by 30%?"
- Recommend: "Best parameters for maximizing OEE"
- Explain: "Why Line 2 outperforms Line 1"
- Demonstrate: All interactions through conversational natural language

## What Makes This a True Virtual Twin

1. **Digital Representation**: Full ontology with sensors and units (SOSA/QUDT)
2. **Synchronization**: 5-min updates with state tracking
3. **Interaction**: Simulate → Recommend → Validate loop
4. **Natural Language**: Claude Code as the conversational interface

## Technical Stack

- **Core**: Python, SQLite, existing virtual ontology
- **Simulation**: Modified mes_data_generation.py
- **Optimization**: scikit-optimize for Bayesian optimization
- **GraphQL**: Strawberry or Graphene (optional)
- **Visualization**: Simple matplotlib/plotly for demos

## Timeline

- **Day 1**: Twin ontology and virtual sensors
- **Day 2**: Actionable parameters and simulation runner
- **Day 3**: Natural language patterns and recommendations
- **Day 4**: GraphQL layer (optional)
- **Day 5**: Demo scenarios and validation

## Next Steps

1. Review and approve this plan
2. Create twin_ontology_spec.yaml extending the base
3. Build actionable_parameters.py module
4. Modify data generator for parameter overlays
5. Implement simulation runner with state tracking
6. Create demo scenarios showing value

This approach stays true to the virtual ontology vision while adding legitimate virtual twin capabilities that can be queried conversationally through Claude Code.