# Twin Model

An ontology-driven simulation framework for manufacturing systems using SimPy containers.

## Overview

Twin Model provides a flexible, ontology-driven architecture for simulating production lines and manufacturing systems. It separates concerns into three distinct layers:

1. **Structure** (Ontology) - Defines equipment types and their properties
2. **Instances** (Manifest) - Declares specific equipment and topology
3. **Parameters** (Config) - Contains tunable simulation parameters

## Features

- **Container-based flow simulation** - Continuous material flow using SimPy containers
- **Ontology-driven architecture** - Clear separation between structure, instances, and parameters
- **Real-time monitoring** - Track OEE, throughput, quality metrics
- **Flexible configuration** - YAML-based configuration system
- **Failure modeling** - MTBF/MTTR and micro-stops simulation
- **Production order support** - Batch and continuous production modes
- **Bottleneck detection** - Real-time identification of production constraints
- **Observable events** - Event-driven architecture for monitoring and control
- **Theory of Constraints (TOC)** - Goldratt's methodology for optimization
- **V-curve speed design** - Automatic speed differentials for push/pull flow
- **Batch processing** - Configurable batch sizes and processing intervals
- **MES integration** - Complete scheduling and production management

## Installation

```bash
# Clone the repository
git clone https://github.com/virtual-ontology/twin-model.git
cd virtual-ontology

# Install with Poetry  
poetry install

# Or install with pip
pip install -e .
```

## Quick Start

```python
from twin_model import OntologyModelBuilder
import simpy

# Create environment
env = simpy.Environment()

# Build model from configuration files
builder = OntologyModelBuilder(
    env=env,
    ontology_path="ontology/filling_line_ontology.yaml",
    manifest_path="manifests/equipment_manifest.yaml", 
    config_path="config/tunable_parameters.yaml"  # Single config file
)

# Build and run simulation
model = builder.build_model()
env.run(until=60)  # Run for 60 minutes

# Access metrics
metrics = builder.get_metrics()
for equip_id, equip_metrics in metrics.items():
    print(f"{equip_id}: OEE={equip_metrics.get('oee', 0):.1%}")
```

## Standalone Simulation

Run a complete simulation with production orders:

```bash
# Run with default configuration (orders cycle to fill duration)
poetry run python run_twin_simulation.py

# Run with custom duration (orders automatically cycle for 7 days)
poetry run python run_twin_simulation.py --days 7

# Run without order cycling (stop when initial orders complete)
poetry run python run_twin_simulation.py --days 1 --no-cycle-orders

# Run with debug output
poetry run python run_twin_simulation.py --debug
```

This will:
- Load configuration from `config/tunable_parameters.yaml`
- Process production orders from `manifests/production_orders_manifest.yaml`
- **Automatically cycle orders** to fill simulation duration (default behavior)
- Schedule orders **per-line independently** (each line starts at t=0)
- Generate MES output with **correct order tracking** via background sync
- Display real-time OEE metrics

## Configuration Files

### Ontology File (Structure)
Defines equipment types and their capabilities:

```yaml
tbox:
  types:
    FillingStation:
      maps_to:
        framework_primitive: "EquipmentFlow"
      required_properties:
        - nominal_rate
        - quality_rate
      relationships:
        can_connect_to: ["PackingStation", "QualityControl"]
```

### Manifest File (Instances)
Declares equipment instances and connections:

```yaml
equipment:
  LINE1-FIL:
    type: "FillingStation"
    line_id: "LINE1"
    position: 10

connections:
  - from: "LINE1-SOURCE"
    to: "LINE1-FIL"
    type: "material_flow"
```

### Config File (Parameters)
Contains tunable parameters:

```yaml
equipment_parameters:
  LINE1-FIL:
    nominal_rate: 50.0
    quality_rate: 0.95
    mtbf: 60.0
    mttr: 10.0
```

## Production Orders

The framework supports both continuous and order-based production:

```python
from twin_model import ProductionOrder

# Create a production order
order = ProductionOrder(
    order_id="ORD-2025-001",
    product_id="SKU-1001",
    target_volume=1000.0,
    due_time=120.0,  # Due in 120 minutes
    priority=8       # Higher priority = more urgent
)

# Add to source (if not in continuous mode)
source = model['primitives']['LINE1-SOURCE']
source.add_order(order)
```

**Note**: When using the simulation runner script:
- Orders **automatically cycle** to fill the simulation duration by default
- Each line schedules orders **independently** (not globally sequenced)
- Use `--no-cycle-orders` flag to disable automatic cycling
- MES tracking ensures correct order IDs via background synchronization

## Documentation

### Getting Started (Recommended Order)
1. [User Guide](docs/llm-ready/00-user-guide.md) - Complete system understanding and tutorial
2. [Architecture Overview](docs/llm-ready/01-architecture-overview.md) - Ontology-driven design explained
3. [Quick Reference](TWIN_MODEL_QUICK_REFERENCE.md) - Common patterns and API reference
4. [Quick Start API](docs/llm-ready/02-quickstart-api.md) - API guide with three-file pathway

### Deep Dive
- [Complete API Reference](docs/llm-ready/03-complete-api-reference.md) - Full API documentation
- [MES Integration Guide](docs/llm-ready/04-mes-integration-guide.md) - Production scheduling and data collection
- [Configuration Reference](docs/llm-ready/05-configuration-reference.md) - All configuration options
- [Example Configurations](docs/llm-ready/yaml-examples/) - Sample YAML files

### Additional Resources
- [Documentation Overview](docs/DOCS_TOC.md) - Complete guide to all documentation
- [Next Steps](NEXT_STEPS.md) - Current status and known issues
- [Production Line Theory](reference/theory_notes.md) - Empirical research and industry standards
- [Implementation Roadmap](IMPLEMENTATION_PLAN.md) - Detailed optimization plan

## Development

```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy twin_model

# Linting
poetry run ruff check twin_model

# Format code
poetry run ruff format twin_model

# Build documentation
poetry run sphinx-build -b html docs/sphinx-source docs/build
```

## Project Structure

```
twin_model/
├── twin_model/           # Main package
│   ├── primitives/       # Flow primitives (Source, Equipment, Sink)
│   ├── monitoring/       # Real-time monitoring
│   ├── scheduling/       # MES production scheduling
│   └── tests/           # Unit and integration tests
├── ontology/            # Ontology definitions
├── manifests/           # Equipment manifests
├── config/              # Configuration files
├── reference/           # Research and theory documentation
└── docs/               # Documentation
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Support

For questions and support, please open an issue on GitHub.