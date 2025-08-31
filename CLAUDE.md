# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# General
- I like using your planning mode and working together to brainstorm and vet approaches
- When doing web searches, start with 2025 forward and if few things or nothing found then lift that constraint

# Code practices for Python
- Comply with PEP 8 (Style Guide), PEP 257 (Docstring Convetions), PEP 484 (Type Hints)
- Use `mypy` and `ruff` to validate compliance
- Use judicious testing (test at module or integration level) and manage with `pytest`
- Use `poetry` for project environment and package management

# Code authoring by Claude
- Use context7 mcp tool to fetch documentation and example patterns
- When critical, search web for patterns or inspirations
- Vet 2-3 paths before proceed, and confirm with me if you are unsure
- Structure large coding tasks in phases, creating an implementation plan markdown file. 
- Stop and test between phases and make room for us to discuss
- Backward compatibility is seldom a requirement, don't keep legacy code, don't make "V2s and FIXED" files, move the old to archive if unsure, or stop and ask
- **NEVER** use hardcodes , always use config patterns, ask if you are unsure
- Use `semgrep` and appropriate rules files to scan for misplaced hardcodes
- Maintain a CHANGELOG.md file and remind me to use the custom claude code `/commit` command

## Common Development Commands

### Testing
```bash
# Run all tests
python -m pytest twin_model/tests/

# Run unit tests only  
python -m pytest twin_model/tests/unit/

# Run integration tests
python -m pytest twin_model/tests/integration/

# Run specific test file
python -m pytest twin_model/tests/unit/test_control_mappings.py
```

### Development Tools
```bash
# Type checking
mypy twin_model

# Linting
ruff check twin_model

# Format code
ruff format twin_model

# Install development dependencies
pip install -e ".[dev]"

# Generate LLM-optimized documentation
python docs/generate_llm_docs.py

# Build HTML documentation (requires sphinx)
sphinx-build -M html docs/source docs/build -c docs/source
```

## Architecture Overview

### Core Design Principles
- **NO BUFFERS Architecture**: Direct equipment-to-equipment connections without intermediate buffers. Equipment uses internal queues only.
- **Ontology-Driven**: Equipment types and behaviors defined in YAML ontologies, not hardcoded.
- **Two-Layer Control System**: High-level controls (operator training, maintenance compliance) map to low-level simulation parameters (cycle time, MTBF).
- **Configuration-Based**: All behaviors defined through YAML manifests, minimizing code changes.

### Key Components

1. **Model Builder** (`twin_model/model_builder.py`): 
   - Interprets ontology structure
   - Creates primitives from manifests
   - Wires equipment connections
   - Integrates control system

2. **Primitives** (`twin_model/primitives/`):
   - `equipment.py`: Core equipment with internal queues, state management, failure modeling
   - `source.py`: Material generator based on production orders
   - `sink.py`: Collects finished products, tracks metrics
   - `scheduler.py`: Manages production orders and changeovers
   - `monitor.py`: Observes and logs equipment states

3. **Control System** (`twin_model/control/`):
   - `control_manager.py`: Maps high-level controls to parameters
   - `parameter_effects.py`: Defines how controls affect simulation (linear, inverse, sigmoid transformations)

4. **Configuration Files**:
   - `ontology/twin_ontology.yaml`: Equipment type definitions
   - `ontology/control_mappings.yaml`: Control-to-parameter mappings
   - `manifests/equipment_manifest.yaml`: Equipment instances
   - `manifests/production_manifest.yaml`: Line configurations
   - `manifests/system_config.yaml`: Failure distributions, global settings

### Material Flow Pattern
```
Source → Equipment1 → Equipment2 → ... → Sink
         ↑__________|  ↑__________|
         (internal)    (internal)
         (queues)      (queues)
```

Equipment pulls from upstream internal output queue and pushes to downstream internal input queue. No external buffers exist between equipment.

### State Management
Equipment states: IDLE, RUNNING, STOPPED_FAILURE, STOPPED_MAINTENANCE, STARVED, BLOCKED, CHANGEOVER, STARTUP, SHUTDOWN

Failure types: micro_stop (seconds), minor_failure (minutes), major_failure (hours)

### Control Effects
Controls affect parameters through mathematical transformations:
- `linear`: param = base + (control * magnitude)
- `inverse_linear`: param = base / (1 + control * magnitude)  
- `sigmoid`: S-curve response for smooth transitions
- `exponential`: Exponential growth/decay

## Key Patterns

### Adding New Equipment Type
1. Define in `ontology/twin_ontology.yaml`
2. Add instance to `manifests/equipment_manifest.yaml`
3. Connect in `manifests/production_manifest.yaml`

### Modifying Control Effects
1. Update mapping in `ontology/control_mappings.yaml`
2. Verify effect type in `twin_model/control/parameter_effects.py`
3. Test with `python -m pytest twin_model/tests/unit/test_control_mappings.py`

### Running Simulations
Always use `OntologyDrivenModelBuilder` with proper paths:
```python
builder = OntologyDrivenModelBuilder(
    env=env,
    ontology_path=Path("ontology/twin_ontology.yaml"),
    manifest_dir=Path("manifests"),
    control_manager=control_mgr
)
```

## Important Notes
- Equipment connections are position-based (lower position → upstream)
- Production orders trigger automatic changeovers
- OEE calculation requires minimum 60 minutes simulation time
- Control values persist across simulation runs unless explicitly reset