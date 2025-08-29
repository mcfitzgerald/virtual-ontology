# Virtual Twin System Usage Guide

## Overview
This guide explains how to use the ontology-driven virtual twin system that bridges MES data analysis to optimization via simulation. The system uses a two-layer control architecture where plant manager actions (actionable controls) affect simulation parameters to discover optimization opportunities.

## System Architecture

### Core Components
```
twin_model/
├── ontology/           # System structure and control definitions
├── manifests/          # Equipment and production configurations
├── primitives/         # SimPy simulation components
├── control/            # Control system and parameter mapping
└── model_builder.py    # Orchestrates model creation
```

## Key Files and Their Purpose

### 1. Ontology Files

#### `ontology/twin_ontology.yaml`
**Purpose**: Defines the virtual twin structure - what exists in the simulation
```yaml
Key sections:
- tbox: Class definitions (Equipment, Source, Sink, etc.)
- rbox: Relationships (feeds_into, part_of_line, etc.) 
- control_system: Two-layer control architecture
- mappings: SimPy primitive mappings
```

**Usage**: This is THE model - it defines all entities and their properties. The model builder reads this to understand what to create.

#### `ontology/control_mappings.yaml`
**Purpose**: Maps actionable controls to simulation parameters
```yaml
Example:
operator_training_hours:
  affects:
    micro_stop_duration: -0.2  # 20% reduction
    performance_factor: +0.1    # 10% improvement
```

### 2. Manifest Files

#### `manifests/equipment_manifest.yaml`
**Purpose**: Concrete equipment instances with specific parameters
```yaml
equipment:
  LINE1-FIL:
    type: Filler
    base_rate: 80  # units/minute
    mtbf: 480      # minutes
    mttr: 30       # minutes
```

#### `manifests/production_manifest.yaml`
**Purpose**: Product definitions and production orders
```yaml
products:
  SKU-1001:
    changeover_group: A
    target_rate: 85
    scrap_rate_normal: 0.05
```

#### `manifests/control_settings.yaml`
**Purpose**: Current control values (what the plant manager sets)
```yaml
controls:
  changeover_reduction_level: 0  # No SMED
  operator_training_hours: 8     # Basic training
  line_speed_setting: 90         # 90% of max
```

#### `manifests/system_config.yaml`
**Purpose**: System-wide configuration
```yaml
system:
  material_flow: internal_queues
  warmup_period: 5.0
  simulation_duration: 480  # 8 hours
```

### 3. Model Builder

#### `twin_model/model_builder.py`
**Purpose**: Reads ontology and manifests to create simulation model

**Key Methods**:
- `build_model()`: Main orchestration
- `_load_manifests()`: Loads equipment and production configs
- `_create_primitives()`: Creates SimPy entities
- `_wire_connections()`: Connects equipment in sequence
- `_apply_controls()`: Sets parameters from control settings

**Usage**:
```python
from twin_model.model_builder import OntologyDrivenModelBuilderV2

builder = ModelBuilderV2(
    env=simpy_env,
    ontology_path="ontology/twin_ontology.yaml",
    manifest_dir="manifests/",
    control_manager=control_mgr
)
model = builder.build_model()
```

### 4. Control System

#### `twin_model/control/control_manager.py`
**Purpose**: Manages the two-layer control system

**Key Functions**:
- `get_control_value(name)`: Get current control setting
- `get_parameter(name)`: Get computed simulation parameter
- `apply_control_effects()`: Update parameters based on controls

**Control Flow**:
```
Plant Manager Sets → Actionable Control → Mapping Function → Simulation Parameter → Equipment Behavior
Example: training_hours=16 → micro_stop_duration×0.8 → faster recovery → higher OEE
```

## How to Use the System

### 1. Basic Simulation Run
```python
import simpy
from twin_model.model_builder import OntologyDrivenModelBuilderV2
from twin_model.control.control_manager import ControlManager

# Setup
env = simpy.Environment()
control_mgr = ControlManager(
    ontology_path="ontology/twin_ontology.yaml",
    mappings_path="ontology/control_mappings.yaml",
    settings_path="manifests/control_settings.yaml"
)

# Build model
builder = ModelBuilderV2(env, "ontology/twin_ontology.yaml", "manifests/", control_mgr)
model = builder.build_model()

# Start processes
for primitive in model['primitives'].values():
    if hasattr(primitive, 'start'):
        primitive.start()

# Run simulation
env.run(until=480)  # 8 hours

# Get results
for line_id, line in model['lines'].items():
    # Calculate OEE, check production, etc.
```

### 2. Modifying Controls
Edit `manifests/control_settings.yaml`:
```yaml
controls:
  changeover_reduction_level: 2  # Implement advanced SMED
  operator_training_hours: 20    # Increase training
  line_speed_setting: 85         # Reduce speed for quality
```

### 3. Adding New Equipment
Edit `manifests/equipment_manifest.yaml`:
```yaml
equipment:
  LINE4-FIL:
    type: Filler
    line_id: LINE4
    position: 1
    base_rate: 100
    mtbf: 600
```

### 4. Creating Production Orders
```python
# Currently disabled - needs implementation
# When enabled, will use production_manifest.yaml orders
```

## Control System Details

### Actionable Controls (What Plant Managers Change)

| Control | Range | Real-World Action | Primary Effect |
|---------|-------|------------------|----------------|
| changeover_reduction_level | 0-2 | SMED implementation | Reduces changeover time |
| operator_training_hours | 0-40 | Monthly training per operator | Improves performance, reduces errors |
| line_speed_setting | 50-100% | % of theoretical max | Trade speed for quality |
| sensor_calibration_frequency | 1-30 days | Maintenance frequency | Reduces micro-stops |
| product_sequencing_strategy | 3 options | How products are ordered | Minimizes changeovers |
| pm_schedule_compliance | 0-100% | Preventive maintenance adherence | Improves MTBF |
| staffing_level | 1-4 | Operators per shift | Affects response time |
| autonomous_maintenance_level | 0-3 | Operator-performed maintenance | Reduces minor stops |

### Simulation Parameters (Internal Model Response)

| Parameter | Base Value | Affected By | Impact |
|-----------|------------|-------------|--------|
| micro_stop_probability | 0.3/5min | sensor_calibration, line_speed | Frequency of brief stops |
| performance_factor | 0.85 | training, staffing | Actual vs theoretical rate |
| scrap_rate | 0.05 | line_speed, training | Quality losses |
| MTBF | 480 min | PM compliance, maintenance | Time between failures |
| MTTR | 30 min | staffing, training | Repair duration |

## Configuration Relationships

```
Ontology (Structure) 
    ↓
Model Builder (Orchestration)
    ↓
Manifests (Instances) + Control Settings (Values)
    ↓
Control Manager (Mapping)
    ↓
Primitives (Simulation)
    ↓
KPIs (OEE, Production, etc.)
```

## Common Tasks

### Check Current OEE
```python
# After simulation run
equipment = model['primitives']['LINE1-FIL']
availability = equipment.state_durations[EquipmentState.RUNNING] / total_time
performance = equipment.units_produced / (running_time * base_rate)
quality = equipment.units_produced / (equipment.units_produced + equipment.units_scrapped)
oee = availability * performance * quality
```

### Modify Line Configuration
1. Edit `manifests/equipment_manifest.yaml` for equipment specs
2. Edit `manifests/system_config.yaml` for system settings
3. Re-run simulation

### Test Control Impact
1. Set baseline in `manifests/control_settings.yaml`
2. Run simulation and record OEE
3. Modify one control
4. Run again and compare

### Debug Issues
- Check logs: `logs/twin_model.log`
- Enable debug mode in primitives
- Add print statements in state transitions
- Verify manifests are loaded correctly

## Current Limitations

### Known Issues
1. **Failures not triggering** - Equipment runs without micro-stops (needs fix)
2. **Order mode disabled** - Sources use continuous generation
3. **No changeover modeling** - Product changes don't cause delays
4. **Low baseline OEE** - Currently 28-37%, target 40-65%

### Not Yet Implemented
- Production order scheduling
- Shift patterns
- Multi-product changeovers
- Dynamic control adjustments
- MES data generation

## Next Steps for Full Functionality

1. **Fix failure generation** to achieve realistic 40-65% baseline OEE
2. **Enable order-driven production** for realistic scheduling
3. **Implement changeover matrices** for product transitions
4. **Complete control mappings** so all controls affect parameters
5. **Add MES transduction** to generate realistic data

## Tips for LLM Integration

When using an LLM to optimize:
1. Provide current control settings and OEE
2. Ask for specific control recommendations
3. Test each recommendation individually
4. Document discovered relationships
5. Use sensitivity analysis to find optimal ranges

## Example Scenarios

### Scenario 1: Baseline Performance
```yaml
# manifests/control_settings.yaml
controls:
  all at default/poor values
Expected OEE: 40-50%
```

### Scenario 2: Quick Wins
```yaml
controls:
  changeover_reduction_level: 1  # Basic SMED
  sensor_calibration_frequency: 7  # Weekly
Expected OEE: 55-65%
```

### Scenario 3: Optimized
```yaml
controls:
  changeover_reduction_level: 2  # Advanced SMED
  operator_training_hours: 30    # High training
  line_speed_setting: 85         # Optimal speed
  pm_schedule_compliance: 95     # Excellent PM
Expected OEE: 70-80%
```

## Support and Documentation

- Main documentation: `README.md`
- Refactor plan: `TWIN_MODEL_REFACTOR_PLAN.md`
- Test examples: `test_full_integration.py`
- Ontology reference: Comments in `twin_ontology.yaml`

---

*For questions or issues, refer to the refactor plan or review the test files for working examples.*