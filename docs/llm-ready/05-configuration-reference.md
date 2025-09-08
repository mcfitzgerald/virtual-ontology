# Configuration Reference Guide

## Overview

The Twin Model uses a comprehensive YAML-based configuration system organized into multiple specialized files. This guide provides a complete reference for all configuration options.

## Configuration File Structure

```
config/
├── tunable_parameters.yaml    # Equipment operational parameters
├── mes_parameters.yaml        # MES integration settings
├── product_manifest.yaml      # Product definitions (30+ products)
├── production_orders.yaml     # Production order queue
├── scheduler_config.yaml      # Scheduler optimization settings
└── twin_model.yaml           # Global simulation settings
```

## Core Configuration Files

### 1. Tunable Parameters (`tunable_parameters.yaml`)

Equipment-specific operational parameters that can be adjusted for optimization.

```yaml
# Equipment performance parameters
equipment:
  LINE1-FIL:
    nominal_rate: 50.0        # Units per minute
    quality_rate: 0.95        # Good product ratio (0-1)
    batch_size: 10.0          # Units per batch
    mtbf: 120.0              # Mean time between failures (minutes)
    mttr: 10.0               # Mean time to repair (minutes)
    micro_stop_probability: 0.05  # Chance of micro-stop per cycle
    micro_stop_duration: 0.5      # Duration in minutes
    
  LINE1-PAC:
    nominal_rate: 45.0
    quality_rate: 0.98
    batch_size: 10.0
    mtbf: 150.0
    mttr: 15.0
    performance_factors:      # Product-specific performance
      ProductA: 1.0
      ProductB: 0.85
      ProductC: 0.90
```

**Key Parameters:**
- `nominal_rate`: Base production rate in units/minute
- `quality_rate`: Fraction of good products (affects scrap)
- `mtbf/mttr`: Reliability parameters for availability
- `performance_factors`: Product-specific rate adjustments

### 2. MES Parameters (`mes_parameters.yaml`)

Manufacturing Execution System integration and data collection settings.

```yaml
mes_config:
  # Data collection settings
  collection:
    bucket_size: 300          # Time bucket in seconds (5 min)
    aggregation_level: "equipment"  # equipment|line|plant
    include_micro_stops: true
    track_changeovers: true
    track_quality: true
    
  # Performance targets
  reporting:
    oee_targets:
      availability: 0.85      # Target availability
      performance: 0.95       # Target performance
      quality: 0.98          # Target quality
      overall: 0.79          # Target OEE (A*P*Q)
    
    kpi_thresholds:
      low_oee_alert: 0.60
      high_scrap_alert: 0.10
      long_changeover_alert: 30  # minutes
    
  # Export settings
  export:
    format: "csv"
    timestamp_format: "%Y-%m-%d %H:%M:%S"
    decimal_precision: 3
    include_headers: true
    
  # Equipment groupings
  lines:
    LINE1:
      equipment: ["LINE1-SOURCE", "LINE1-FIL", "LINE1-PAC", "LINE1-SINK"]
      target_oee: 0.80
    LINE2:
      equipment: ["LINE2-SOURCE", "LINE2-FIL", "LINE2-PAC", "LINE2-SINK"]
      target_oee: 0.75
    LINE3:
      equipment: ["LINE3-SOURCE", "LINE3-FIL", "LINE3-PAC", "LINE3-SINK"]
      target_oee: 0.70
```

### 3. Product Manifest (`product_manifest.yaml`)

Complete product catalog with specifications and constraints.

```yaml
products:
  # Standard Products
  ProductA:
    family: "Standard"
    complexity: "Low"
    allergen_group: "None"
    target_rate: 50.0         # Units per minute
    quality_spec: 0.95        # Quality requirement
    min_batch_size: 100
    max_batch_size: 1000
    changeover_group: "A"
    packaging_type: "Box"
    shelf_life_days: 365
    
  ProductB:
    family: "Standard"
    complexity: "Medium"
    allergen_group: "None"
    target_rate: 45.0
    quality_spec: 0.96
    min_batch_size: 100
    max_batch_size: 1000
    changeover_group: "A"
    packaging_type: "Box"
    shelf_life_days: 365
    
  # Premium Products
  ProductP1:
    family: "Premium"
    complexity: "High"
    allergen_group: "None"
    target_rate: 35.0
    quality_spec: 0.98
    min_batch_size: 50
    max_batch_size: 500
    changeover_group: "B"
    packaging_type: "Pouch"
    shelf_life_days: 180
    special_requirements:
      - "Clean room"
      - "Temperature control"
    
  # Allergen Products
  ProductN1:
    family: "Specialty"
    complexity: "Medium"
    allergen_group: "Nuts"
    target_rate: 40.0
    quality_spec: 0.97
    min_batch_size: 75
    max_batch_size: 750
    changeover_group: "C"
    packaging_type: "Box"
    shelf_life_days: 270
    allergen_cleaning_time: 45  # minutes
    
  ProductD1:
    family: "Specialty"
    complexity: "Medium"
    allergen_group: "Dairy"
    target_rate: 42.0
    quality_spec: 0.96
    min_batch_size: 80
    max_batch_size: 800
    changeover_group: "D"
    packaging_type: "Tub"
    shelf_life_days: 90
    allergen_cleaning_time: 30

# Product families configuration
families:
  Standard:
    changeover_time_within: 5    # minutes
    changeover_time_between: 15  # minutes
    
  Premium:
    changeover_time_within: 10
    changeover_time_between: 20
    
  Specialty:
    changeover_time_within: 15
    changeover_time_between: 30

# Allergen groups
allergen_groups:
  None:
    cleaning_required: false
    
  Nuts:
    cleaning_required: true
    cleaning_time: 45
    validation_required: true
    
  Dairy:
    cleaning_required: true
    cleaning_time: 30
    validation_required: false
```

### 4. Production Orders (`production_orders.yaml`)

Queue of production orders to be scheduled and executed.

```yaml
# Production orders configuration
orders:
  - order_id: "ORD-2025-001"
    product_id: "ProductA"
    quantity: 5000
    priority: 1               # 1=highest, 10=lowest
    line_id: "LINE1"         # Specific line assignment
    due_date: "2025-01-15 14:00:00"
    customer: "Customer_ABC"
    notes: "Rush order"
    
  - order_id: "ORD-2025-002"
    product_id: "ProductB"
    quantity: 3000
    priority: 2
    line_id: "ANY"           # Scheduler assigns line
    due_date: "2025-01-15 18:00:00"
    customer: "Customer_XYZ"
    
  - order_id: "ORD-2025-003"
    product_id: "ProductP1"
    quantity: 1500
    priority: 3
    line_id: "LINE2"
    due_date: "2025-01-16 10:00:00"
    customer: "Customer_Premium"
    special_requirements:
      - "Quality inspection"
      - "Special packaging"
    
  - order_id: "ORD-2025-004"
    product_id: "ProductN1"
    quantity: 2000
    priority: 2
    line_id: "LINE3"
    due_date: "2025-01-16 14:00:00"
    customer: "Customer_DEF"
    notes: "Allergen product - clean line first"

# Order queue settings
queue_settings:
  max_queue_size: 100
  allow_rush_orders: true
  auto_assign_lines: true
  respect_due_dates: true
  
# Scheduling windows
scheduling_windows:
  - shift_name: "Day Shift"
    start_time: "06:00:00"
    end_time: "14:00:00"
    available_lines: ["LINE1", "LINE2", "LINE3"]
    
  - shift_name: "Evening Shift"
    start_time: "14:00:00"
    end_time: "22:00:00"
    available_lines: ["LINE1", "LINE2"]
    
  - shift_name: "Night Shift"
    start_time: "22:00:00"
    end_time: "06:00:00"
    available_lines: ["LINE1"]  # Reduced capacity
```

### 5. Scheduler Configuration (`scheduler_config.yaml`)

Optimization settings for production scheduling.

```yaml
scheduler:
  # Scheduler type selection
  type: "CampaignOptimizer"  # Sequential|CampaignOptimizer|ProductionScheduler
  
  # Campaign optimization parameters
  campaign_parameters:
    campaign_size: 50         # Target units per campaign
    min_campaign_size: 20     # Minimum viable campaign
    max_campaign_size: 200    # Maximum campaign size
    group_by_family: true     # Group products by family
    group_by_allergen: true   # Group by allergen status
    
  # Optimization settings
  optimization:
    strategy: "minimize_changeovers"  # minimize_changeovers|minimize_time|maximize_throughput
    lookahead_horizon: 480    # Minutes to look ahead
    reoptimization_interval: 60  # Reoptimize every N minutes
    use_genetic_algorithm: false
    max_iterations: 1000
    
  # Cost factors for optimization
  cost_factors:
    changeover_cost_per_minute: 100.0
    inventory_holding_cost: 0.5
    late_penalty_per_hour: 500.0
    scrap_cost_per_unit: 2.0
    
  # Scheduling constraints
  constraints:
    max_lines: 3
    allow_split_orders: false
    respect_due_dates: true
    max_late_hours: 4
    min_line_utilization: 0.70
    
  # Changeover matrix overrides
  changeover_matrix:
    default: 15               # Default changeover time (minutes)
    same_family: 5
    different_family: 15
    allergen_cleaning: 45
    complexity_change_per_level: 10
    
  # Line capabilities
  line_capabilities:
    LINE1:
      allowed_families: ["Standard", "Premium", "Specialty"]
      max_complexity: "High"
      allergen_capable: true
      
    LINE2:
      allowed_families: ["Standard", "Premium"]
      max_complexity: "Medium"
      allergen_capable: false
      
    LINE3:
      allowed_families: ["Standard", "Specialty"]
      max_complexity: "Medium"
      allergen_capable: true
```

### 6. Global Simulation Settings (`twin_model.yaml`)

Overall simulation configuration and system-wide parameters.

```yaml
simulation:
  # Time settings
  time_unit: "minutes"
  simulation_duration: 1440    # 24 hours
  warmup_period: 60            # 1 hour warmup
  random_seed: 42              # For reproducibility
  
  # Logging configuration
  logging:
    level: "INFO"              # DEBUG|INFO|WARNING|ERROR
    output_file: "simulation.log"
    include_timestamps: true
    log_state_changes: true
    log_failures: true
    log_changeovers: true
    
  # Performance settings
  performance:
    max_events_per_step: 1000
    checkpoint_interval: 3600  # Save state every hour
    enable_profiling: false
    memory_limit_gb: 8
    
  # Model settings
  model:
    use_stochastic_failures: true
    use_quality_variations: true
    use_performance_variations: true
    enable_micro_stops: true
    
  # Output configuration
  output:
    results_directory: "results/"
    save_final_state: true
    save_metrics_csv: true
    save_event_log: false
    generate_reports: true

# System-wide defaults
defaults:
  equipment:
    startup_time: 5.0          # Minutes to start equipment
    shutdown_time: 2.0         # Minutes to stop equipment
    warmup_cycles: 10          # Cycles before full speed
    
  buffers:
    default_capacity: 100      # Units
    warning_level: 0.8         # 80% full warning
    critical_level: 0.95       # 95% full critical
    
  quality:
    inspection_rate: 0.1       # Inspect 10% of products
    rejection_threshold: 0.02  # Reject if >2% defects
    
  maintenance:
    preventive_interval: 480   # 8 hours
    preventive_duration: 30    # 30 minutes
    enable_predictive: false
```

## Configuration Hierarchy

The configuration system follows this hierarchy:

1. **Ontology** (Structure) - Defines what's possible
2. **Manifest** (Instances) - Declares what exists
3. **Config** (Parameters) - Specifies behavior
4. **Runtime** (Overrides) - Dynamic adjustments

```python
# Configuration loading order
config = {
    **ontology_defaults,      # Base from ontology
    **manifest_properties,    # Override with manifest
    **config_parameters,      # Override with config
    **runtime_overrides      # Final runtime overrides
}
```

## Using Configurations

### Loading Configuration

```python
from twin_model import OntologyModelBuilder
import yaml

# Load individual configs
with open("config/product_manifest.yaml") as f:
    products = yaml.safe_load(f)
    
with open("config/scheduler_config.yaml") as f:
    scheduler_config = yaml.safe_load(f)

# Or use the builder
builder = OntologyModelBuilder(
    env=env,
    ontology_path="ontology/filling_line_ontology.yaml",
    manifest_path="manifests/equipment_manifest.yaml",
    config_path="config/tunable_parameters.yaml"
)

# Additional configs can be loaded
builder.load_mes_config("config/mes_parameters.yaml")
builder.load_scheduler_config("config/scheduler_config.yaml")
```

### Runtime Overrides

```python
# Override specific parameters at runtime
builder.set_parameter("LINE1-FIL.nominal_rate", 55.0)
builder.set_parameter("scheduler.campaign_size", 75)

# Batch updates
overrides = {
    "LINE1-FIL.mtbf": 180.0,
    "LINE1-PAC.quality_rate": 0.97,
    "mes_config.bucket_size": 600
}
builder.apply_overrides(overrides)
```

## Validation

### Schema Validation

Each configuration file has an associated schema:

```python
from twin_model.config import validate_config

# Validate against schema
is_valid = validate_config(
    config_data=products,
    schema_name="product_manifest"
)

# Get validation errors
errors = validate_config(
    config_data=scheduler_config,
    schema_name="scheduler_config",
    return_errors=True
)
```

### Cross-File Validation

```python
from twin_model.config import ConfigValidator

validator = ConfigValidator()

# Check references
validator.check_product_references(orders, products)
validator.check_line_assignments(orders, equipment)
validator.check_changeover_compatibility(products)
```

## Best Practices

1. **Version Control**: Keep all configs in version control
2. **Environment Separation**: Use different configs for dev/test/prod
3. **Documentation**: Comment complex configurations
4. **Validation**: Always validate before running simulations
5. **Incremental Changes**: Make small, tested changes
6. **Backup**: Keep backups of working configurations

## Configuration Templates

Templates are provided for common scenarios:

- `templates/high_volume_production.yaml` - High throughput configuration
- `templates/high_mix_low_volume.yaml` - Many products, small batches
- `templates/quality_focused.yaml` - Emphasis on quality over speed
- `templates/cost_optimized.yaml` - Minimize operational costs

## Troubleshooting

### Common Issues

1. **Missing Required Fields**
   ```yaml
   # Error: Missing 'family' field
   ProductX:
     complexity: "Low"  # Missing: family field
   ```

2. **Invalid References**
   ```yaml
   # Error: Product 'ProductZ' not in manifest
   orders:
     - product_id: "ProductZ"  # Does not exist
   ```

3. **Type Mismatches**
   ```yaml
   # Error: nominal_rate must be numeric
   nominal_rate: "fifty"  # Should be: 50.0
   ```

4. **Constraint Violations**
   ```yaml
   # Error: priority must be 1-10
   priority: 15  # Out of range
   ```

For detailed API documentation on configuration handling, see the API reference.

## Batch Processing Parameters

Critical parameters that determine actual throughput. The relationship is:
**Actual throughput = (batch_size / processing_interval) × performance_factor × quality_rate**

### Impact of Batch Size
```yaml
equipment:
  batch_size: 10.0   # Units processed per batch
  # With processing_interval=0.1: Max 100 units/min
  # With processing_interval=0.01: Max 1000 units/min
  
  batch_size: 100.0  # Larger batch (10x throughput)
  # With processing_interval=0.1: Max 1000 units/min
  # With processing_interval=0.01: Max 10000 units/min
```

### Impact of Processing Interval
```yaml
equipment:
  processing_interval: 0.1   # Process every 6 seconds
  # With batch_size=10: Max 100 units/min
  # With batch_size=100: Max 1000 units/min
  
  processing_interval: 0.01  # Process every 0.6 seconds (10x faster)
  # With batch_size=10: Max 1000 units/min
  # With batch_size=100: Max 10000 units/min
```

### Recommended Settings for Realistic Throughput
Based on industry research (see `reference/theory_notes.md`):

```yaml
# For 100-200 units/min target throughput:
defaults:
  equipment:
    batch_size: 100.0         # Process 100 units at a time
    processing_interval: 0.1   # Every 6 seconds
    # Result: 1000 units/min max capacity
    # With performance_factor=0.5: 500 units/min actual
    # With quality_rate=0.95: 475 units/min good output
```

## V-Curve Speed Design

Implements the production line V-curve principle where the constraint (bottleneck) operates at the lowest speed, with upstream and downstream equipment running faster.

### Speed Differential Strategy
```yaml
# Based on Theory of Constraints (Goldratt)
# Constraint = Filler (100%)
# Upstream = +10-20% (push material to constraint)
# Downstream = +10-30% (pull material from constraint)

equipment_parameters:
  # Upstream equipment (push)
  LINE1-SOURCE:
    generation_rate: 120.0   # 120% of filler speed
    
  # Constraint (bottleneck)
  LINE1-FIL:
    nominal_rate: 100.0      # Base speed (100%)
    
  # Downstream equipment (pull)
  LINE1-PCK:
    nominal_rate: 110.0      # 110% of filler speed
  LINE1-PAL:
    nominal_rate: 130.0      # 130% of filler speed
  LINE1-SINK:
    collection_rate: 130.0   # Match fastest downstream
```

### Benefits of V-Curve Design
- Prevents constraint starvation (always has input material)
- Prevents constraint blocking (output always consumed)
- Maximizes constraint utilization (key to overall throughput)
- Creates natural accumulation points

### Example for Three-Line System
```yaml
# LINE 1 - Small scale (100 units/min constraint)
LINE1-SOURCE: 120  # Push
LINE1-FIL: 100     # Constraint
LINE1-PCK: 110     # Pull
LINE1-PAL: 130     # Pull

# LINE 2 - Standard (150 units/min constraint)
LINE2-SOURCE: 180  # Push
LINE2-FIL: 150     # Constraint
LINE2-PCK: 165     # Pull
LINE2-PAL: 195     # Pull

# LINE 3 - High speed (200 units/min constraint)
LINE3-SOURCE: 240  # Push
LINE3-FIL: 200     # Constraint
LINE3-PCK: 220     # Pull
LINE3-PAL: 260     # Pull
```