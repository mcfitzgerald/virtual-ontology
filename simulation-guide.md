# Twin Model Simulation Guide

## Overview

This guide explains how to build and run production line simulations using the Twin Model framework. The framework uses an ontology-driven architecture that separates structure (what exists), configuration (how it behaves), and scheduling (when production happens).

## Prerequisites

- Python 3.10+
- Poetry for dependency management
- SimPy simulation library
- Project dependencies installed via `poetry install`

## Core Concepts

### Three-File Architecture

The Twin Model requires three YAML files to define a simulation:

1. **Ontology** (`ontology/*.yaml`) - Defines equipment types and relationships
2. **Manifest** (`manifests/*.yaml`) - Declares actual equipment instances
3. **Configuration** (`config/*.yaml`) - Sets operational parameters

### Flow Primitives

The simulation uses three main primitive types:

- **SourceFlow**: Generates material based on production orders
- **EquipmentFlow**: Processes material (filling, packing, palletizing)
- **SinkFlow**: Collects finished products and calculates metrics

## Step 1: Define Your Ontology

Create an ontology file that defines your equipment types:

```yaml
# ontology/production_line.yaml
metadata:
  name: "Production Line Ontology"
  version: "1.0.0"
  
tbox:
  types:
    MaterialSource:
      maps_to:
        framework_primitive: "SourceFlow"
      properties:
        required: ["generation_rate"]
        
    FillingStation:
      extends: "ProcessingEquipment"
      maps_to:
        framework_primitive: "EquipmentFlow"
      relationships:
        can_connect_to: ["PackingStation"]
        
    PackingStation:
      extends: "ProcessingEquipment"
      maps_to:
        framework_primitive: "EquipmentFlow"
      relationships:
        can_connect_to: ["PalletizingStation"]
        
    PalletizingStation:
      extends: "ProcessingEquipment"
      maps_to:
        framework_primitive: "EquipmentFlow"
      relationships:
        can_connect_to: ["ProductSink"]
        
    ProductSink:
      maps_to:
        framework_primitive: "SinkFlow"
```

## Step 2: Declare Equipment Instances

Create a manifest file declaring your actual equipment:

```yaml
# manifests/production_manifest.yaml
metadata:
  name: "Production Equipment"
  version: "1.0.0"
  
equipment:
  # Line 1 Equipment
  LINE1-SOURCE:
    type: "MaterialSource"
    line_id: "1"
    position: 0
    
  LINE1-FIL:
    type: "FillingStation"
    line_id: "1"
    position: 10
    
  LINE1-PCK:
    type: "PackingStation"
    line_id: "1"
    position: 20
    
  LINE1-PAL:
    type: "PalletizingStation"
    line_id: "1"
    position: 30
    
  LINE1-SINK:
    type: "ProductSink"
    line_id: "1"
    position: 40
    
connections:
  - from: "LINE1-SOURCE"
    to: "LINE1-FIL"
  - from: "LINE1-FIL"
    to: "LINE1-PCK"
  - from: "LINE1-PCK"
    to: "LINE1-PAL"
  - from: "LINE1-PAL"
    to: "LINE1-SINK"
```

## Step 3: Configure Parameters

Create a configuration file with operational parameters:

```yaml
# config/simulation_parameters.yaml
metadata:
  name: "Simulation Parameters"
  version: "1.0.0"
  
# Defaults for all equipment types (prevents hardcoded fallbacks)
defaults:
  source:
    generation_rate: 300.0      # Units per minute
    generation_interval: 0.1    # Check every 6 seconds
    max_output_rate: 350.0
    internal_capacity: 2000.0
    
  sink:
    collection_rate: 300.0      # Match source rate
    collection_interval: 0.1
    max_input_rate: 350.0
    internal_capacity: 10000.0
    
  equipment:
    nominal_rate: 90.0          # Units per minute
    quality_rate: 0.95          # 95% good product
    performance_factor: 0.85    # 85% of nominal
    batch_size: 10.0
    processing_interval: 0.1
    mtbf: 120.0                 # Mean time between failures
    mttr: 10.0                  # Mean time to repair
    
# Equipment-specific overrides
equipment_parameters:
  LINE1-SOURCE:
    generation_rate: 310.0      # Higher rate for Line 1
    
  LINE1-FIL:
    nominal_rate: 95.0
    quality_rate: 0.96
    performance_factor: 0.90
    mtbf: 150.0
    mttr: 8.0
    
  LINE1-PCK:
    nominal_rate: 90.0
    quality_rate: 0.94
    batch_size: 12.0
    
  LINE1-PAL:
    nominal_rate: 88.0
    quality_rate: 0.97
    
# Flow capacity configuration
flow_capacity:
  defaults:
    max_input_rate: 350.0
    max_output_rate: 350.0
    internal_capacity: 1000.0
    initial_level: 0.0
    
  equipment:
    # Sources need larger buffers
    LINE1-SOURCE:
      internal_capacity: 2000.0
      initial_level: 500.0
      
    # Sinks need collection parameters
    LINE1-SINK:
      collection_rate: 300.0    # Units per minute
      collection_interval: 0.1
      internal_capacity: 10000.0
```

## Step 4: Define Production Orders

Create production orders for the simulation:

```yaml
# config/production_orders.yaml
metadata:
  name: "Production Orders"
  version: "1.0.0"
  
orders:
  - order_id: "ORD-001"
    product_id: "ProductA"
    product_name: "Product A - Standard"
    target_volume: 100000       # Units to produce
    line_id: "LINE1"
    priority: 5
    
  - order_id: "ORD-002"
    product_id: "ProductB"
    product_name: "Product B - Premium"
    target_volume: 150000
    line_id: "LINE1"
    priority: 4
```

## Step 5: Build and Run Simulation

### Basic Simulation Script

```python
#!/usr/bin/env python3
"""Run production line simulation."""

import logging
import simpy
import yaml
from datetime import datetime
from pathlib import Path

from twin_model import OntologyModelBuilder
from twin_model.primitives import SourceFlow
from twin_model.primitives.source_flow import ProductionOrder as SourceProductionOrder
from twin_model.integration import MESCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_simulation(simulation_hours=24):
    """Run production line simulation."""
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Build model using three-file architecture
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=Path("ontology/production_line.yaml"),
        manifest_path=Path("manifests/production_manifest.yaml"),
        config_path=Path("config/simulation_parameters.yaml")
    )
    
    model = builder.build_model()
    logger.info(f"Built model with {len(model['primitives'])} equipment pieces")
    
    # Load production orders
    with open("config/production_orders.yaml", 'r') as f:
        orders_data = yaml.safe_load(f)
    
    # Add orders to sources
    for order_data in orders_data['orders']:
        line_id = f"LINE{order_data['line_id']}"
        source_id = f"{line_id}-SOURCE"
        
        if source_id in model['primitives']:
            source = model['primitives'][source_id]
            
            # Create order for source
            order = SourceProductionOrder(
                order_id=order_data['order_id'],
                product_id=order_data['product_id'],
                target_volume=order_data['target_volume'],
                due_time=env.now + (simulation_hours * 60),
                priority=order_data.get('priority', 5)
            )
            
            source.add_order(order)
            logger.info(f"Added order {order.order_id} to {source_id}")
    
    # Initialize MES data collection
    mes_collector = MESCollector(
        start_date=datetime.now(),
        collection_interval=5.0  # 5-minute intervals
    )
    
    # Register equipment with MES
    for equip_id, equipment in model['primitives'].items():
        if '-' in equip_id:
            line_id = equip_id.split('-')[0][-1]
            equip_type = equip_id.split('-')[1]
            mes_collector.register_equipment(equip_id, line_id, equip_type)
    
    # Run simulation
    simulation_minutes = simulation_hours * 60
    logger.info(f"Starting {simulation_hours}-hour simulation...")
    
    env.run(until=simulation_minutes)
    
    # Report results
    report_results(model, mes_collector)
    
    # Export MES data
    mes_collector.export_to_csv(Path("simulation_output.csv"))
    logger.info("Simulation complete!")
    
def report_results(model, mes_collector):
    """Report simulation results."""
    logger.info("=" * 60)
    logger.info("SIMULATION RESULTS")
    logger.info("=" * 60)
    
    # Production totals
    total_produced = 0
    for equip_id, equipment in model['primitives'].items():
        if hasattr(equipment, 'total_collected'):  # Sinks
            total_produced += equipment.total_collected
            logger.info(f"{equip_id}: {equipment.total_collected:.0f} units collected")
    
    logger.info(f"Total Production: {total_produced:.0f} units")
    
    # OEE metrics
    for equip_id, equipment in model['primitives'].items():
        if hasattr(equipment, 'get_oee'):
            oee = equipment.get_oee()
            availability = equipment.get_availability()
            performance = equipment.get_performance()
            quality = equipment.get_quality()
            
            logger.info(f"{equip_id}: OEE={oee:.1f}% "
                       f"(A={availability:.1f}%, P={performance:.1f}%, Q={quality:.1f}%)")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    run_simulation(simulation_hours=24)
```

## Step 6: Run Using Poetry

Execute the simulation using Poetry:

```bash
# Run simulation
~/.local/bin/poetry run python run_simulation.py

# Run with specific duration
~/.local/bin/poetry run python run_simulation.py --hours 168  # 1 week

# Check output
cat simulation_output.csv
```

## Advanced Configuration

### Multi-Line Setup

Extend the manifest with multiple production lines:

```yaml
equipment:
  # Line 1
  LINE1-SOURCE:
    type: "MaterialSource"
    line_id: "1"
  # ... other LINE1 equipment
  
  # Line 2
  LINE2-SOURCE:
    type: "MaterialSource"
    line_id: "2"
  # ... other LINE2 equipment
  
  # Line 3
  LINE3-SOURCE:
    type: "MaterialSource"
    line_id: "3"
  # ... other LINE3 equipment
```

### Changeover Handling

Configure product changeover times:

```python
def calculate_changeover_time(from_product: str, to_product: str) -> float:
    """Calculate changeover time between products."""
    if from_product == to_product:
        return 0.0
    
    # Load product manifest
    product_manifest = ProductManifest()
    product_manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    
    from_prod = product_manifest.get_product(from_product)
    to_prod = product_manifest.get_product(to_product)
    
    if from_prod and to_prod:
        if from_prod.changeover.family == to_prod.changeover.family:
            return 5.0  # Same family: quick changeover
        elif from_prod.changeover.group == to_prod.changeover.group:
            return 15.0  # Same group: medium changeover
        else:
            return 30.0  # Different group: full changeover
    
    return 20.0  # Default changeover time
```

## Important Configuration Notes

### Parameter Resolution Order

After the fixes are implemented, parameters are resolved in this order:

1. **equipment_parameters** section (highest priority)
2. **flow_capacity.equipment** section
3. **defaults** section by equipment type
4. Hardcoded fallback (last resort, should be avoided)

### Critical Parameters to Set

Always configure these parameters to avoid using hardcoded defaults:

**For Sources:**
- `generation_rate` (default fallback: 60.0 - too low!)
- `generation_interval`

**For Sinks:**
- `collection_rate` (default fallback: 50.0 - too low!)
- `collection_interval`

**For Equipment:**
- `nominal_rate` (default fallback: 50.0)
- `quality_rate`
- `performance_factor`
- `mtbf` and `mttr`

### Flow Capacity Settings

Ensure flow capacities are higher than processing rates:
- `max_input_rate` > upstream equipment output rate
- `max_output_rate` > equipment nominal rate
- `internal_capacity` > batch_size * safety_factor

## Monitoring and Debugging

### Enable Debug Logging

```python
# Add to simulation script
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
logging.getLogger('twin_model.ontology_model_builder').setLevel(logging.DEBUG)
```

### Track Parameter Usage

The enhanced OntologyModelBuilder will log parameter sources:

```
INFO - Creating LINE1-SOURCE:
INFO -   generation_rate: 310.0 (from: equipment_parameters)
INFO -   generation_interval: 0.1 (from: defaults)
```

### Monitor Production Progress

```python
def monitor_production(env, model, interval=60):
    """Monitor production progress during simulation."""
    while True:
        yield env.timeout(interval)
        
        total = sum(
            equip.total_collected 
            for equip in model['primitives'].values() 
            if hasattr(equip, 'total_collected')
        )
        
        logger.info(f"Time {env.now:.0f}: Total production = {total:.0f} units")
```

## Troubleshooting

### Low Production Output

If production is much lower than expected:

1. **Check source generation_rate**: Should be 200-300+ units/minute
2. **Check sink collection_rate**: Should match source rate
3. **Verify flow capacities**: Buffers shouldn't be bottlenecks
4. **Review equipment parameters**: nominal_rate, performance_factor
5. **Check for excessive failures**: MTBF too low or MTTR too high

### Equipment Stuck in IDLE/BLOCKED States

1. **Check connections**: Ensure all equipment is properly wired
2. **Verify orders**: Sources need orders to generate material
3. **Check buffer sizes**: Too small buffers cause blockages
4. **Review batch sizes**: Must be smaller than buffer capacity

### OEE Lower Than Expected

1. **Availability**: Adjust MTBF/MTTR ratio
2. **Performance**: Increase performance_factor or nominal_rate
3. **Quality**: Increase quality_rate parameter

## Best Practices

1. **Always use the defaults section** to avoid hardcoded fallbacks
2. **Log parameter sources** to verify correct configuration is used
3. **Start with small simulations** (1 hour) to verify setup
4. **Monitor key metrics** during long runs
5. **Version control** your configuration files
6. **Document** any custom parameters or modifications

## Example: Targeting Specific KPIs

To achieve specific OEE targets (e.g., 46% OEE):

```yaml
# Calculate component targets
# OEE = Availability × Performance × Quality
# 0.46 = 0.67 × 0.496 × 0.626

defaults:
  equipment:
    # For 67% availability
    mtbf: 60.0
    mttr: 30.0  # 60/(60+30) = 66.7% availability
    
    # For 49.6% performance  
    performance_factor: 0.55
    nominal_rate: 90.0
    
    # For 62.6% quality (overall)
    quality_rate: 0.95  # Individual equipment
```

## Summary

The Twin Model provides a flexible, ontology-driven approach to production line simulation. By properly configuring the three core files (ontology, manifest, configuration) and ensuring all critical parameters are set, you can accurately simulate complex production scenarios and optimize for specific KPIs.