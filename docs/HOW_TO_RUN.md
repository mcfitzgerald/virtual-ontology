# How to Run the Virtual Twin Model

## Quick Start

This guide shows how to run a simulation of the virtual twin manufacturing model.

## Prerequisites

```bash
# Install dependencies
pip install simpy pyyaml numpy

# Verify directory structure
ls ontology/        # Should contain twin_ontology.yaml, control_mappings.yaml
ls manifests/       # Should contain equipment_manifest.yaml, production_manifest.yaml, etc.
ls config/          # Should contain twin_model.yaml
```

## Basic Simulation Run

### 1. Minimal Example

```python
#!/usr/bin/env python3
"""Run a basic twin model simulation."""

import simpy
from pathlib import Path
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.control.control_manager import ControlManager

# Create SimPy environment
env = simpy.Environment()

# Set up paths
ontology_path = Path("ontology/twin_ontology.yaml")
manifest_dir = Path("manifests")
control_mappings_path = Path("ontology/control_mappings.yaml")

# Initialize control manager
control_mgr = ControlManager(
    ontology_path=ontology_path,
    mappings_path=control_mappings_path
)

# Create model builder
builder = OntologyDrivenModelBuilder(
    env=env,
    ontology_path=ontology_path,
    manifest_dir=manifest_dir,
    control_manager=control_mgr
)

# Build the model
model = builder.build_model()
print(f"Model built with {len(model['primitives'])} primitives")

# Run simulation for 1 shift (480 minutes)
env.run(until=480)
print(f"Simulation completed at time {env.now}")
```

### 2. Full Example with KPI Tracking

```python
#!/usr/bin/env python3
"""Run simulation with KPI monitoring and control changes."""

import simpy
from pathlib import Path
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.control.control_manager import ControlManager

def run_simulation_with_kpis():
    """Run a complete simulation with KPI tracking."""
    
    # Setup environment
    env = simpy.Environment()
    
    # Initialize control system
    control_mgr = ControlManager(
        ontology_path=Path("ontology/twin_ontology.yaml"),
        mappings_path=Path("ontology/control_mappings.yaml")
    )
    
    # Set initial control values (baseline scenario)
    control_mgr.set_control_value("operator_training_hours", 8)
    control_mgr.set_control_value("line_speed_setting", 90)
    control_mgr.set_control_value("pm_schedule_compliance", 60)
    
    # Build model
    builder = OntologyDrivenModelBuilder(
        env=env,
        ontology_path=Path("ontology/twin_ontology.yaml"),
        manifest_dir=Path("manifests"),
        control_manager=control_mgr,
        config_path=Path("config/twin_model.yaml")
    )
    
    model = builder.build_model()
    primitives = model["primitives"]
    scheduler = model.get("scheduler")
    monitors = model.get("monitors", [])
    
    # Get equipment for KPI tracking
    equipment_list = [p for p in primitives.values() 
                     if hasattr(p, 'state_times')]
    
    # Run simulation for 1 week (10080 minutes)
    simulation_duration = 10080
    env.run(until=simulation_duration)
    
    # Calculate KPIs
    print("\n=== SIMULATION RESULTS ===")
    print(f"Simulation time: {env.now} minutes")
    
    # Calculate OEE for each equipment
    for equipment in equipment_list:
        if hasattr(equipment, 'calculate_oee'):
            oee = equipment.calculate_oee()
            print(f"\n{equipment.config.id} OEE:")
            print(f"  Availability: {oee['availability']:.1%}")
            print(f"  Performance: {oee['performance']:.1%}")
            print(f"  Quality: {oee['quality']:.1%}")
            print(f"  Overall OEE: {oee['oee']:.1%}")
    
    # Get production metrics from sinks
    sinks = [p for p in primitives.values() 
             if hasattr(p, 'total_collected')]
    
    for sink in sinks:
        print(f"\n{sink.config.id} Production:")
        print(f"  Total collected: {sink.total_collected}")
        print(f"  Total rejected: {sink.total_rejected}")
        print(f"  Throughput: {sink.get_throughput():.1f} units/hour")
    
    return model, env

if __name__ == "__main__":
    model, env = run_simulation_with_kpis()
```

### 3. Scenario Comparison

```python
#!/usr/bin/env python3
"""Compare different control scenarios."""

import simpy
from pathlib import Path
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.control.control_manager import ControlManager

def run_scenario(scenario_name, control_settings):
    """Run a single scenario with given control settings."""
    
    env = simpy.Environment()
    
    # Setup control manager
    control_mgr = ControlManager(
        ontology_path=Path("ontology/twin_ontology.yaml"),
        mappings_path=Path("ontology/control_mappings.yaml")
    )
    
    # Apply control settings
    for control, value in control_settings.items():
        control_mgr.set_control_value(control, value)
    
    # Build and run model
    builder = OntologyDrivenModelBuilder(
        env=env,
        ontology_path=Path("ontology/twin_ontology.yaml"),
        manifest_dir=Path("manifests"),
        control_manager=control_mgr
    )
    
    model = builder.build_model()
    env.run(until=10080)  # 1 week
    
    # Calculate overall OEE
    equipment = [p for p in model["primitives"].values() 
                if hasattr(p, 'calculate_oee')]
    
    total_oee = 0
    for eq in equipment:
        oee = eq.calculate_oee()
        total_oee += oee['oee']
    
    avg_oee = total_oee / len(equipment) if equipment else 0
    
    print(f"{scenario_name}: OEE = {avg_oee:.1%}")
    return avg_oee

# Define scenarios
scenarios = {
    "Baseline": {
        "operator_training_hours": 8,
        "line_speed_setting": 90,
        "pm_schedule_compliance": 60,
        "changeover_reduction_level": 0
    },
    "Quick Wins": {
        "operator_training_hours": 16,
        "line_speed_setting": 85,
        "pm_schedule_compliance": 70,
        "changeover_reduction_level": 1
    },
    "Optimized": {
        "operator_training_hours": 30,
        "line_speed_setting": 82,
        "pm_schedule_compliance": 90,
        "changeover_reduction_level": 2
    }
}

# Run comparisons
print("=== SCENARIO COMPARISON ===\n")
results = {}
for name, settings in scenarios.items():
    results[name] = run_scenario(name, settings)

print("\n=== SUMMARY ===")
best_scenario = max(results, key=results.get)
print(f"Best scenario: {best_scenario} with {results[best_scenario]:.1%} OEE")
```

## Configuration Files

### Key Configuration Files

1. **ontology/twin_ontology.yaml** - Defines the model structure
2. **ontology/control_mappings.yaml** - Maps controls to parameters
3. **manifests/system_config.yaml** - System-wide settings and failure distributions
4. **manifests/equipment_manifest.yaml** - Equipment specifications
5. **manifests/production_manifest.yaml** - Production line configurations
6. **config/twin_model.yaml** - Technical configuration parameters

### Modifying Configuration

To change simulation behavior without code changes:

```yaml
# manifests/system_config.yaml
control_settings:
  operator_training_hours: 20  # Increase training
  line_speed_setting: 85       # Reduce speed for quality
  
# manifests/equipment_manifest.yaml  
equipment:
  LINE1-FIL:
    properties:
      base_rate: 60.0  # Units per minute
      mtbf: 600       # Increase reliability
```

## Common Tasks

### Running with Custom Duration

```python
# Run for 2 shifts (960 minutes)
env.run(until=960)

# Run for 1 month (43200 minutes)
env.run(until=43200)
```

### Extracting Metrics During Run

```python
def monitor_callback(env, equipment):
    """Print metrics every hour."""
    while True:
        yield env.timeout(60)  # Every hour
        oee = equipment.calculate_oee()
        print(f"[{env.now}] {equipment.config.id} OEE: {oee['oee']:.1%}")

# Add to simulation
for eq in equipment_list:
    env.process(monitor_callback(env, eq))
```

### Saving Results

```python
import json

# Collect results
results = {
    "simulation_time": env.now,
    "equipment_oee": {},
    "production": {}
}

for eq in equipment_list:
    oee = eq.calculate_oee()
    results["equipment_oee"][eq.config.id] = oee

for sink in sinks:
    results["production"][sink.config.id] = {
        "total": sink.total_collected,
        "rejected": sink.total_rejected
    }

# Save to file
with open("simulation_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'twin_model'**
   - Ensure you're running from the project root directory
   - Add project to Python path: `export PYTHONPATH=$PYTHONPATH:.`

2. **FileNotFoundError for YAML files**
   - Check that ontology/ and manifests/ directories exist
   - Verify file paths are correct relative to your working directory

3. **No equipment producing OEE metrics**
   - Ensure simulation runs long enough (minimum 60 minutes)
   - Check that equipment primitives are properly initialized

4. **Control changes not affecting simulation**
   - Verify control names match those in control_mappings.yaml
   - Check that control values are within valid bounds
   - Ensure control manager is passed to model builder

## Next Steps

- Review [SYSTEM_USAGE_GUIDE.md](guides/SYSTEM_USAGE_GUIDE.md) for detailed architecture
- See [CONTROL_SYSTEM_GUIDE.md](guides/CONTROL_SYSTEM_GUIDE.md) for control optimization
- Check [PRIMITIVE_REFERENCE.md](reference/PRIMITIVE_REFERENCE.md) for primitive details
- Read [SIMULATION_PATTERNS.md](reference/SIMULATION_PATTERNS.md) for advanced patterns