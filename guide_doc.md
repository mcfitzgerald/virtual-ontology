# Twin Model System Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Configuration System](#configuration-system)
6. [Database Integration](#database-integration)
7. [Performance Optimization](#performance-optimization)
8. [Usage Workflows](#usage-workflows)
9. [Discovery & Optimization](#discovery--optimization)

## System Overview

The Twin Model framework is an **ontology-driven, SimPy-based discrete-event simulation system** designed for modeling manufacturing digital twins. It provides a separation between structure (defined by ontology) and configuration (provided by manifests), enabling discovery-based optimization and pattern learning.

### Key Features
- **Ontology-Driven**: Structure and relationships defined in YAML
- **SimPy Integration**: Discrete-event simulation with precise timing
- **Rich Observables**: Comprehensive event emission for analysis
- **Performance Optimized**: 30-day simulations with <500MB memory
- **Discovery-Based**: No prescribed parameter effects, learns patterns

### Design Philosophy
```
Structure (Ontology) → Behavior (Primitives) → Configuration (Manifests) → Discovery (Patterns)
```

## Architecture

### Layered Architecture
```
┌─────────────────────────────────────┐
│         Application Layer           │
│    (Experiments, Analysis, API)     │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│       Transduction Layer            │
│    (MES Format, KPI Extraction)     │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│        Simulation Layer             │
│    (SimPy Environment, Events)      │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│         Primitive Layer             │
│   (Equipment, Buffer, Source, etc)  │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│        Configuration Layer          │
│    (Ontology, Manifests, Config)    │
└─────────────────────────────────────┘
```

### File Structure
```
virtual-ontology/
├── ontology/
│   └── twin_ontology.yaml          # Structure definition
├── manifests/
│   ├── equipment_manifest.yaml     # Equipment instances
│   └── production_manifest.yaml    # Products & schedules
├── twin_model/
│   ├── primitives/                 # Simulation building blocks
│   │   ├── base.py                # Base primitive class
│   │   ├── equipment.py           # Manufacturing equipment
│   │   ├── buffer.py              # Material storage
│   │   ├── source.py              # Material generation
│   │   ├── sink.py                # Product collection
│   │   ├── scheduler.py           # Production scheduling
│   │   └── monitor.py             # KPI monitoring
│   ├── model_builder.py           # Builds model from ontology
│   ├── transduction/              # Data conversion
│   │   └── mes_transducer.py     # Convert to MES format
│   ├── config.py                  # Performance configuration
│   ├── state_manager.py           # Checkpoint/resume
│   └── logging_config.py          # Centralized logging
├── database/
│   ├── models.py                  # SQLModel definitions
│   ├── manager.py                 # Database operations
│   └── integration.py             # Twin model integration
└── data/
    └── twin_database.db           # SQLite database
```

## Core Components

### 1. Ontology (`twin_ontology.yaml`)
Defines the **abstract structure** without values:

```yaml
tbox:  # Class definitions
  Equipment:
    type: "Thing"
    properties: [base_rate, mtbf, mttr]
    primitive: "EquipmentPrimitive"
  
  Filler:
    type: "Equipment"
    inherits_properties: true
    
rbox:  # Relationships
  feeds_into:
    domain: Equipment
    range: Buffer
    cardinality: "1-to-1"
    
observables:  # What can be measured
  equipment_state:
    source: Equipment
    type: state
    aggregation: current
    
controllables:  # Experimental parameters
  micro_stop_probability:
    applies_to: Equipment
    range: [0.0, 10.0]
    default: 1.0
```

### 2. Manifests
Provide **concrete instances and values**:

**equipment_manifest.yaml**:
```yaml
equipment:
  - id: LINE1-FIL
    type: Filler
    base_rate: 70
    mtbf: 480
    mttr: 30
    failure_patterns:
      micro_stop:
        probability_per_5min: 0.02
        duration_range: [0.5, 2.0]
```

**production_manifest.yaml**:
```yaml
products:
  - product_id: SKU-1001
    product_name: "Premium Widget"
    target_rate_units_per_5min: 175
    standard_cost_per_unit: 2.50
    sale_price_per_unit: 5.00
```

### 3. Primitives
SimPy-based building blocks implementing behavior:

```python
class EquipmentPrimitive(BasePrimitive):
    """Manufacturing equipment simulation"""
    
    def run(self):
        while True:
            # Process unit
            yield self.env.timeout(cycle_time)
            
            # Emit observable
            self.emit_observable(
                event_type="unit_produced",
                value=1,
                metadata={"product": self.current_product}
            )
```

### 4. Model Builder
Orchestrates model construction:

```python
builder = OntologyDrivenModelBuilder(
    ontology_path="ontology/twin_ontology.yaml",
    manifest_dir="manifests/"
)

# 1. Parse ontology for structure
# 2. Load manifests for values
# 3. Instantiate primitives
# 4. Wire relationships
# 5. Start simulation
model = builder.build_model(env)
```

### 5. MES Transducer
Converts raw observables to industrial format:

```python
transducer = MESTransducer(time_bucket=5)  # 5-minute buckets
mes_df = transducer.process_observables(
    observables,  # Raw events from simulation
    manifests     # For context (products, equipment)
)
# Returns DataFrame with OEE, availability, quality scores
```

## Data Flow

### Simulation Flow
```
1. CONFIGURATION LOADING
   Ontology → Structure Definition
   Manifests → Instance Values
   
2. MODEL BUILDING
   OntologyDrivenModelBuilder:
   - Parses ontology classes
   - Creates primitive instances
   - Wires relationships (feeds_into)
   - Initializes SimPy environment
   
3. SIMULATION EXECUTION
   SimPy Environment:
   - Discrete events fire
   - Primitives emit observables
   - State transitions occur
   - Failures cascade
   
4. DATA COLLECTION
   Observable Buffers:
   - Circular buffers (prevent memory overflow)
   - Sampling based on config
   - Critical events always captured
   
5. TRANSDUCTION
   MES Transducer:
   - Aggregates by time buckets
   - Calculates KPIs
   - Formats for database
   
6. STORAGE
   Database:
   - twin_runs (metadata)
   - simulation_data (MES format)
   - kpi_snapshots (aggregated)
```

### Observable Event Structure
```python
{
    'timestamp': 1234.5,           # Simulation time
    'event_type': 'unit_produced', # Event category
    'primitive_id': 'LINE1-FIL',   # Source equipment
    'primitive_type': 'Equipment', # Primitive class
    'state': 'RUNNING',           # Current state
    'value': 1,                   # Event value
    'metadata': {                 # Additional context
        'product_id': 'SKU-1001',
        'quality': 0.98,
        'cycle_time': 0.857
    }
}
```

## Configuration System

### Performance Presets
Six optimized configurations for different scenarios:

```python
from twin_model.config import PerformanceConfig, ConfigPreset

# Development: Full data collection
config = PerformanceConfig.from_preset(ConfigPreset.DEVELOPMENT)
# - Keep all events (sampling_rate=1)
# - Large buffers (10,000 events)
# - Detailed logging

# Production: Balanced performance
config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
# - Sample 10% of events
# - Medium buffers (1,000 events)
# - 5-minute aggregation

# Long Running: 30+ day simulations
config = PerformanceConfig.from_preset(ConfigPreset.LONG_RUNNING)
# - Minimal memory (100MB limit)
# - Daily checkpoints
# - Aggressive sampling (1%)
```

### Sampling Configuration
```python
sampling = SamplingConfig(
    mode=SimulationMode.PRODUCTION,
    sampling_rate=10,        # Keep every 10th event
    aggregation_interval=5,  # 5-minute windows
    buffer_size=1000,       # Circular buffer size
    enable_global_observables=False
)

# Critical events always recorded:
critical_events = {
    "equipment_failure",
    "state_change",
    "maintenance",
    "cascade_failure"
}
```

## Database Integration

### Hybrid Storage Approach
- **YAML Files**: Structure (ontology) and configuration (manifests)
- **SQLite Database**: Operational data and results

### Database Schema
```sql
-- Configuration (from manifests)
equipment_config       -- Equipment specifications
product_config        -- Product definitions
production_schedule   -- Production orders

-- Operations
twin_runs            -- Simulation run metadata
simulation_data      -- MES-format output
simulation_observables -- Raw events (optional)
historical_mes_data  -- Baseline data

-- Discovery
experiments          -- Parameter experiments
discovered_patterns  -- Found patterns
parameter_recommendations -- Optimizations
kpi_snapshots       -- Aggregated KPIs
```

### Integration Workflow
```python
from database.integration import TwinDatabaseIntegration

integration = TwinDatabaseIntegration()

# Run simulation with database storage
run_id = integration.run_simulation_to_db(
    run_type="experiment",
    parameters={
        "micro_stop_probability": 1.2,
        "performance_factor": 0.95
    },
    days=7,
    parent_run_id="baseline_001"
)

# Results automatically stored:
# - twin_runs: Run metadata
# - simulation_data: MES events
# - kpi_snapshots: Aggregated metrics
```

## Performance Optimization

### Memory Management
```python
# Circular buffers prevent unbounded growth
from collections import deque
buffer = deque(maxlen=1000)  # Automatically drops oldest

# Incremental aggregation (Welford's algorithm)
class IncrementalStats:
    def update(self, value):
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.variance += delta * (value - self.mean)
```

### Event Batching
```python
# Batch events by type and time window
batches = defaultdict(list)
for event in events:
    key = (event['type'], event['time'] // 300)  # 5-min windows
    batches[key].append(event)

# Process batches instead of individual events
# Reduces processing by 99%
```

### State Persistence
```python
from twin_model.state_manager import StateManager

manager = StateManager(checkpoint_dir="checkpoints")

# Save checkpoint
checkpoint = manager.save_checkpoint(
    env, primitives, observables
)

# Resume from checkpoint
env, primitives = manager.restore_checkpoint(
    checkpoint_id="chk_001"
)
```

## Usage Workflows

### 1. Running a Baseline Simulation
```python
from twin_model.model_builder import OntologyDrivenModelBuilder
import simpy

# Build model
builder = OntologyDrivenModelBuilder(
    ontology_path="ontology/twin_ontology.yaml",
    manifest_dir="manifests/"
)

# Create environment and model
env = simpy.Environment()
model = builder.build_model(env)

# Run for 7 days
env.run(until=7 * 24 * 60)

# Collect results
observables = builder.collect_observables()
```

### 2. Running Experiments
```python
# Baseline run
baseline_params = {"micro_stop_probability": 1.0}
baseline_id = integration.run_simulation_to_db(
    run_type="baseline",
    parameters=baseline_params,
    days=7
)

# Experimental runs with variations
for factor in [0.5, 0.8, 1.2, 1.5]:
    test_params = {"micro_stop_probability": factor}
    test_id = integration.run_simulation_to_db(
        run_type="experiment",
        parameters=test_params,
        days=7,
        parent_run_id=baseline_id
    )
```

### 3. Analyzing Results
```python
# Compare runs
comparison = db_manager.compare_runs(
    baseline_id, test_id
)

# Extract patterns
patterns = analyzer.find_patterns(
    observables,
    pattern_types=["correlation", "threshold"]
)

# Generate recommendations
recommendations = optimizer.recommend_parameters(
    target="maximize_oee",
    constraints={"quality_score": ">0.95"}
)
```

## Discovery & Optimization

### Pattern Discovery
The system discovers patterns without prescribed relationships:

```python
# Observable patterns emerge from data
discovered_patterns = {
    "micro_stop_cascade": {
        "description": "Micro-stops in Filler increase Packer failures",
        "evidence": "correlation=0.73, p<0.01",
        "confidence": 0.85
    },
    "startup_scrap_spike": {
        "description": "First 10 minutes have 3x scrap rate",
        "evidence": "mean_diff=2.8x, n=50",
        "confidence": 0.92
    }
}
```

### Parameter Optimization
```python
# System learns optimal parameters through experiments
optimal_parameters = {
    "micro_stop_probability": 0.7,  # Reduced from 1.0
    "performance_factor": 1.05,     # Slight increase
    "changeover_time_factor": 0.85  # Faster changeovers
}

# Expected improvements
expected_kpis = {
    "oee_improvement": "+5.2%",
    "quality_improvement": "+1.8%",
    "throughput_increase": "+8.3%"
}
```

### Continuous Learning
```python
# Each experiment adds to knowledge base
for experiment in experiments:
    # Run simulation
    results = run_simulation(experiment.parameters)
    
    # Extract patterns
    patterns = extract_patterns(results)
    
    # Update recommendations
    update_recommendations(patterns)
    
    # Validate improvements
    validate_in_production(recommendations)
```

## Advanced Features

### Cascade Failure Modeling
```python
failure_modes = {
    "valve_failure": {
        "probability_per_5min": 0.001,
        "duration_range": [30, 90],
        "cascade_probability": 0.3,  # 30% chance to affect downstream
        "cascade_delay": 5.0         # Minutes before cascade
    }
}
```

### Multi-Line Coordination
```python
# Lines can share resources or constraints
production_lines = {
    "LINE1": ["FIL", "PCK", "PAL"],
    "LINE2": ["FIL", "LAB", "PCK", "PAL"],
    "LINE3": ["MIX", "FIL", "CAP", "PCK"]
}

# Cross-line effects modeled through shared buffers
shared_buffer = BufferPrimitive(
    capacity=1000,
    policy="FIFO",
    shared_by=["LINE1", "LINE2"]
)
```

### Real-Time Digital Twin Mode
```python
# Connect to live MES data
real_time_config = PerformanceConfig.from_preset(
    ConfigPreset.REAL_TIME
)

# Update parameters from live data
live_parameters = fetch_from_mes()
model.update_parameters(live_parameters)

# Run in sync with real time
env.run(until=env.now + 60)  # Next minute
```

## Troubleshooting

### Common Issues

1. **Memory Growth**
   - Use appropriate performance preset
   - Reduce sampling_rate
   - Enable checkpoint/resume for long runs

2. **Slow Simulations**
   - Use FAST or PRODUCTION preset
   - Disable global observables
   - Increase aggregation_interval

3. **Missing Events**
   - Check sampling configuration
   - Verify critical_events list
   - Review buffer sizes

4. **Database Performance**
   - Use batch inserts
   - Create appropriate indexes
   - Consider partitioning for large datasets

## Best Practices

1. **Start with Structure**: Define ontology before manifests
2. **Use Presets**: Start with standard performance configs
3. **Incremental Experiments**: Small parameter changes
4. **Version Control**: Track ontology/manifest versions
5. **Monitor Performance**: Use logging and progress reporters
6. **Validate Patterns**: Test discoveries in multiple scenarios
7. **Document Discoveries**: Record patterns in database

## Conclusion

The Twin Model framework provides a powerful, flexible system for manufacturing simulation and optimization. Its ontology-driven architecture, combined with discovery-based learning, enables continuous improvement without prescribed relationships. The performance optimizations make it suitable for production use, while the rich observable system provides deep insights into system behavior.

For questions or contributions, see the project repository.