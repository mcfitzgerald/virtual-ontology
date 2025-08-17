# SimPy Twin Model

A discrete event simulation model for manufacturing production lines using SimPy.

## Features

- **Realistic Material Flow**: Discrete units flow through equipment and buffers
- **Equipment Modeling**: Configurable failure rates (MTBF/MTTR), production rates, and quality
- **Buffer Management**: Work-in-process tracking with starvation and blockage detection
- **Parameter Sensitivity**: 5 actionable parameters with measurable impact on OEE
- **Multi-Line Support**: Simulate multiple production lines simultaneously
- **MES Data Logging**: Capture equipment states and metrics at regular intervals

## Installation

```bash
pip install simpy
```

## Quick Start

```python
from twin_model import SimulationRunner, ActionableParameters

# Create runner with default configuration
runner = SimulationRunner()

# Adjust parameters
params = ActionableParameters(
    performance_factor=1.2,  # 20% faster production
    scrap_multiplier=0.8,     # 20% less scrap
)

# Run simulation
results = runner.run_simulation(
    parameters=params,
    duration_days=7,
    seed=42
)

# Display results
print(f"Mean OEE: {results.kpi_summary['mean_oee']:.1f}%")
print(f"Total Output: {results.kpi_summary['total_units_produced']}")
```

## Documentation

Full documentation is available in the `docs/` directory. To build and view:

```bash
cd docs
make html
open _build/html/index.html  # On macOS
# or
python -m http.server -d _build/html  # Serve on http://localhost:8000
```

## Testing

Run the test suite:

```bash
python tests/test_simulation.py
```

## Architecture

The model consists of:

- **Equipment**: Production machines with failure modeling
- **Buffers**: Work-in-process storage between equipment
- **Production Lines**: Complete lines with material flow
- **Configuration**: Fully config-driven parameters
- **Runner**: Simulation execution and results collection

## Parameter Impact

The 5 actionable parameters and their effects:

1. **micro_stop_probability**: Scales MTBF (failure frequency)
2. **performance_factor**: Scales production rate
3. **scrap_multiplier**: Scales quality losses
4. **material_reliability**: Controls material availability
5. **cascade_sensitivity**: Controls buffer sizes (coupling tightness)

## License

Part of the Virtual Ontology project.