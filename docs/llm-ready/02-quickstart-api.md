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
4. **Apply Parameters** - Sets operational parameters from config
5. **Wire Connections** - Connects equipment using shared SimPy containers
6. **Start Processes** - Initializes all SimPy processes

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
# Create a production order
order = ProductionOrder(
    order_id="ORD-001",
    product_id="SKU-1001", 
    target_volume=1000.0,
    due_time=120.0,
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
if not source.continuous_mode:
    order = ProductionOrder(
        order_id="ORD-2025-001",
        product_id="SKU-1001",
        target_volume=1000,
        due_time=120,
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
from twin_model.scheduling import ProductionScheduler, CampaignOptimizer
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.integration import MESIntegration
from twin_model.transduction import MESCollector

# Load product manifest and orders
manifest = ProductManifest("config/product_manifest.yaml")
scheduler = CampaignOptimizer(
    manifest=manifest,
    campaign_size=50,
    optimization_strategy="minimize_changeovers"
)

# Load and schedule production orders
scheduler.load_orders("config/production_orders.yaml")
scheduled_orders = scheduler.optimize()

# Setup MES integration
mes_collector = MESCollector(env)
mes_integration = MESIntegration(
    collector=mes_collector,
    output_path="mes_output.csv"
)

# Connect to model
for equip_id, equipment in model['primitives'].items():
    equipment.observable.subscribe(mes_collector)

# Run with scheduled orders
for order in scheduled_orders:
    line_source = model['primitives'][f"{order.line_id}-SOURCE"]
    line_source.add_order(order)

env.run(until=1440)  # 24 hours

# Export MES data
mes_records = mes_integration.get_records()
mes_integration.export_to_csv()
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