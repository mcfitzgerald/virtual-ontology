# Twin Model Quick Reference

## Overview

Twin Model is an **ontology-driven simulation framework** built on SimPy that simulates manufacturing production lines using a unique three-file architecture that enforces separation of concerns.

## Core Architecture: The Three-File System

### 1. Ontology File (What CAN exist)
Defines equipment types and their rules:
```yaml
tbox:
  types:
    FillingStation:
      maps_to:
        framework_primitive: "EquipmentFlow"
      relationships:
        can_connect_to: ["PackingStation"]
```

### 2. Manifest File (What DOES exist)
Declares actual equipment instances:
```yaml
equipment:
  LINE1-FIL:
    type: "FillingStation"
    line_id: "LINE1"
    position: 10
    
connections:
  - from: "LINE1-SOURCE"
    to: "LINE1-FIL"
```

### 3. Config File (HOW it behaves)
Sets operational parameters:
```yaml
equipment_parameters:
  LINE1-FIL:
    nominal_rate: 50.0      # units/minute
    quality_rate: 0.95      # 95% good products
    mtbf: 120.0            # minutes between failures
    mttr: 10.0             # minutes to repair
```

## Key Components

### Flow Primitives
Equipment types map to three base primitives:

| Primitive | Purpose | Key Features |
|-----------|---------|--------------|
| **SourceFlow** | Generate material | Continuous or order-driven production |
| **EquipmentFlow** | Process material | Buffers, quality, failures, changeovers |
| **SinkFlow** | Collect products | OEE calculation, metrics tracking |

### Material Flow
- **Container-based**: Uses SimPy Containers for continuous flow (NOT discrete units)
- **Rate-based**: Equipment processes at units/minute rates
- **No artificial batching**: Material flows continuously without waiting for batch sizes
- **State tracking**: IDLE, FLOWING, STARVED, BLOCKED, FAILED

### Time Units
**Everything is in MINUTES** - rates, durations, MTBF, MTTR, simulation time

## Built-in Features

### MES Data Collection
- **MESDataCollector**: Captures data at 5-minute intervals
- **Equipment scope**: Only core production equipment (FIL, PCK, PAL)
- **Event transduction**: Converts simulation events to MES records
- **OEE calculation**: Availability × Performance × Quality
- **CSV export**: Standard MES format output (9 equipment × 12 intervals = 108 rows for 60-min simulation)

### Production Scheduling
- **ProductionOrder**: Defines what/when/how much to produce
- **ProductManifest**: Product specifications and changeover rules
- **Schedulers**:
  - SequentialScheduler: FIFO processing
  - CampaignOptimizer: Groups similar products
  - ProductionScheduler: Multi-line coordination

### Observable Events
All equipment emits events for monitoring:
- `state_change`: Equipment state transitions
- `flow_processed`: Material processing
- `buffer_level`: Buffer changes
- `failure_start/end`: Equipment failures
- `changeover_start/end`: Product changes

## Important Distinctions

### Production Orders vs Removed Batch Processing

| Aspect | Production Orders (CURRENT) | Batch Processing (REMOVED) |
|--------|---------------------------|--------------------------|
| Purpose | Schedule what to produce | Force batch-size processing |
| Impact | Defines target volumes over time | Created artificial bottlenecks |
| Processing | Continuous flow at rates | Waited for minimum batch sizes |
| Result | Efficient production | Limited to 8% of target |

**Key Point**: Production orders are for SCHEDULING (what/when), not HOW material flows (always continuous).

## Simulation Runner Script

### Purpose
Orchestrates complete production simulations with all required components.

### Required Inputs
All five YAML files must be provided:
1. **Ontology**: Equipment type definitions
2. **Manifest**: Equipment instances and connections
3. **Config**: Operational parameters
4. **Product Manifest**: Product specifications
5. **Production Orders**: What to produce when

### Usage
```bash
poetry run python run_twin_simulation.py \
  --ontology ontology/filling_line_ontology.yaml \
  --manifest manifests/equipment_manifest.yaml \
  --config config/tunable_parameters.yaml \
  --product-manifest config/product_manifest.yaml \
  --production-orders config/production_orders.yaml \
  --duration 1440 \                    # 24 hours in minutes
  --mes-output mes_data.csv \          # Optional MES export
  --report-interval 60                 # Report every hour
```

### How It Works

1. **Load & Validate**: Checks all 5 YAML files exist
2. **Build Model**: Creates equipment using OntologyModelBuilder
3. **Load Orders**: Parses production orders from YAML
4. **Connect Sources**: Links orders to source equipment by line_id
5. **Setup MES**: Optional data collection for metrics
6. **Run Simulation**: Executes for specified duration with periodic reports
7. **Export Results**: Final metrics and optional MES CSV

### Output

#### Progress Reports (every interval)
```
SIMULATION TIME: 60.0 minutes (1.0 hours)
LINE1:
  Total Production: 2850 units
  Production Rate: 47.5 units/min
  Line OEE: 71.3%
  States: SOURCE:FLOWING -> FIL:FLOWING -> PCK:FLOWING -> SINK:FLOWING
```

#### Final Summary
- Total production by line
- OEE breakdown (Availability, Performance, Quality)
- Per-equipment OEE metrics
- MES CSV with 5-minute interval data (108 rows for 9 equipment over 60 minutes)

### Key Features
- **No optimization**: Orders run exactly as specified (no campaign grouping)
- **Sequential execution**: Orders processed in the order they appear
- **Multi-line support**: Automatically routes orders to correct line
- **Real-time metrics**: Continuous OEE and production tracking

## Common Patterns

### Running a Basic Simulation
```python
import simpy
from twin_model import OntologyModelBuilder

env = simpy.Environment()
builder = OntologyModelBuilder(
    env=env,
    ontology_path="ontology.yaml",
    manifest_path="manifest.yaml", 
    config_path="config.yaml"
)

model = builder.build_model()
env.run(until=480)  # 8 hours
metrics = builder.get_metrics()
```

### Adding Production Orders
```python
from twin_model.scheduling import ProductionOrder

order = ProductionOrder(
    order_id="ORD-001",
    product_id="SKU-1001",
    product_name="8oz Water",
    target_volume=10000,
    line_id="LINE1",
    scheduled_start=0,
    scheduled_duration=240  # 4 hours
)

source = model['primitives']['LINE1-SOURCE']
source.add_order(order)
```

### Collecting MES Data
```python
from twin_model.transduction import MESDataCollector

mes_collector = MESDataCollector(
    env=env,
    product_manifest_path="product_manifest.yaml"
)

# Register only core production equipment
for eq_id, equipment in model['primitives'].items():
    # Skip buffers, sources, and sinks
    if 'BUF' in eq_id or 'SOURCE' in eq_id or 'SINK' in eq_id:
        continue
    # Register FIL, PCK, PAL equipment
    if any(equip_type in eq_id for equip_type in ['-FIL', '-PCK', '-PAL']):
        mes_collector.register_equipment(
            equipment_id=eq_id,
            equipment=equipment,
            equipment_type=equipment.__class__.__name__,
            line_id=eq_id.split('-')[0]
        )

# Start collection process
env.process(mes_collector.collect_data())

env.run(until=1440)  # 24 hours

# Force final collection and export
mes_collector.collect_current_data()
mes_collector.save_to_csv("mes_data.csv")
```

## Tips & Best Practices

1. **Time Units**: Always use minutes consistently
2. **Rates**: Define as units/minute, not units/hour
3. **Production Orders**: Use for scheduling, not for forcing batch behavior
4. **Parameter Tuning**: Start with baseline config, adjust incrementally
5. **OEE Targets**: 
   - World-class: 85%+
   - Good: 60-75%
   - Baseline: 45-55%
6. **Bottleneck Detection**: Look for equipment frequently in BLOCKED state
7. **Starvation Issues**: Check upstream generation rates
8. **MES Collection**: 5-minute intervals balance detail vs performance
   - Core equipment only (FIL, PCK, PAL) - not buffers/sources/sinks
   - Expected rows: (# equipment) × (duration÷5 + 1) - e.g., 9×12=108 for 60 minutes

## Troubleshooting

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| No production | Orders not connected to sources | Check line_id mapping |
| Low OEE | High failure rates or low performance | Adjust MTBF/MTTR and performance_factor |
| Equipment STARVED | Upstream too slow | Increase upstream rates |
| Equipment BLOCKED | Downstream bottleneck | Identify and optimize bottleneck |
| Orders not starting | Wrong scheduled_start time | Ensure times are in simulation minutes |

## Key Differences from Traditional Simulators

1. **Ontology-Driven**: Structure defined separately from parameters
2. **Continuous Flow**: No artificial batch constraints
3. **Container-Based**: SimPy Containers, not discrete events
4. **Observable Pattern**: All events can be monitored
5. **Three-File Separation**: Clean separation of concerns
6. **YAML Configuration**: No hardcoded values