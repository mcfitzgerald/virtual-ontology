# Twin Model - Ontology-Driven Manufacturing Simulation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SimPy](https://img.shields.io/badge/SimPy-4.0+-green.svg)](https://simpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Twin Model is an ontology-driven discrete event simulation framework for manufacturing systems. It provides a flexible, configuration-based approach to modeling production lines with realistic equipment behavior, failure patterns, and control systems.

### Key Features

- **Ontology-Driven Architecture**: Define equipment types and behaviors using YAML ontologies
- **NO BUFFERS Design**: Direct equipment-to-equipment connections for realistic material flow
- **Two-Layer Control System**: Map high-level controls to simulation parameters
- **Realistic Failure Modeling**: Micro-stops, minor failures, and major breakdowns
- **Production Order Management**: Schedule-based production with changeover support
- **OEE Metrics**: Built-in availability, performance, and quality tracking
- **MES Data Generation**: Produce realistic manufacturing execution system data

## Quick Start

### Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install simpy pydantic pyyaml numpy pandas
```

### Basic Usage

```python
import simpy
from pathlib import Path
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.control.control_manager import ControlManager

# Create SimPy environment
env = simpy.Environment()

# Initialize control manager (optional)
control_mgr = ControlManager(
    ontology_path=Path("ontology/twin_ontology.yaml"),
    mappings_path=Path("ontology/control_mappings.yaml")
)

# Build model from ontology
builder = OntologyDrivenModelBuilder(
    env=env,
    ontology_path=Path("ontology/twin_ontology.yaml"),
    manifest_dir=Path("manifests"),
    control_manager=control_mgr
)

model = builder.build_model()

# Run simulation
env.run(until=480)  # 8 hours

# Get metrics
for equipment in model.equipment_list:
    print(f"{equipment.name}: OEE = {equipment.oee:.2%}")
```

## Project Structure

```
twin-model/
├── twin_model/              # Core simulation module
│   ├── primitives/         # Equipment, source, sink, scheduler
│   ├── control/            # Control system implementation
│   ├── model_builder.py    # Main model construction
│   └── tests/              # Unit and integration tests
├── ontology/               # Equipment type definitions
│   ├── twin_ontology.yaml  # Main ontology
│   └── control_mappings.yaml # Control parameter mappings
├── manifests/              # Equipment instances and configuration
│   ├── equipment_manifest.yaml
│   ├── production_manifest.yaml
│   └── system_config.yaml
├── config/                 # Runtime configuration
│   └── twin_model.yaml
├── templates/              # Ontology templates
├── docs/                   # Documentation
│   ├── HOW_TO_RUN.md      # Detailed usage guide
│   └── llm_output/        # API documentation
└── mes_data_sample.csv    # Example output format
```

## Documentation

- **[HOW_TO_RUN.md](docs/HOW_TO_RUN.md)** - Comprehensive usage guide with examples
- **[API Documentation](docs/llm_output/twin_model_api.md)** - Complete API reference
- **[Architecture Guide](docs/architecture/TWIN_ARCHITECTURE.md)** - System design and concepts
- **[Primitive Reference](docs/reference/PRIMITIVE_REFERENCE.md)** - Equipment types and behaviors

### Generating Documentation

```bash
# Generate LLM-optimized documentation
python docs/generate_llm_docs.py

# Generate HTML documentation (requires sphinx)
sphinx-build -M html docs/source docs/build -c docs/source
```

## Configuration

### Ontology (Equipment Types)

Define equipment types in `ontology/twin_ontology.yaml`:

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

### Manifests (Equipment Instances)

Specify equipment instances in `manifests/equipment_manifest.yaml`:

```yaml
equipment:
  - id: "LATHE_001"
    type: "Lathe"
    properties:
      cycle_time: 45.0
      quality_rate: 0.99
```

### Control Mappings

Configure control effects in `ontology/control_mappings.yaml`:

```yaml
speed_setpoint:
  parameters:
    - name: cycle_time
      effect_type: inverse_linear
      magnitude: 0.5
```

## Testing

Run the test suite:

```bash
# All tests
python -m pytest twin_model/tests/

# Unit tests only
python -m pytest twin_model/tests/unit/

# Integration tests
python -m pytest twin_model/tests/integration/
```

## Example Output

The simulation generates MES-compatible data (see `mes_data_sample.csv`):

| Timestamp | EquipmentID | MachineStatus | GoodUnitsProduced | OEE_Score |
|-----------|-------------|---------------|-------------------|-----------|
| 00:00:00  | LINE1-FIL   | Running       | 218              | 48.4      |
| 00:05:00  | LINE1-FIL   | Running       | 235              | 52.2      |

## Development

### Setting up for development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run type checking
mypy twin_model

# Run linting
ruff check twin_model

# Format code
ruff format twin_model
```

## Contributing

Contributions are welcome! Please ensure:
- All tests pass
- Code follows the existing style
- Documentation is updated
- Type hints are provided

## License

MIT License - see LICENSE file for details

## Citation

If you use this software in your research, please cite:

```bibtex
@software{twin_model,
  title = {Twin Model: Ontology-Driven Manufacturing Simulation},
  author = {Virtual Ontology Team},
  year = {2024},
  url = {https://github.com/yourusername/twin-model}
}
```