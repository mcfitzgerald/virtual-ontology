# MES Integration Guide

## Overview

The Twin Model includes a comprehensive Manufacturing Execution System (MES) integration layer that provides production scheduling, execution tracking, and performance monitoring capabilities. This guide covers the complete workflow from production planning to MES data collection.

## Architecture

The MES integration consists of four main components:

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│ Product Manifest│────▶│  Scheduler   │────▶│  Production  │
│  (30+ products) │     │ (Optimizer)  │     │   Orders     │
└─────────────────┘     └──────────────┘     └──────────────┘
                               │                      │
                               ▼                      ▼
                        ┌──────────────┐     ┌──────────────┐
                        │  Equipment   │────▶│     MES      │
                        │  Execution   │     │  Collector   │
                        └──────────────┘     └──────────────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │  MES Records │
                                              │    (CSV)     │
                                              └──────────────┘
```

## Product Manifest

The product manifest (`config/product_manifest.yaml`) defines all products that can be manufactured:

```yaml
products:
  ProductA:
    family: "Standard"
    complexity: "Low"
    allergen_group: "None"
    target_rate: 50.0
    quality_spec: 0.95
    min_batch_size: 100
    max_batch_size: 1000
    changeover_group: "A"
    
  ProductB:
    family: "Premium"
    complexity: "High"
    allergen_group: "Nuts"
    target_rate: 35.0
    quality_spec: 0.98
    min_batch_size: 50
    max_batch_size: 500
    changeover_group: "B"
```

### Product Attributes

- **family**: Product category for grouping similar products
- **complexity**: Manufacturing complexity (Low/Medium/High)
- **allergen_group**: Allergen classification for changeover requirements
- **target_rate**: Target production rate (units/minute)
- **quality_spec**: Quality specification (0-1)
- **batch_size**: Min/max batch constraints
- **changeover_group**: Group for changeover optimization

## Production Scheduling

### Scheduler Types

1. **Sequential Scheduler**: Simple FIFO scheduling
2. **Campaign Optimizer**: Groups similar products to minimize changeovers
3. **Production Scheduler**: Multi-line scheduling with load balancing

### Basic Usage

```python
from twin_model.scheduling import CampaignOptimizer
from twin_model.scheduling.product_manifest import ProductManifest

# Load product definitions
manifest = ProductManifest("config/product_manifest.yaml")

# Create scheduler
scheduler = CampaignOptimizer(
    manifest=manifest,
    campaign_size=50,  # Units per campaign
    optimization_strategy="minimize_changeovers"
)

# Load orders from YAML
scheduler.load_orders("config/production_orders.yaml")

# Or add orders programmatically
from twin_model.scheduling import ProductionOrder

order = ProductionOrder(
    order_id="ORD-2025-001",
    product_id="ProductA",
    quantity=1000,
    priority=1,
    line_id="LINE1",
    due_date="2025-01-15"
)
scheduler.add_order(order)

# Optimize schedule
optimized_schedule = scheduler.optimize()
```

### Production Orders Format

```yaml
# config/production_orders.yaml
orders:
  - order_id: "ORD-001"
    product_id: "ProductA"
    quantity: 1000
    priority: 1
    line_id: "LINE1"
    due_date: "2025-01-15"
    
  - order_id: "ORD-002"
    product_id: "ProductB"
    quantity: 500
    priority: 2
    line_id: "LINE2"
    due_date: "2025-01-16"
```

## Campaign Optimization

The campaign optimizer groups products to minimize changeover costs:

```python
from twin_model.scheduling.cost_calculator import CostCalculator

# Calculate changeover costs
calculator = CostCalculator(manifest)
cost = calculator.calculate_changeover_cost("ProductA", "ProductB")

# Factors considered:
# - Product family differences
# - Allergen cleaning requirements
# - Complexity transitions
# - Equipment adjustments

# Optimization strategies:
# - "minimize_changeovers": Reduce total number of changeovers
# - "minimize_time": Reduce total changeover time
# - "maximize_throughput": Maximize production output
```

### Changeover Matrix

The system automatically generates a changeover cost matrix based on:

1. **Same Family**: 5-minute changeover
2. **Different Family**: 15-minute changeover  
3. **Allergen Cleaning**: +30 minutes
4. **Complexity Change**: +10 minutes per level

## MES Data Collection

### Setting Up Collection

```python
from twin_model.transduction import MESCollector
from twin_model.integration import MESIntegration

# Create collector
mes_collector = MESCollector(env)

# Configure collection parameters
mes_collector.configure(
    bucket_size=300,  # 5-minute buckets
    buffer_size=1000,  # Max records in memory
    flush_interval=3600  # Flush to disk every hour
)

# Connect to equipment
for equipment_id, equipment in model['primitives'].items():
    equipment.observable.subscribe(mes_collector)
```

### MES Records Structure

The MES collector generates records with:

```python
{
    'timestamp': '2025-01-15 10:00:00',
    'equipment_id': 'LINE1-FIL',
    'product_id': 'ProductA',
    'order_id': 'ORD-001',
    'state': 'RUNNING',
    'units_produced': 250,
    'units_scrapped': 5,
    'runtime_seconds': 300,
    'downtime_seconds': 0,
    'availability': 1.0,
    'performance': 0.95,
    'quality': 0.98,
    'oee': 0.93
}
```

### Exporting MES Data

```python
# Real-time export
mes_integration = MESIntegration(
    collector=mes_collector,
    output_path="mes_output.csv",
    real_time=True
)

# Run simulation
env.run(until=1440)  # 24 hours

# Export accumulated data
mes_integration.export_to_csv()

# Or get records programmatically
records = mes_integration.get_records(
    start_time=0,
    end_time=1440,
    equipment_filter=['LINE1-FIL', 'LINE1-PAC']
)
```

## Performance Metrics

### OEE Calculation

The MES integration automatically calculates OEE metrics:

```python
# Per-equipment OEE
oee = availability * performance * quality

# Where:
# - Availability = Runtime / Scheduled Time
# - Performance = Actual Rate / Target Rate  
# - Quality = Good Units / Total Units
```

### Aggregated Metrics

```python
from twin_model.integration import MESAggregator

aggregator = MESAggregator(mes_records)

# Line-level metrics
line_metrics = aggregator.by_line("LINE1")

# Product-level metrics
product_metrics = aggregator.by_product("ProductA")

# Time-based aggregation
hourly_metrics = aggregator.by_time_bucket(3600)  # Hourly

# Custom aggregation
shift_metrics = aggregator.aggregate(
    group_by=['shift', 'line_id'],
    metrics=['oee', 'units_produced', 'downtime']
)
```

## Integration with Simulation

### Complete Workflow

```python
import simpy
from twin_model import OntologyModelBuilder
from twin_model.scheduling import CampaignOptimizer
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.integration import MESIntegration
from twin_model.transduction import MESCollector

# 1. Setup simulation
env = simpy.Environment()

# 2. Build model
builder = OntologyModelBuilder(
    env=env,
    ontology_path="ontology/filling_line_ontology.yaml",
    manifest_path="manifests/equipment_manifest.yaml",
    config_path="config/tunable_parameters.yaml"
)
model = builder.build_model()

# 3. Setup scheduling
manifest = ProductManifest("config/product_manifest.yaml")
scheduler = CampaignOptimizer(manifest, campaign_size=50)
scheduler.load_orders("config/production_orders.yaml")
schedule = scheduler.optimize()

# 4. Setup MES collection
mes_collector = MESCollector(env)
mes_integration = MESIntegration(mes_collector, "mes_output.csv")

# 5. Connect components
for equip_id, equipment in model['primitives'].items():
    equipment.observable.subscribe(mes_collector)

# 6. Execute production
for order in schedule:
    source = model['primitives'][f"{order.line_id}-SOURCE"]
    source.add_order(order)

# 7. Run simulation
env.run(until=1440)  # 24 hours

# 8. Export results
mes_integration.export_to_csv()
print(f"Simulation complete. MES data exported to mes_output.csv")
```

## Configuration Files

### MES Parameters (`config/mes_parameters.yaml`)

```yaml
mes_config:
  collection:
    bucket_size: 300  # 5 minutes
    aggregation_level: "equipment"
    include_micro_stops: true
    
  reporting:
    oee_targets:
      availability: 0.85
      performance: 0.95
      quality: 0.98
    
  export:
    format: "csv"
    timestamp_format: "%Y-%m-%d %H:%M:%S"
    decimal_precision: 3
```

### Scheduler Configuration (`config/scheduler_config.yaml`)

```yaml
scheduler:
  type: "CampaignOptimizer"
  parameters:
    campaign_size: 50
    min_campaign_size: 20
    max_campaign_size: 200
    
  optimization:
    strategy: "minimize_changeovers"
    lookahead_horizon: 480  # 8 hours
    reoptimization_interval: 60  # 1 hour
    
  constraints:
    max_lines: 3
    allow_split_orders: false
    respect_due_dates: true
```

## Best Practices

1. **Product Grouping**: Define product families carefully to optimize changeovers
2. **Campaign Sizing**: Balance between changeover reduction and inventory costs
3. **Real-time Collection**: Enable real-time MES collection for large simulations
4. **Data Validation**: Validate product IDs against manifest before scheduling
5. **Performance Monitoring**: Monitor OEE trends to identify bottlenecks

## Troubleshooting

### Common Issues

1. **Orders Not Executing**
   - Verify line_id matches equipment naming convention
   - Check source equipment is not in continuous mode
   - Ensure product_id exists in manifest

2. **Low OEE Values**
   - Review changeover frequency and duration
   - Check product rate compatibility with equipment
   - Verify quality specifications are achievable

3. **Memory Issues with MES Collection**
   - Reduce buffer_size in collector configuration
   - Enable periodic flushing to disk
   - Use aggregation to reduce record count

## API Reference

For detailed API documentation, see:
- `twin_model.scheduling` - Scheduling components
- `twin_model.integration` - MES integration layer
- `twin_model.transduction` - Data collection and transformation