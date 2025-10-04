# Twin Model Complete User Guide

## Table of Contents
1. [Understanding the System](#part-1-understanding-the-system)
2. [Building Your First Model](#part-2-building-your-first-model)
3. [Advanced Features](#part-3-advanced-features)
4. [Common Patterns](#part-4-common-patterns)
5. [Troubleshooting](#part-5-troubleshooting)
6. [Complete Working Example](#appendix-a-complete-working-example)

---

## Part 1: Understanding the System

### What is Twin Model?

Twin Model is an **ontology-driven simulation framework** built on SimPy that separates simulation concerns into distinct, manageable layers. Unlike traditional simulation tools where structure and parameters are intertwined, Twin Model enforces clean separation of responsibilities.

### The Three-File Architecture

Every Twin Model simulation requires exactly three YAML files:

```
1. Ontology File    →  Defines what CAN exist (types & rules)
2. Manifest File    →  Declares what DOES exist (instances)
3. Config File      →  Controls HOW it behaves (parameters)
```

This separation provides:
- **Reusability**: One ontology supports many configurations
- **Validation**: Manifest is validated against ontology rules
- **Flexibility**: Parameters can be tuned without structural changes
- **Clarity**: Clear separation of concerns

### File Organization

```
your-project/
├── ontology/
│   └── filling_line_ontology.yaml     # Equipment types and rules
├── manifests/
│   ├── equipment_manifest.yaml        # Equipment instances
│   ├── product_manifest.yaml          # Product definitions
│   └── production_orders_manifest.yaml # Production schedule
├── config/
│   └── tunable_parameters.yaml        # All operational parameters
├── run_twin_simulation.py             # Standalone simulation runner
└── output/
    └── test_mes_output.csv            # Simulation results
```

### Key Concepts

1. **Equipment Types** (defined in ontology):
   - `MaterialSource`: Generates material flow
   - `FillingStation`: Fills containers
   - `PackingStation`: Packs filled items
   - `ProductCollection`: Collects finished products

2. **Flow Primitives** (framework implementations):
   - `SourceFlow`: Material generation
   - `EquipmentFlow`: Processing equipment
   - `SinkFlow`: Product collection

3. **Connections**: Equipment connected via SimPy containers (pipes)

---

## Part 2: Building Your First Model

Let's build a simple production line with three stations: filling, packing, and collection.

### Step 1: Create the Ontology

Create `ontology/simple_line_ontology.yaml`:

```yaml
# Simple Production Line Ontology
# Defines the types of equipment that can exist

metadata:
  name: "Simple Production Line Ontology"
  version: "1.0.0"
  description: "Basic production line with filling and packing"
  
tbox:
  types:
    # Material source - generates product flow
    MaterialSource:
      description: "Generates material for production"
      maps_to:
        framework_primitive: "SourceFlow"
      required_properties:
        - generation_rate        # Units per minute
        - generation_interval    # Update frequency (seconds)
        - continuous_mode       # true for continuous generation
      relationships:
        can_connect_to: ["FillingStation"]
    
    # Filling station - first processing step
    FillingStation:
      description: "Fills containers with material"
      maps_to:
        framework_primitive: "EquipmentFlow"
      required_properties:
        - fill_rate            # Units per minute
        - quality_rate         # Fraction of good products (0-1)
        - performance_factor   # Efficiency factor (0-1)
      relationships:
        can_receive_from: ["MaterialSource"]
        can_connect_to: ["PackingStation"]
    
    # Packing station - second processing step
    PackingStation:
      description: "Packs filled containers"
      maps_to:
        framework_primitive: "EquipmentFlow"
      required_properties:
        - pack_size           # Units per pack
        - quality_rate
        - performance_factor
      relationships:
        can_receive_from: ["FillingStation"]
        can_connect_to: ["ProductCollection"]
    
    # Product collection - end point
    ProductCollection:
      description: "Collects finished products"
      maps_to:
        framework_primitive: "SinkFlow"
      required_properties:
        - collection_rate     # Units per minute
        - nominal_rate        # For OEE calculation
      relationships:
        can_receive_from: ["PackingStation"]

rbox:
  rules:
    - name: "line_completeness"
      type: "constraint"
      description: "Each line must have source and sink"
    
    - name: "connection_validity"
      type: "constraint"
      description: "Connections must follow type relationships"
```

### Step 2: Define Equipment Instances

Create `manifests/equipment_manifest.yaml`:

```yaml
# Equipment Manifest
# Declares actual equipment instances and their connections

metadata:
  name: "Simple Line Equipment"
  version: "1.0.0"

equipment:
  # Line 1 Equipment
  LINE1-SOURCE:
    type: "MaterialSource"
    line_id: "LINE1"
    position: 0
    properties:
      location: "Building A"
      
  LINE1-FIL:
    type: "FillingStation"
    line_id: "LINE1"
    position: 10
    properties:
      model: "Filler-3000"
      capacity: 60  # Units/min max
      
  LINE1-PCK:
    type: "PackingStation"
    line_id: "LINE1"
    position: 20
    properties:
      model: "Packer-2000"
      capacity: 55
      
  LINE1-SINK:
    type: "ProductCollection"
    line_id: "LINE1"
    position: 30
    properties:
      storage: "Warehouse 1"

connections:
  - from: "LINE1-SOURCE"
    to: "LINE1-FIL"
    
  - from: "LINE1-FIL"
    to: "LINE1-PCK"
    
  - from: "LINE1-PCK"
    to: "LINE1-SINK"
```

### Step 3: Configure Parameters

Create `config/tunable_parameters.yaml`:

```yaml
# Tunable Parameters
# Controls equipment behavior and performance

metadata:
  name: "Simulation Parameters"
  version: "1.0.0"
  description: "Operational parameters for production line"

# Default values for all equipment
defaults:
  source:
    generation_rate: 60.0      # Units/minute
    generation_interval: 0.01  # Update every 0.01 minutes
    continuous_mode: true
    default_product: "PROD-001"
    
  equipment:
    performance_factor: 0.85   # 85% efficiency
    quality_rate: 0.95        # 95% good products
    processing_interval: 0.01
    mtbf: 120.0              # Mean time between failures (minutes)
    mttr: 10.0               # Mean time to repair (minutes)
    
  sink:
    collection_rate: 50.0
    collection_interval: 0.01
    window_duration: 5.0      # OEE calculation window

# Equipment-specific parameters (override defaults)
equipment_parameters:
  LINE1-SOURCE:
    generation_rate: 55.0     # Slightly below capacity
    continuous_mode: true
    
  LINE1-FIL:
    nominal_rate: 50.0        # Design capacity
    fill_rate: 50.0          # Actual fill rate
    quality_rate: 0.96       # 96% quality
    performance_factor: 0.90  # 90% efficiency
    mtbf: 60.0               # Fails every hour on average
    mttr: 5.0                # 5 minute repairs
    
  LINE1-PCK:
    nominal_rate: 52.0
    pack_size: 12            # 12 units per pack
    quality_rate: 0.94
    performance_factor: 0.88
    mtbf: 90.0
    mttr: 7.0
    
  LINE1-SINK:
    collection_rate: 55.0
    nominal_rate: 50.0       # Expected rate for OEE
```

### Step 4: Run the Simulation

#### Option A: Use the Standalone Runner (Recommended)

The easiest way to run a simulation is using the provided `run_twin_simulation.py`:

```bash
# Run with default 14-day simulation
poetry run python run_twin_simulation.py

# Run for 7 days with debug output
poetry run python run_twin_simulation.py --days 7 --debug

# Run for 30 days
poetry run python run_twin_simulation.py --days 30
```

This standalone runner will:
- Load all configuration from the standard locations
- Process production orders from `manifests/production_orders_manifest.yaml`
- Generate MES output to `test_mes_output.csv`
- Display real-time OEE metrics during the run
- Show final statistics when complete

#### Option B: Create Your Own Simulation Script

Create `simulations/run_simulation.py`:

```python
#!/usr/bin/env python3
"""
Simple production line simulation using Twin Model
"""

import simpy
from pathlib import Path
from twin_model import OntologyModelBuilder

def run_simulation():
    # 1. Create SimPy environment
    env = simpy.Environment()
    
    # 2. Define file paths
    ontology_path = Path("ontology/simple_line_ontology.yaml")
    manifest_path = Path("manifests/equipment_manifest.yaml")
    config_path = Path("config/tunable_parameters.yaml")
    
    # 3. Build the model
    print("Building simulation model...")
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_path=manifest_path,
        config_path=config_path
    )
    
    model = builder.build_model()
    print(f"Model built with {len(model['primitives'])} equipment pieces")
    
    # 4. Run simulation
    simulation_time = 480  # 8 hours (in minutes)
    print(f"\nRunning simulation for {simulation_time} minutes...")
    
    env.run(until=simulation_time)
    
    # 5. Get results
    print("\n=== Simulation Results ===")
    metrics = builder.get_metrics()
    
    for equipment_id, equipment_metrics in metrics.items():
        if equipment_id.endswith('-SINK'):
            # Sink shows overall line performance
            oee = equipment_metrics.get('oee', 0)
            total = equipment_metrics.get('total_consumed', 0)
            print(f"\n{equipment_id}:")
            print(f"  Total Production: {total:.0f} units")
            print(f"  OEE: {oee:.1%}")
        else:
            # Equipment shows individual performance
            state = equipment_metrics.get('state', 'UNKNOWN')
            processed = equipment_metrics.get('total_output', 0)
            scrap = equipment_metrics.get('total_scrap', 0)
            print(f"\n{equipment_id}:")
            print(f"  State: {state}")
            print(f"  Processed: {processed:.0f} units")
            print(f"  Scrap: {scrap:.0f} units")
            print(f"  Yield: {(processed/(processed+scrap) if processed else 0):.1%}")

if __name__ == "__main__":
    run_simulation()
```

### Understanding the Output

When you run the simulation, you'll see:

1. **Equipment States**: IDLE, FLOWING, STARVED, BLOCKED, or FAILED
2. **Production Metrics**: Units processed, scrap generated
3. **OEE (Overall Equipment Effectiveness)**: 
   - Availability = Runtime / Scheduled Time
   - Performance = Actual Rate / Nominal Rate
   - Quality = Good Units / Total Units
   - OEE = Availability × Performance × Quality

---

## Part 3: Advanced Features

### Using Production Orders

Instead of continuous generation, use production orders:

```python
from twin_model.scheduling import ProductionOrder

# Create orders
order1 = ProductionOrder(
    order_id="ORD-001",
    product_id="SKU-1001",
    quantity=1000,
    priority=1,
    due_date="2025-01-15"
)

# Add to source
source = model['primitives']['LINE1-SOURCE']
source.add_order(order1)
```

### MES Integration

Collect manufacturing execution data:

```python
from twin_model.transduction import MESCollector
from twin_model.integration import MESIntegration

# Setup MES collection
mes_collector = MESCollector(env)
mes_integration = MESIntegration(
    collector=mes_collector,
    output_path="mes_output.csv"
)

# Connect to equipment
for equipment_id, equipment in model['primitives'].items():
    equipment.observable.subscribe(mes_collector)

# Run simulation
env.run(until=1440)  # 24 hours

# Export data
mes_integration.export_to_csv()
```

### Campaign Optimization

Optimize production scheduling:

```python
from twin_model.scheduling import CampaignOptimizer
from twin_model.scheduling.product_manifest import ProductManifest

# Load products
manifest = ProductManifest("config/product_manifest.yaml")

# Create optimizer
optimizer = CampaignOptimizer(
    manifest=manifest,
    campaign_size=50,
    optimization_strategy="minimize_changeovers"
)

# Load and optimize orders
optimizer.load_orders("config/production_orders.yaml")
schedule = optimizer.optimize()

# Execute optimized schedule
for order in schedule:
    source = model['primitives'][f"{order.line_id}-SOURCE"]
    source.add_order(order)
```

---

## Part 4: Common Patterns

### Three-Line Factory

Example manifest for multi-line facility:

```yaml
equipment:
  # Line 1 - High speed, standard products
  LINE1-SOURCE:
    type: "MaterialSource"
    line_id: "LINE1"
  LINE1-FIL:
    type: "FillingStation"
    line_id: "LINE1"
  # ... more equipment
  
  # Line 2 - Medium speed, premium products
  LINE2-SOURCE:
    type: "MaterialSource"
    line_id: "LINE2"
  # ... more equipment
  
  # Line 3 - Flexible, specialty products
  LINE3-SOURCE:
    type: "MaterialSource"
    line_id: "LINE3"
  # ... more equipment
```

### Quality Control Loop

Add inspection and rework:

```yaml
tbox:
  types:
    QualityInspection:
      maps_to:
        framework_primitive: "EquipmentFlow"
      properties:
        reject_rate: 0.02  # 2% rejection
      relationships:
        can_connect_to: ["ReworkStation", "ProductCollection"]
    
    ReworkStation:
      maps_to:
        framework_primitive: "EquipmentFlow"
      properties:
        rework_success_rate: 0.90  # 90% successful rework
      relationships:
        can_connect_to: ["QualityInspection"]  # Loop back
```

### Changeover Optimization

Configure product-specific changeover times:

```yaml
# In product_manifest.yaml
products:
  ProductA:
    changeover_group: "A"
    allergen_group: "None"
    
  ProductB:
    changeover_group: "B"
    allergen_group: "Nuts"  # Requires cleaning
```

---

## Part 5: Troubleshooting

### Common Issues and Solutions

#### 1. "Equipment type not found in ontology"

**Error**: `ValidationError: Equipment type 'CustomEquipment' not defined in ontology`

**Solution**: Ensure the equipment type in manifest matches ontology definition exactly:
```yaml
# In ontology
tbox:
  types:
    CustomEquipment:  # Must match exactly
      ...

# In manifest
equipment:
  MY-EQUIPMENT:
    type: "CustomEquipment"  # Must match ontology
```

#### 2. "Invalid connection"

**Error**: `ConnectionError: Cannot connect FillingStation to MaterialSource`

**Solution**: Check relationship rules in ontology:
```yaml
FillingStation:
  relationships:
    can_receive_from: ["MaterialSource"]  # Add this
    can_connect_to: ["PackingStation"]
```

#### 3. Low OEE Values

**Symptoms**: OEE below 50%

**Check**:
1. MTBF/MTTR ratios (availability)
2. Performance factors (too low?)
3. Quality rates (excessive scrap?)
4. Bottlenecks (check BLOCKED states)

#### 4. Equipment Always STARVED

**Cause**: Upstream equipment too slow

**Solutions**:
- Increase upstream generation/processing rates
- Add buffers between equipment
- Balance line rates

#### 5. Memory Issues in Long Simulations

**Solution**: Enable periodic data flushing:
```python
mes_collector.configure(
    buffer_size=1000,     # Smaller buffer
    flush_interval=3600   # Flush hourly
)
```

#### 6. Zero or Small Config Values Not Honored (FIXED in v2.0)

**Previous Issue**: Configuration values like `nominal_rate: 0.01` or `mtbf: 0` would fall through to defaults

**Status**: ✅ Fixed as of v2.0

**Explanation**: The framework now uses explicit `None` checking for parameter resolution. Zero and small values are treated as valid configuration values.

```yaml
# These values are now properly honored:
equipment_parameters:
  TEST-EQUIPMENT:
    nominal_rate: 0.01      # ✅ Will be 0.01
    quality_rate: 0.0       # ✅ Will be 0.0
    mtbf: 0.1              # ✅ Will be 0.1
```

**Note**: Only missing parameters (no key in YAML) fall through to defaults. Explicit zero values are respected.

### Performance Optimization Tips

1. **Reduce update intervals** for faster simulation:
   ```yaml
   processing_interval: 0.1  # Update every 0.1 minutes
   ```

2. **Use appropriate time units** (minutes vs seconds)

3. **Monitor bottlenecks**:
   ```python
   # Check equipment states periodically
   for equip_id, equip in model['primitives'].items():
       if equip.state == "BLOCKED":
           print(f"Bottleneck at {equip_id}")
   ```

4. **Optimize connection topology** - minimize long chains

---

## Appendix A: Complete Working Example

Here's a complete, ready-to-run example:

### Directory Structure
```
twin_model_example/
├── ontology/
│   └── example_ontology.yaml
├── manifests/
│   └── example_manifest.yaml
├── config/
│   └── example_config.yaml
└── run_example.py
```

### example_ontology.yaml
```yaml
metadata:
  name: "Example Production Line"
  version: "1.0.0"

tbox:
  types:
    MaterialSource:
      maps_to:
        framework_primitive: "SourceFlow"
      required_properties:
        - generation_rate
        - continuous_mode
      relationships:
        can_connect_to: ["ProcessingStation"]
    
    ProcessingStation:
      maps_to:
        framework_primitive: "EquipmentFlow"
      required_properties:
        - nominal_rate
        - quality_rate
      relationships:
        can_receive_from: ["MaterialSource", "ProcessingStation"]
        can_connect_to: ["ProcessingStation", "ProductSink"]
    
    ProductSink:
      maps_to:
        framework_primitive: "SinkFlow"
      required_properties:
        - collection_rate
      relationships:
        can_receive_from: ["ProcessingStation"]
```

### example_manifest.yaml
```yaml
metadata:
  name: "Example Equipment"
  version: "1.0.0"

equipment:
  SOURCE-1:
    type: "MaterialSource"
    line_id: "MAIN"
    position: 0
    
  PROC-1:
    type: "ProcessingStation"
    line_id: "MAIN"
    position: 10
    
  PROC-2:
    type: "ProcessingStation"
    line_id: "MAIN"
    position: 20
    
  SINK-1:
    type: "ProductSink"
    line_id: "MAIN"
    position: 30

connections:
  - from: "SOURCE-1"
    to: "PROC-1"
  - from: "PROC-1"
    to: "PROC-2"
  - from: "PROC-2"
    to: "SINK-1"
```

### example_config.yaml
```yaml
metadata:
  name: "Example Configuration"
  version: "1.0.0"

defaults:
  equipment:
    performance_factor: 0.85
    quality_rate: 0.95
    processing_interval: 0.01

equipment_parameters:
  SOURCE-1:
    generation_rate: 100.0
    continuous_mode: true
    generation_interval: 0.01
    
  PROC-1:
    nominal_rate: 95.0
    quality_rate: 0.97
    performance_factor: 0.90
    
  PROC-2:
    nominal_rate: 90.0
    quality_rate: 0.95
    performance_factor: 0.88
    
  SINK-1:
    collection_rate: 100.0
    collection_interval: 0.01
    nominal_rate: 85.0
```

### run_example.py
```python
#!/usr/bin/env python3

import simpy
from pathlib import Path
from twin_model import OntologyModelBuilder

# Setup
env = simpy.Environment()

builder = OntologyModelBuilder(
    env=env,
    ontology_path=Path("ontology/example_ontology.yaml"),
    manifest_path=Path("manifests/example_manifest.yaml"),
    config_path=Path("config/example_config.yaml")
)

# Build and run
model = builder.build_model()
env.run(until=60)  # Run for 1 hour

# Results
metrics = builder.get_metrics()
for equip_id, data in metrics.items():
    print(f"{equip_id}: {data.get('total_output', 0):.0f} units")
```

---

## Appendix B: Quick Reference

### File Types Summary

| File | Purpose | Location | Required |
|------|---------|----------|----------|
| Ontology | Define types & rules | `ontology/*.yaml` | Yes |
| Manifest | Declare instances | `manifests/*.yaml` | Yes |
| Config | Set parameters | `config/*.yaml` | Yes |
| Products | Define products | `config/product_manifest.yaml` | No |
| Orders | Production schedule | `config/production_orders.yaml` | No |

### Key Classes

| Class | Purpose | Module |
|-------|---------|--------|
| `OntologyModelBuilder` | Build simulation | `twin_model` |
| `ProductionOrder` | Define orders | `twin_model.scheduling` |
| `MESCollector` | Collect data | `twin_model.transduction` |
| `CampaignOptimizer` | Optimize schedule | `twin_model.scheduling` |

### Common Parameters

| Parameter | Typical Range | Unit | Notes |
|-----------|--------------|------|-------|
| `nominal_rate` | 10-200 | units/min | Design capacity |
| `quality_rate` | 0.90-0.99 | fraction | Good product ratio |
| `performance_factor` | 0.70-0.95 | fraction | Efficiency |
| `mtbf` | 60-480 | minutes | Reliability |
| `mttr` | 5-30 | minutes | Maintainability |
| `processing_interval` | 0.01-1.0 | minutes | Update frequency |

---

## Next Steps

1. **Start Simple**: Begin with a single-line, 3-equipment model
2. **Add Complexity**: Introduce failures, quality issues, multiple products
3. **Optimize**: Use MES data to identify bottlenecks
4. **Scale**: Add multiple lines and scheduling
5. **Integrate**: Connect to external systems via MES export

For more details, see:
- [Architecture Overview](01-architecture-overview.md)
- [API Reference](03-complete-api-reference.md)
- [MES Integration Guide](04-mes-integration-guide.md)
- [Configuration Reference](05-configuration-reference.md)