# Twin Model API Documentation

## Quick Start - The Three-File Pathway

The Twin Model uses an **ontology-driven architecture** that requires three YAML files to build a simulation:

```python
from twin_model import OntologyModelBuilder
import simpy

# 1. Create SimPy environment
env = simpy.Environment()

# 2. Define the three required files
ontology_path = "ontology/filling_line_ontology.yaml"  # Structure & types
manifest_path = "manifests/equipment_manifest.yaml"    # Equipment instances
config_path = "config/tunable_parameters.yaml"         # Parameters

# 3. Build the model using OntologyModelBuilder
builder = OntologyModelBuilder(
    env=env,
    ontology_path=ontology_path,
    manifest_path=manifest_path,
    config_path=config_path
)

# 4. Generate the simulation model
model = builder.build_model()

# 5. Run the simulation
env.run(until=60)  # Run for 60 minutes

# 6. Get metrics
metrics = builder.get_metrics()
for equipment_id, equipment_metrics in metrics.items():
    print(f"{equipment_id}: OEE={equipment_metrics.get('oee', 0):.1%}")
```

## Core Components

### OntologyModelBuilder

The central class that orchestrates model building from the three configuration files:

**Constructor:**
```python
OntologyModelBuilder(
    env: simpy.Environment,
    ontology_path: Path,  # Path to ontology YAML
    manifest_path: Path,  # Path to manifest YAML
    config_path: Path     # Path to config YAML
)
```

**Key Methods:**
- `build_model() -> Dict[str, Any]` - Builds complete simulation model
- `get_metrics() -> Dict[str, Any]` - Returns current metrics from all equipment

**Model Building Process:**
1. **Load Files** - Reads and parses the three YAML files
2. **Validate** - Checks manifest against ontology constraints
3. **Create Primitives** - Instantiates flow primitives based on equipment types
4. **Apply Parameters** - Sets operational parameters from config using explicit None checking
5. **Wire Connections** - Connects equipment using shared SimPy containers
6. **Start Processes** - Initializes all SimPy processes

**Parameter Resolution:**

The builder resolves parameters using a four-tier hierarchy with explicit `None` checking to properly handle zero and small values:

1. Equipment-specific parameters (`equipment_parameters.LINE1-FIL.nominal_rate`)
2. Type defaults (`defaults.equipment.nominal_rate`)
3. Flow capacity defaults (`defaults.flow_capacity.equipment.max_input_rate`)
4. Hardcoded fallbacks (last resort)

**Critical:** As of v2.0, zero and small configuration values (e.g., `nominal_rate: 0.01`) are properly honored instead of falling through to defaults. The `_get_param()` helper method uses explicit `if value is not None` checks rather than relying on Python's truthiness evaluation.

### Flow Primitives

#### BaseFlowPrimitive
Abstract base class for all flow primitives:
- Manages flow state (IDLE, FLOWING, STARVED, BLOCKED, FAILED)
- Tracks metrics (input, output, scrap, downtime)
- Provides OEE calculation methods
- Emits observable events

#### SourceFlow
Generates material into the system:
- **Continuous Mode**: Generates material continuously at specified rate
- **Order Mode**: Processes ProductionOrder objects with priorities
- Key parameters: `generation_rate`, `generation_interval`

```python
from twin_model.scheduling import ProductionOrder

# Create a production order
order = ProductionOrder(
    order_id="ORD-001",
    product_id="SKU-1001",
    product_name="Product A",
    target_volume=1000.0,
    line_id="LINE1",
    scheduled_start=0.0,
    scheduled_duration=120.0,
    priority=5
)

# Add to source
source.add_order(order)
```

#### EquipmentFlow
Processes material with realistic constraints:
- Internal buffer for work-in-progress
- Quality losses (scrap generation)
- Performance factors
- Failure modeling (MTBF/MTTR)
- Micro-stops simulation
- Product changeover support

Key parameters via `ProcessingParameters`:
- `nominal_rate` - Maximum processing rate
- `quality_rate` - Fraction of good output
- `performance_factor` - Actual vs nominal performance
- `batch_size` - Minimum processing batch

#### SinkFlow
Collects finished products and calculates metrics:
- Tracks production windows
- Calculates OEE (Availability × Performance × Quality)
- Maintains production history
- Aggregates metrics from upstream equipment
- **NEW**: `get_metrics()` method returns comprehensive metrics including OEE

#### AccumulationBuffer (NEW)
Provides inter-equipment flow management:
- **FIFO/FILO operation modes** - First-in-first-out or last-in-first-out
- **Dynamic capacity management** - Handles overflow and underflow
- **Dwell time tracking** - Monitors material residence time
- **Flow rate constraints** - Configurable input/output rates

```python
from twin_model.primitives.buffer_flow import AccumulationBuffer, BufferParameters

# Create buffer parameters
buffer_params = BufferParameters(
    mode="FIFO",
    warning_level_low=0.2,  # 20% warning level
    warning_level_high=0.8,  # 80% warning level
    max_dwell_time=60.0  # Maximum 60 minute dwell time
)

# Create and connect buffer
buffer = AccumulationBuffer(env, config, flow_capacity, buffer_params)
buffer.connect(upstream_equipment, downstream_equipment)
buffer.start()
```

### Data Classes

#### FlowCapacity
Defines flow constraints:
- `max_input_rate` - Maximum input flow rate
- `max_output_rate` - Maximum output flow rate
- `internal_capacity` - Buffer capacity
- `initial_level` - Starting material level

#### ProcessingParameters
Equipment processing configuration:
- `nominal_rate` - Design processing rate
- `quality_rate` - Quality percentage (0-1)
- `performance_factor` - Performance factor (0-1)
- `batch_size` - Minimum batch size
- `processing_interval` - Time between processing attempts

#### FailureParameters
Failure and maintenance parameters:
- `mtbf` - Mean time between failures (minutes)
- `mttr` - Mean time to repair (minutes)
- `micro_stop_rate` - Micro-stops per hour
- `micro_stop_duration` - Average micro-stop duration (seconds)

#### ProductionOrder
Production order for material generation:
- `order_id` - Unique order identifier
- `product_id` - Product to produce
- `target_volume` - Total volume to produce
- `due_time` - Order due time
- `priority` - Order priority (higher = more urgent)
- `completed_volume` - Tracks progress

### Monitoring

#### FlowMonitor
Real-time monitoring and bottleneck detection:
- Tracks equipment states and throughput
- Identifies bottlenecks and their severity
- Maintains historical snapshots
- Calculates line-level metrics

```python
monitor = FlowMonitor(env, monitoring_interval=1.0)
monitor.register_primitives(model['primitives'])
monitor.start()
```

## Configuration Files Structure

### Ontology (Structure Definition)
```yaml
tbox:
  types:
    EquipmentType:
      maps_to:
        framework_primitive: "EquipmentFlow"
      required_properties: [...]
      relationships:
        can_connect_to: [...]
```

### Manifest (Equipment Instances)
```yaml
equipment:
  EQUIPMENT_ID:
    type: "EquipmentType"
    line_id: "LINE1"
    position: 10
    
connections:
  - from: "SOURCE_ID"
    to: "EQUIPMENT_ID"
```

### Config (Tunable Parameters)
```yaml
equipment_parameters:
  EQUIPMENT_ID:
    nominal_rate: 50.0
    quality_rate: 0.95
    mtbf: 120.0
    mttr: 10.0
```

## Control Layer (NEW)

### VCurveController
Implements Theory of Constraints speed control:

```python
from twin_model.control.vcurve_controller import VCurveController, VCurveParameters

# Configure V-curve control
vcurve_params = VCurveParameters(
    mode="FIXED_CONSTRAINT",         # or "DYNAMIC_CONSTRAINT"
    constraint_equipment="LINE1-FIL", # Bottleneck equipment
    upstream_differential=0.20,       # 20% faster upstream
    downstream_differential=0.15,     # 15% faster downstream
    update_interval=5.0,              # Update every 5 minutes
    max_speed_multiplier=1.4,
    min_speed_multiplier=0.85
)

# Create and start controller
controller = VCurveController(env, model['primitives'], vcurve_params)
controller.start()

# After simulation, get metrics
metrics = controller.get_metrics()
print(f"Constraint starvation rate: {metrics['constraint_starvation_rate']:.1%}")
print(f"Constraint blocking rate: {metrics['constraint_blocking_rate']:.1%}")
```

## Scheduling Components (ENHANCED)

### SubOptimalScheduleGenerator
Automated production schedule generation:

```python
from twin_model.scheduling.schedule_generator import (
    SubOptimalScheduleGenerator,
    ScheduleGeneratorConfig
)

# Configure schedule generation
config = ScheduleGeneratorConfig(
    sequence_mode="optimized",      # "optimized", "random", "campaign"
    batch_sizing="dynamic",          # "fixed", "dynamic", "economic"
    min_batch_hours=4.0,
    max_batch_hours=12.0,
    changeover_frequency_target=0.15 # Target 15% changeover time
)

# Generate schedule
generator = SubOptimalScheduleGenerator(
    config=config,
    product_manifest_path=Path("manifests/product_manifest.yaml"),
    random_seed=42
)

# Generate 7-day schedule
orders = generator.generate_schedule(
    duration_days=7,
    start_date=datetime(2025, 1, 1)
)

# Dispatch to sources
for order in orders:
    line_source = model['primitives'][f"LINE{order.line_id}-SOURCE"]
    line_source.add_order(order)
```

## Enhanced Methods

### EquipmentFlow.get_metrics() (NEW)
Returns comprehensive equipment metrics:

```python
metrics = equipment.get_metrics()
# Returns:
# {
#     'total_input': 1000.0,
#     'total_output': 950.0,
#     'total_scrap': 50.0,
#     'oee': 0.72,
#     'availability': 0.85,
#     'performance': 0.90,
#     'quality': 0.95,
#     'state': 'FLOWING',
#     'utilization': 0.78
# }
```

### SinkFlow.get_metrics() (NEW)
Returns sink metrics with OEE calculations:

```python
metrics = sink.get_metrics()
# Returns:
# {
#     'total_collected': 5000.0,
#     'current_oee': 0.68,
#     'availability': 0.82,
#     'performance': 0.88,
#     'quality': 0.94,
#     'production_rate': 45.2,
#     'window_metrics': {...}
# }
```

## Complete Example

```python
from pathlib import Path
import simpy
from twin_model import OntologyModelBuilder, ProductionOrder

# Setup
env = simpy.Environment()

# Build model from configuration files
builder = OntologyModelBuilder(
    env=env,
    ontology_path=Path("ontology/filling_line_ontology.yaml"),
    manifest_path=Path("manifests/equipment_manifest.yaml"),
    config_path=Path("config/tunable_parameters.yaml")
)

model = builder.build_model()

# Access specific equipment
source = model['primitives']['LINE1-SOURCE']
equipment = model['primitives']['LINE1-FIL']
sink = model['primitives']['LINE1-SINK']

# Add production orders (if not in continuous mode)
from twin_model.scheduling import ProductionOrder

if not source.continuous_mode:
    order = ProductionOrder(
        order_id="ORD-2025-001",
        product_id="SKU-1001",
        product_name="Product A",
        target_volume=1000,
        line_id="LINE1",
        scheduled_start=0,
        scheduled_duration=120,
        priority=8
    )
    source.add_order(order)

# Run simulation
env.run(until=480)  # 8 hours

# Get results
metrics = builder.get_metrics()
for equip_id, equip_metrics in metrics.items():
    print(f"\n{equip_id}:")
    print(f"  Total Output: {equip_metrics['total_output']:.1f} units")
    print(f"  OEE: {equip_metrics['oee']:.1%}")
    print(f"  - Availability: {equip_metrics['availability']:.1%}")
    print(f"  - Performance: {equip_metrics['performance']:.1%}")
    print(f"  - Quality: {equip_metrics['quality']:.1%}")
```

## MES Integration Example

```python
from twin_model.scheduling import ProductionScheduler
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.transduction.mes_collector import MESDataCollector

# Load product manifest and orders
manifest = ProductManifest(Path("manifests/product_manifest.yaml"))
scheduler = ProductionScheduler(
    manifest=manifest
)

# Load and schedule production orders
scheduler.load_orders("config/production_orders.yaml")
scheduled_orders = scheduler.optimize()

# Setup MES integration
mes_collector = MESDataCollector(env)

# Connect to model
for equip_id, equipment in model['primitives'].items():
    equipment.observable.subscribe(mes_collector)

# Run with scheduled orders
for order in scheduled_orders:
    line_source = model['primitives'][f"{order.line_id}-SOURCE"]
    line_source.add_order(order)

env.run(until=1440)  # 24 hours

# Export MES data
mes_records = mes_collector.get_mes_records()
mes_collector.export_to_csv("mes_output.csv")
print(f"Generated {len(mes_records)} MES records")
```

## Key Design Patterns

1. **Container-Based Flow**: All material flow uses SimPy Containers for continuous simulation
2. **Shared Buffers**: Equipment connected via shared containers (output of one is input of next)
3. **Observable Events**: Equipment emits events for monitoring and control
4. **State Tracking**: Comprehensive state duration tracking for OEE calculation
5. **Ontology Validation**: Manifest validated against ontology constraints

## See Also

- [Ontology-Driven Architecture Guide](01-architecture-overview.md) - Detailed explanation of the three-file system
- [API Reference](03-complete-api-reference.md) - Complete API documentation (auto-generated)
- [Examples](yaml-examples/) - Example configuration files