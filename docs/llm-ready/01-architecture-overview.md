# Twin Model - Ontology-Driven Architecture Guide

## Overview

The Twin Model is a unique simulation framework that uses an **ontology-driven architecture** to separate concerns and enable flexible, maintainable simulations. Unlike traditional simulation frameworks where structure and parameters are mixed, Twin Model enforces a clean separation of:

1. **Structure** (Ontology) - What CAN exist
2. **Instances** (Manifest) - What DOES exist  
3. **Parameters** (Config) - HOW it behaves
4. **Scheduling** (MES Integration) - WHEN production happens
5. **Products** (Product Manifest) - WHAT is produced

## Core Concepts

### The Three-File System

The Twin Model requires three YAML files to build a simulation:

```
ontology.yaml    →  Defines types and relationships
manifest.yaml    →  Declares equipment instances
config.yaml      →  Sets operational parameters
     ↓                        ↓
     └────────────────────────┘
                 ↓
         OntologyModelBuilder
                 ↓
         Simulation Model
```

### Why This Architecture?

1. **Reusability**: One ontology can support many different configurations
2. **Validation**: Manifest is validated against ontology constraints
3. **Flexibility**: Parameters can be tuned without changing structure
4. **Clarity**: Clear separation between "what", "which", and "how"

## The Ontology File

The ontology defines the vocabulary and rules for your simulation domain.

### Structure

```yaml
metadata:
  name: "Your Ontology Name"
  version: "1.0.0"
  description: "Description of the domain"

tbox:  # Terminology Box - Type definitions
  types:
    EquipmentType:
      extends: "ParentType"  # Optional inheritance
      maps_to:
        framework_primitive: "EquipmentFlow"  # Maps to twin_model primitive
      properties:
        required: ["property1", "property2"]
        optional: ["property3"]
      relationships:
        can_connect_to: ["OtherType1", "OtherType2"]
        requires: ["SupportType"]

rbox:  # Rules Box - Business rules and constraints
  rules:
    - name: "rule_name"
      type: "constraint"
      applies_to: ["EquipmentType"]
      condition: "Description of rule"

context:  # Domain context and metadata
  domain: "manufacturing"
  scope: "production_line"
```

### Key Concepts

#### Type Mapping
Each equipment type maps to a framework primitive:
- `SourceFlow` - Material generation
- `EquipmentFlow` - Processing equipment
- `SinkFlow` - Product collection

#### Inheritance
Types can extend other types, inheriting their properties and relationships:
```yaml
FillingStation:
  extends: "ProcessingEquipment"
  maps_to:
    framework_primitive: "EquipmentFlow"
```

#### Relationships
Define valid connections between equipment:
```yaml
relationships:
  can_connect_to: ["PackingStation", "QualityControl"]
```

## The Manifest File

The manifest declares actual equipment instances and their connections.

### Structure

```yaml
metadata:
  name: "Equipment Instances"
  version: "1.0.0"

equipment:
  EQUIPMENT_ID:
    type: "EquipmentType"  # Must be defined in ontology
    line_id: "LINE1"       # Production line assignment
    position: 10           # Position in line (for ordering)
    properties:            # Instance-specific properties
      location: "Building A"

connections:
  - from: "SOURCE_ID"
    to: "EQUIPMENT_ID"
  - from: "EQUIPMENT_ID"
    to: "SINK_ID"
```

### Validation Rules

1. Equipment `type` must exist in ontology
2. Connections must follow ontology relationships
3. Required properties must be provided
4. Line and position are structural requirements

## The Configuration File

The configuration contains all tunable parameters.

### Structure

```yaml
metadata:
  name: "Simulation Parameters"
  version: "1.0.0"

defaults:
  equipment:
    nominal_rate: 50.0
    quality_rate: 0.95
    performance_factor: 0.85

equipment_parameters:
  EQUIPMENT_ID:
    nominal_rate: 60.0       # Override default
    quality_rate: 0.98
    mtbf: 120.0             # Mean time between failures
    mttr: 10.0              # Mean time to repair
    batch_size: 10.0
    processing_interval: 0.1

flow_capacity:
  defaults:
    max_input_rate: 100.0
    max_output_rate: 100.0
    internal_capacity: 500.0
  equipment:
    EQUIPMENT_ID:
      internal_capacity: 1000.0  # Override default
```

### Parameter Categories

1. **Processing Parameters**
   - `nominal_rate` - Units per minute
   - `quality_rate` - Fraction of good output (0-1)
   - `performance_factor` - Actual vs nominal (0-1)
   - `batch_size` - Minimum processing batch

2. **Failure Parameters**
   - `mtbf` - Mean time between failures (minutes)
   - `mttr` - Mean time to repair (minutes)
   - `micro_stop_rate` - Micro-stops per hour
   - `micro_stop_duration` - Average stop duration (seconds)

3. **Flow Capacity**
   - `max_input_rate` - Maximum input units/minute
   - `max_output_rate` - Maximum output units/minute
   - `internal_capacity` - Buffer size (units)
   - `initial_level` - Starting material level

## The OntologyModelBuilder

The `OntologyModelBuilder` class orchestrates the entire process:

### Process Flow

1. **Load Files**: Read ontology, manifest, and config YAML files
2. **Validate**: Check manifest against ontology constraints
3. **Create Equipment**: Instantiate primitives based on types
4. **Apply Parameters**: Set operational parameters from config
5. **Wire Connections**: Connect equipment using shared buffers
6. **Start Processes**: Initialize SimPy processes

### Usage Example

```python
from twin_model import OntologyModelBuilder
import simpy
from pathlib import Path

# Create environment
env = simpy.Environment()

# Define file paths
ontology_path = Path("ontology/production_line.yaml")
manifest_path = Path("manifests/line1_equipment.yaml")
config_path = Path("config/operational_params.yaml")

# Build model
builder = OntologyModelBuilder(
    env=env,
    ontology_path=ontology_path,
    manifest_path=manifest_path,
    config_path=config_path
)

# Generate simulation model
model = builder.build_model()

# Access components
primitives = model['primitives']  # Equipment instances
lines = model['lines']            # Equipment by production line

# Run simulation
env.run(until=60)  # Run for 60 minutes

# Get metrics
metrics = builder.get_metrics()
```

## Benefits of Ontology-Driven Design

### 1. Separation of Concerns
- **Ontology**: Domain expert defines what's possible
- **Manifest**: Engineer declares what exists
- **Config**: Operator tunes how it runs

### 2. Validation and Consistency
- Type checking ensures valid equipment
- Connection validation prevents invalid topologies
- Parameter validation catches configuration errors

### 3. Reusability
- One ontology supports multiple factories
- Manifests can be generated programmatically
- Configs can be optimized without structural changes

### 4. Maintainability
- Changes to types affect all instances
- New equipment types don't break existing configs
- Parameters can be version-controlled separately

### 5. Documentation
- Ontology serves as domain documentation
- Manifest documents actual installation
- Config documents operational settings

## Example: Filling Line

### Ontology Definition
```yaml
FillingStation:
  extends: "ProcessingEquipment"
  maps_to:
    framework_primitive: "EquipmentFlow"
  relationships:
    can_connect_to: ["PackingStation", "QualityControl"]
```

### Manifest Instance
```yaml
LINE1-FIL:
  type: "FillingStation"
  line_id: "LINE1"
  position: 10
```

### Configuration Parameters
```yaml
LINE1-FIL:
  nominal_rate: 50.0
  quality_rate: 0.95
  batch_size: 10.0
  mtbf: 120.0
```

### Result
The OntologyModelBuilder creates an `EquipmentFlow` primitive with the specified parameters, validates connections, and integrates it into the simulation.

## MES Integration Layer

### Production Scheduling
The Twin Model now includes a comprehensive MES (Manufacturing Execution System) integration layer that manages production scheduling and execution:

```yaml
# scheduler_config.yaml
scheduler:
  type: "CampaignOptimizer"
  campaign_size: 50
  optimization_strategy: "minimize_changeovers"
  
# production_orders.yaml  
orders:
  - order_id: "ORD-001"
    product_id: "ProductA"
    quantity: 1000
    priority: 1
    line_id: "LINE1"
```

### Key Components

1. **Production Scheduler** (`twin_model/scheduling/`)
   - `ProductionScheduler`: Multi-line production scheduling
   - `CampaignOptimizer`: Groups similar products to minimize changeovers
   - `SequentialScheduler`: Simple FIFO scheduling
   - `CostCalculator`: Changeover cost optimization

2. **Product Manifest** (`config/product_manifest.yaml`)
   - Defines 30+ products with specifications
   - Product families and allergen groups
   - Target rates and quality parameters
   - Changeover compatibility matrix

3. **MES Integration** (`twin_model/integration/`)
   - Real-time data collection
   - Event transduction to MES records
   - Performance metrics aggregation
   - OEE calculation and tracking

### Scheduling Flow

```
Production Orders → Scheduler → Equipment → MES Collector
                        ↓           ↓            ↓
                   Optimization  Execution   Metrics
```

## Best Practices

1. **Keep Ontologies Stable**: Changes affect all dependent systems
2. **Version Everything**: Use semantic versioning for all three files
3. **Document Constraints**: Use comments in YAML files
4. **Validate Early**: Check files before running simulations
5. **Separate Environments**: Different configs for dev/test/prod

## Troubleshooting

### Common Issues

1. **"Equipment type not defined in ontology"**
   - Check spelling in manifest
   - Ensure type exists in ontology

2. **"Invalid connection"**
   - Check `can_connect_to` relationships
   - Verify equipment IDs exist

3. **"Missing required parameter"**
   - Check config file for equipment ID
   - Verify parameter names match

4. **"No material flow"**
   - Check connections are properly wired
   - Verify processing parameters are reasonable
   - Ensure batch_size < internal_capacity

## Advanced Topics

### Custom Validators
Implement custom validation rules in the ontology:
```yaml
rbox:
  rules:
    - name: "quality_check_required"
      applies_to: ["FillingStation"]
      condition: "Must connect to QualityControl before Packaging"
```

### Dynamic Configuration
Load configurations at runtime:
```python
# Load different configs for different scenarios
if scenario == "high_volume":
    config_path = Path("config/high_volume.yaml")
else:
    config_path = Path("config/standard.yaml")
```

### Ontology Evolution
Handle ontology versioning:
```yaml
metadata:
  version: "2.0.0"
  compatible_with: ["1.8", "1.9"]
  breaking_changes:
    - "Removed DeprecatedType"
    - "Changed FillingStation relationships"
```

## Summary

The Twin Model's ontology-driven architecture provides a powerful, flexible framework for building simulations. By separating structure, instances, and parameters, it enables:

- Clear domain modeling
- Robust validation
- Easy configuration management
- Scalable simulation development

This architecture is particularly valuable for:
- Multi-site deployments with similar equipment
- Scenario testing with different configurations
- Long-term maintenance of simulation models
- Collaboration between domain experts and developers
## Flow Control Components

### Buffer Flow Management

The Twin Model includes sophisticated buffer management for material flow control between equipment.

#### AccumulationBuffer Architecture

The `AccumulationBuffer` class provides inter-equipment flow management with several key features:

```
Upstream Equipment → [AccumulationBuffer] → Downstream Equipment
                            ↓
                    - Capacity Management
                    - Overflow Detection
                    - Underflow Detection
                    - Dwell Time Tracking
```

**Key Design Principles:**
- **Inheritance**: AccumulationBuffer extends BaseFlowPrimitive for consistency
- **Container Sharing**: Uses SimPy containers for seamless flow integration
- **State Tracking**: Monitors buffer levels and flow states
- **Event-Driven**: Emits observables for monitoring

**Buffer Modes:**
- **FIFO** (First-In-First-Out): Standard queue behavior
- **FILO** (First-In-Last-Out): Stack behavior for specific processes

### V-Curve Speed Control

The V-curve controller implements Theory of Constraints (TOC) principles for optimal line speed management.

#### Theory of Constraints Implementation

```
        Constraint (Bottleneck)
               ↓
    ┌──────────┼──────────┐
    ↓          ↓          ↓
Upstream   Constraint  Downstream
(+20%)      (100%)      (+15%)
```

**Control Strategy:**
1. **Identify Constraint**: Find the bottleneck equipment
2. **Protect Constraint**: Prevent starvation and blocking
3. **Speed Differential**: Run non-constraints faster
4. **Monitor Performance**: Track protection metrics

**Control Modes:**
- **Fixed Constraint**: Pre-defined bottleneck that doesn't change
- **Dynamic Constraint**: Automatically identifies bottleneck based on utilization

#### Speed Calculation Algorithm

```python
# Pseudo-code for V-curve speed calculation
if equipment.position < constraint.position:
    # Upstream: prevent starvation
    speed = nominal * (1 + upstream_differential)
elif equipment.position > constraint.position:
    # Downstream: prevent blocking
    speed = nominal * (1 + downstream_differential)
else:
    # Constraint: run at nominal
    speed = nominal
```

### State Duration Tracking

A critical aspect of the architecture is accurate state duration tracking for OEE calculations.

#### State Tracking Fix

The recent architecture improvement addresses a critical bug where equipment state durations weren't properly tracked:

**Problem**: Equipment repeatedly called `change_state()` with the same state, preventing duration accumulation.

**Solution**: Check current state before calling `change_state()`:
```python
if self.current_state != FlowState.FLOWING:
    self.change_state(FlowState.FLOWING)
```

**Impact**: 
- Accurate availability calculations
- Correct OEE metrics
- Reliable performance monitoring

#### MES Integration Enhancement

The MES collector now properly captures current state duration:
```python
# Include time in current state when capturing metrics
time_in_current_state = env.now - equipment.last_state_change
state_durations[current_state] += time_in_current_state
```

## Production Scheduling Architecture

### Schedule Generation Strategy

The schedule generator creates production orders with various optimization strategies:

```
Product Manifest → Schedule Generator → Production Orders
                          ↓
                  Optimization Strategy:
                  - Minimize Changeovers
                  - Group Product Families
                  - Balance Line Utilization
```

### Sub-Optimal Baseline Generation

For testing and improvement opportunities, the system can generate deliberately sub-optimal schedules:

**Sub-Optimal Characteristics:**
- Random product sequencing
- Short batch sizes (2-6 hours)
- Excessive changeovers (>15% of time)
- Poor family grouping
- Misaligned line assignments

This creates a baseline with 45-55% OEE, providing clear improvement opportunities.

## Data Flow Architecture

### Continuous Flow Simulation

The system uses SimPy containers for continuous material flow:

```
Source → Container → Equipment → Container → Equipment → Container → Sink
           ↑                         ↑                         ↑
      Flow Control            Buffer Management         Quality Tracking
```

**Key Principles:**
- **No Batch Constraints**: Material flows continuously at configured rates
- **Container-Based**: Uses SimPy's Container primitive for flow
- **Rate-Based Processing**: Equipment processes at units/minute rates
- **Real-Time Metrics**: Continuous tracking of throughput and quality

### Event Observable Pattern

All flow primitives emit observable events for monitoring:

```python
Observable Events:
- state_change: Equipment state transitions
- flow_processed: Material processing events
- buffer_level: Buffer fill level changes
- failure_start/end: Equipment failure events
- changeover_start/end: Product changeover events
```

## Integration Points

### MES Data Collection

The MES collector integrates with equipment through standard interfaces:

1. **Registration**: Equipment registers with collector
2. **Interval Collection**: 5-minute data intervals
3. **Metric Aggregation**: Calculate OEE components
4. **CSV Export**: Standard MES format output

### Configuration Integration

All components integrate through the three-file system:

```
Ontology Definition → Manifest Instance → Config Parameters
         ↓                    ↓                  ↓
    Type System          Equipment          Operational
    Validation           Topology           Settings
         ↓                    ↓                  ↓
         └────────────────────┴──────────────────┘
                             ↓
                    Integrated Simulation
```

## Performance Considerations

### State Management Optimization

- Avoid redundant state changes
- Cache frequently accessed metrics
- Use event-driven updates vs polling

### Buffer Sizing Guidelines

- Pre-constraint: 3-5 minutes of production
- Post-constraint: 2-3 minutes of production
- Between equipment: 1-2 minutes of production

### V-Curve Tuning

- Upstream differential: 15-25% (typically 20%)
- Downstream differential: 10-20% (typically 15%)
- Update interval: 5-10 minutes
- Speed limits: 80-150% of nominal

