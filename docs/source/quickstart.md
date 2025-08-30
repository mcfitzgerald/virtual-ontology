# Quick Start Guide

## Installation

Ensure you have Python 3.8+ and the required dependencies:

```bash
pip install simpy pydantic pyyaml
```

## Basic Usage

### 1. Simple Simulation

```python
import simpy
from pathlib import Path
from twin_model.model_builder import OntologyDrivenModelBuilder

# Create environment
env = simpy.Environment()

# Build model from ontology
builder = OntologyDrivenModelBuilder(
    env=env,
    ontology_path=Path("ontology/twin_ontology.yaml"),
    manifest_dir=Path("manifests")
)

model = builder.build_model()

# Run simulation
env.run(until=480)  # 8 hours

# Get metrics
for equipment in model.equipment_list:
    print(f"{equipment.name}: OEE = {equipment.oee:.2%}")
```

### 2. With Control System

```python
from twin_model.control.control_manager import ControlManager

# Initialize control manager
control_mgr = ControlManager(
    ontology_path=Path("ontology/twin_ontology.yaml"),
    mappings_path=Path("ontology/control_mappings.yaml")
)

# Apply control settings
control_mgr.set_control("speed_setpoint", 85)
control_mgr.set_control("quality_level", 2)

# Build model with controls
builder = OntologyDrivenModelBuilder(
    env=env,
    ontology_path=Path("ontology/twin_ontology.yaml"),
    manifest_dir=Path("manifests"),
    control_manager=control_mgr
)
```

### 3. Production Orders

```python
from twin_model.primitives.scheduler import ProductionOrder, Product, ProductCategory

# Create product
product = Product(
    product_id="PROD001",
    category=ProductCategory.A,
    family="automotive",
    cycle_time=30.0,
    quality_rate=0.98
)

# Create production order
order = ProductionOrder(
    order_id="ORD001",
    product=product,
    quantity=1000,
    due_date=960,  # Due at end of 2 shifts
    priority=1
)

# Add to scheduler
scheduler = model.get_scheduler()
scheduler.add_order(order)
```

## Configuration Files

### Ontology (ontology/twin_ontology.yaml)

Defines equipment types and behaviors:

```yaml
Equipment:
  properties:
    cycle_time:
      type: float
      default: 60.0
    mtbf:
      type: float
      default: 1000.0
```

### Manifest (manifests/plant_manifest.yaml)

Specifies equipment instances:

```yaml
equipment:
  - id: "LATHE_001"
    type: "Lathe"
    properties:
      cycle_time: 45.0
      quality_rate: 0.99
```

### Control Mappings (ontology/control_mappings.yaml)

Maps controls to effects:

```yaml
speed_setpoint:
  parameters:
    - name: cycle_time
      effect_type: inverse_linear
      magnitude: 0.5
```

## Common Patterns

### Monitoring Equipment Status

```python
def monitor_equipment(env, equipment):
    while True:
        yield env.timeout(60)  # Check every minute
        print(f"{env.now}: {equipment.name} - State: {equipment.state}")
        print(f"  Processed: {equipment.parts_produced}")
        print(f"  OEE: {equipment.oee:.2%}")

env.process(monitor_equipment(env, model.equipment_list[0]))
```

### Custom Failure Patterns

```python
equipment.failure_rate_multiplier = 2.0  # Double failure rate
equipment.repair_time_multiplier = 0.5   # Faster repairs
```

### Changeover Management

```python
source = model.get_source()
source.changeover_duration = 45.0  # Minutes
source.smed_level = 1  # Apply SMED reduction
```