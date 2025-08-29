# Twin Model Clean Refactor Plan

> **STATUS: ✅ COMPLETED (August 2024)**  
> This refactor plan has been successfully implemented through Phases 1-7.  
> See TWIN_ARCHITECTURE.md for current system documentation.

## Executive Summary
Complete refactor of the twin model to implement an ontology-driven virtual twin that bridges MES data analysis to optimization via LLM orchestration. This plan establishes a clean architecture with proper material flow, realistic control abstractions, and clear extensibility patterns.

## Core Philosophy & Goals

### Ultimate Vision
Enable manufacturing optimization using existing MES data without massive digital twin investment by:
1. Using ontologies as the semantic bridge between MES data and virtual twin
2. Allowing LLMs to discover patterns and optimize through simulation
3. Providing actionable recommendations in real-world terms

### Key Principles
- **Ontology-First**: The twin ontology IS the model - it defines what exists
- **Two-Layer Control**: Separate actionable controls from simulation parameters
- **Discovery-Oriented**: LLM discovers correlations, not prescriptive mappings
- **No Hardcoding**: Everything configuration-driven via ontology/manifests
- **Clean Architecture**: Internal queues only, no hybrid modes

## Background & Context

### The Problem We're Solving
In real-world manufacturing, companies have rich MES data but lack digital twins. This POC demonstrates how to:
- Build a virtual twin from existing MES data using ontologies
- Use LLMs for reasoning and orchestration across the system
- Generate baseline (realistically poor) performance data for optimization
- Discover improvement opportunities through simulation

### Why Ontologies?
The dual-ontology approach enables:
- **MES Ontology**: Natural language to SQL for data analysis
- **Twin Ontology**: Defines simulation structure and controls
- **LLM Bridge**: Semantic understanding for both analysis and simulation
- **Low Overhead**: No massive investment in traditional digital twin systems

## Phase 1: Ontology Definition (Day 1)

### 1.1 Create New Twin Ontology
**File**: `ontology/twin_ontology_v2.yaml`

#### Core Structure
```yaml
entities:
  Equipment:
    - No separate Buffer class
    - Internal queues (part of equipment)
    - Direct equipment-to-equipment connections
  Source:
    - Order-driven generation
    - Feeds first equipment's input queue
  Sink:
    - Collects from last equipment
  Products:
    - Different characteristics per SKU
  Orders:
    - Production schedule
```

### 1.2 Define Actionable Controls
Based on research, implement controls that plant managers actually use:

```yaml
actionable_controls:
  # Changeover Management
  changeover_reduction_level:
    description: "SMED implementation (0=none, 1=basic, 2=advanced)"
    real_world: "Quick changeover techniques, duplicate jigs"
    affects:
      changeover_duration: [-30%, -50%]
    
  # Operator Competency
  operator_training_hours:
    description: "Monthly training hours per operator"
    real_world: "SOP training, problem-solving, equipment familiarity"
    affects:
      micro_stop_recovery_time: -20%
      scrap_rate: -15%
      performance_factor: +10%
    
  # Line Speed Policy
  line_speed_setting:
    description: "Percentage of theoretical maximum"
    real_world: "Balance between volume and quality"
    affects:
      base_rate: direct
      scrap_rate: +2% per 10% increase
      micro_stop_frequency: +1.5% per 10% increase
    
  # Sensor Maintenance
  sensor_calibration_frequency:
    description: "Days between calibrations"
    real_world: "Clean sensors, adjust triggers"
    affects:
      micro_stop_probability: exponential after 7 days
      false_reject_rate: increases with drift
    
  # Production Scheduling
  product_sequencing_strategy:
    description: "How products are sequenced"
    real_world: "Group similar products, minimize changeovers"
    options:
      - random
      - changeover_optimized
      - campaign_mode
    
  # Preventive Maintenance
  pm_schedule_compliance:
    description: "Percentage of PM completed on time"
    real_world: "Bearing lubrication, belt tension, parts replacement"
    affects:
      mtbf: +30% at 100%
      major_failure_probability: -50% at 100%
```

### 1.3 Define Simulation Parameters
Internal parameters that respond to controls:

```yaml
simulation_parameters:
  # Derived from actionable controls
  micro_stop_probability:
    base_value: 0.3  # per 5 minutes
    modifiers:
      - sensor_drift_factor
      - line_speed_factor
      - operator_skill_factor
    
  performance_factor:
    base_value: 0.85
    modifiers:
      - operator_training_effect
      - shift_performance
      - equipment_wear
    
  scrap_rate:
    base_value: 0.05
    modifiers:
      - line_speed_quality_tradeoff
      - operator_experience
      - product_complexity
```

### 1.4 Observable Patterns
What emerges from simulation:

```yaml
observable_patterns:
  bottleneck_location:
    emerges_from: "Rate mismatches between equipment"
    
  starvation_patterns:
    emerges_from: "Queue dynamics and production rates"
    
  quality_cascades:
    emerges_from: "Upstream problems affecting downstream"
    
  shift_variations:
    emerges_from: "Parameter combinations per shift"
```

## Phase 2: Core Infrastructure (Day 2)

### 2.1 Model Builder Refactor
**File**: `twin_model/model_builder.py`

Key changes:
- Remove ALL buffer wiring logic
- Implement `_wire_internal_queue_mode()`
- Direct equipment-to-equipment connections
- Source → First Equipment input queue
- Last Equipment → Sink

### 2.2 Equipment Primitive Updates
**File**: `twin_model/primitives/equipment.py`

Required changes:
```python
# Remove
- self.upstream buffer checking
- self.downstream buffer feeding
- hybrid mode logic

# Keep/Add
+ self.input_queue = simpy.Store(env, capacity=20)
+ self.output_queue = simpy.Store(env, capacity=20)
+ connect_to(next_equipment) method
+ Only check internal queues for material
```

### 2.3 Source/Sink Updates
**Files**: `twin_model/primitives/source.py`, `twin_model/primitives/sink.py`

Changes:
- Source puts directly into equipment.input_queue
- Immediate t=0 order release
- Initial WIP configuration support
- Sink pulls from last equipment.output_queue

## Phase 3: Control Implementation (Day 3)

### 3.1 Control Manager
**New File**: `twin_model/control/control_manager.py`

Responsibilities:
- Load actionable controls from ontology
- Apply control → parameter mappings
- Validate control bounds
- Enable runtime adjustments

### 3.2 Realistic Failure Modeling
Based on research findings:

```yaml
failure_distribution:
  micro_stops:
    percentage: 80%
    causes:
      - jams_at_handoffs: 40%
      - sensor_trips: 25%
      - minor_adjustments: 15%
    duration: 0.5-3 minutes
    
  minor_failures:
    percentage: 15%
    causes:
      - component_issues: 10%
      - calibration_drift: 5%
    duration: 5-30 minutes
    
  major_failures:
    percentage: 5%
    causes:
      - equipment_breakdown: 3%
      - critical_component: 2%
    duration: 30+ minutes
```

### 3.3 Production Scheduling Enhancement
Implement realistic scheduling:
- Changeover matrices (product-to-product times)
- Campaign production support
- Shift-specific product assignment
- ABC analysis for prioritization

## Phase 4: Integration & Testing (Day 4)

### 4.1 End-to-End Flow Testing
**File**: `twin_model/tests/test_material_flow.py`

Test cases:
- Order flows from scheduler → source → equipment → sink
- No immediate starvation at startup
- Proper state transitions
- Queue levels remain reasonable

### 4.2 Control Testing
**File**: `twin_model/tests/test_controls.py`

Test cases:
- Each actionable control affects parameters correctly
- Bounds are enforced
- Combinations work as expected
- No hardcoded values

### 4.3 KPI Validation
**File**: `twin_model/tests/test_kpi_targets.py`

Validate:
- OEE ~60% achievable
- Availability ~60%
- Performance ~85%
- Quality ~95%

## Phase 5: MES Integration Prep (Day 5)

### 5.1 Transduction Layer
**File**: `twin_model/transduction/mes_transducer.py`

Updates:
- Generate realistic MES records
- Include failure reasons
- Add shift patterns
- Implement noise/variation

### 5.2 LLM Interface Documentation
Create clear documentation for LLM understanding:
- Control descriptions
- Effect explanations
- Discovery hints
- Recommendation templates

### 5.3 Validation Suite
Comprehensive testing:
- pytest for unit tests
- mypy for type checking
- ruff for style
- semgrep for hardcode detection

## Technical Implementation Details

### Directory Structure
```
twin_model/
├── ontology/
│   ├── twin_ontology_v2.yaml      # Clean ontology
│   ├── control_mappings.yaml      # Control → parameter
│   └── observable_patterns.yaml   # Emergent behaviors
├── primitives/
│   ├── base.py                    # Base primitive
│   ├── equipment.py               # Internal queues only
│   ├── source.py                  # Order-driven
│   ├── sink.py                    # Collection point
│   ├── scheduler.py               # Order management
│   └── monitor.py                 # KPI tracking
├── control/
│   ├── __init__.py
│   ├── actionable_controls.py     # Plant manager controls
│   ├── control_manager.py         # Mapping engine
│   └── parameter_effects.py       # Simulation parameters
├── model_builder.py               # Clean, no buffers
├── config.py                      # Configuration loader
└── tests/
    ├── test_material_flow.py
    ├── test_controls.py
    ├── test_kpi_targets.py
    └── test_integration.py
```

### Configuration Architecture
```yaml
# manifests/system_config.yaml
system:
  material_flow: "internal_queues"  # Only option now
  startup:
    warmup_period: 5.0
    initial_wip: true
    
# manifests/control_settings.yaml  
controls:
  changeover_reduction_level: 1
  operator_training_hours: 20
  line_speed_setting: 85
  sensor_calibration_frequency: 7
  product_sequencing_strategy: "changeover_optimized"
  pm_schedule_compliance: 80
```

## Success Criteria

### Phase Gates
Each phase must meet criteria before proceeding:

**Phase 1**: Ontology complete and reviewed
**Phase 2**: Material flows without errors
**Phase 3**: Controls affect simulation correctly
**Phase 4**: All tests passing
**Phase 5**: Can generate realistic MES data

### Final Validation
- [ ] 60% OEE achievable with realistic parameters
- [ ] No starvation/blocking oscillations
- [ ] Actionable recommendations generated
- [ ] Clear control → effect relationships
- [ ] System is extensible for new controls
- [ ] No hardcoded values (passes semgrep)
- [ ] Passes mypy and ruff checks
- [ ] Comprehensive test coverage

## Risk Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Material flow bugs | High | Test incrementally, simple cases first |
| Parameter tuning | Medium | Use industry benchmarks as guide |
| Performance issues | Low | Profile if needed, optimize later |

### Process Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Strict phase gates, clear priorities |
| Lost context | Medium | Document decisions in code |
| Over-engineering | Medium | Start simple, add only as needed |

## Extension Guidelines

### Adding New Actionable Control
1. Define in `twin_ontology_v2.yaml`:
   ```yaml
   new_control_name:
     description: "What it does"
     real_world: "How it's implemented"
     affects: {parameter: effect}
   ```
2. Add mapping in `control_mappings.yaml`
3. Model builder automatically interprets
4. Test with simulation
5. Document for LLM

### Modifying Line Configuration
1. Update `equipment_manifest.yaml`
2. Adjust equipment connections if needed
3. Recalibrate parameters
4. Run validation tests
5. Update documentation

### Adding New Observable
1. Define in ontology what causes it
2. Add emission in primitive
3. Include in transduction
4. Document pattern for LLM discovery

## Dependencies & Tools

### Required Libraries
- SimPy (discrete event simulation)
- PyYAML (configuration)
- NumPy (distributions)
- pytest (testing)
- mypy (type checking)
- ruff (linting)
- semgrep (hardcode detection)

### Development Tools
- poetry (package management)
- git (version control)
- Context7 MCP (documentation lookup)

## Timeline & Milestones

| Day | Phase | Deliverable | Success Metric |
|-----|-------|-------------|----------------|
| 1 | Ontology | twin_ontology_v2.yaml | Reviewed & approved |
| 2 | Infrastructure | Core primitives | Material flows |
| 3 | Controls | Control system | Parameters respond |
| 4 | Testing | Test suite | All tests pass |
| 5 | Integration | MES transduction | Realistic data generated |

## Next Steps

1. **Immediate**: Save this plan and create ontology
2. **Today**: Complete Phase 1 (ontology definition)
3. **Tomorrow**: Begin Phase 2 (core infrastructure)
4. **This Week**: Achieve working simulation
5. **Next Week**: Integrate with MES analysis

## References

### Industry Standards
- OEE World Class: 85% (we target 60% for realistic baseline)
- Micro-stops: 80% of all stops
- Changeover best practice: Under 10 minutes (SMED)

### Research Sources
- Filling line micro-stop causes and solutions
- OEE improvement strategies
- Plant manager actionable controls
- SimPy best practices for production lines

### Internal Documentation
- Original prototype (main branch README)
- TWIN_MODEL_STATUS_REPORT.md
- Previous implementation attempts

---

*Document Version: 1.0*
*Created: 2024*
*Purpose: Guide clean refactor of twin model with proper architecture*