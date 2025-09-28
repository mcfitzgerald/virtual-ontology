# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# General
- I like using your planning mode and working together to brainstorm and vet approaches
- When doing web searches, start with 2025 forward and if few things or nothing found then lift that constraint

# Project Overview
Twin Model is an ontology-driven simulation framework for manufacturing systems using SimPy containers. The architecture separates concerns into three layers:
- **Structure (Ontology)**: Equipment types and properties defined in `ontology/filling_line_ontology.yaml`
- **Instances (Manifest)**: Specific equipment declarations in `manifests/equipment_manifest.yaml`
- **Parameters (Config)**: Tunable simulation parameters in `config/tunable_parameters.yaml`

# Commands

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

# Scan for hardcoded values
poetry run semgrep --config .semgrep/rules/ twin_model/
```

## Running Simulations
```bash
# Run standalone simulation with default configuration
poetry run python run_twin_simulation.py

# Run with custom duration (in days)
poetry run python run_twin_simulation.py --days 7

# Run with debug output
poetry run python run_twin_simulation.py --debug
```

## Building Documentation
```bash
poetry run sphinx-build -b html docs/sphinx-source docs/build
```

# Architecture

## Core Components
- **OntologyModelBuilder** (`ontology_model_builder.py`): Main entry point that builds simulation models from YAML configuration files
- **Primitives** (`twin_model/primitives/`):
  - `SourceFlow`: Material sources with production order support
  - `EquipmentFlow`: Processing equipment with OEE modeling (MTBF/MTTR, quality, micro-stops)
  - `SinkFlow`: Output collection with metrics aggregation
  - `BufferFlow`: Intermediate storage between equipment
- **Scheduling** (`twin_model/scheduling/`): MES production scheduling and campaign optimization
- **Monitoring** (`twin_model/monitoring/`): Real-time OEE, throughput, and bottleneck detection
- **Integration** (`twin_model/integration/`): MES data collection and export
- **Transduction** (`twin_model/transduction/`): Event-driven data transformation

## Configuration Files
All configuration lives in three directories:
- `ontology/`: Equipment type definitions (TBox - terminological box)
- `manifests/`: Equipment instances, connections, production orders (ABox - assertional box)
- `config/`: Tunable parameters for all equipment and simulation settings

## Key Design Patterns
- **Container-based flow**: Uses SimPy containers for continuous material flow simulation
- **Event-driven monitoring**: Observable events for state changes and metrics
- **V-curve speed design**: Automatic speed differentials for push/pull flow optimization
- **Theory of Constraints (TOC)**: Goldratt's methodology for bottleneck identification

# Code Practices for Python
- Comply with PEP 8 (Style Guide), PEP 257 (Docstring Conventions), PEP 484 (Type Hints)
- Use `mypy` and `ruff` to validate compliance
- Use judicious testing (test at module or integration level) and manage with `pytest`
- Use `poetry` for project environment and package management
- Always use `poetry run` to execute Python commands in this project

# Code Authoring by Claude
- Use context7 mcp tool to fetch documentation and example patterns
- When critical, search web for patterns or inspirations
- Vet 2-3 paths before proceed, and confirm with me if you are unsure
- Structure large coding tasks in phases, creating an implementation plan markdown file
- Stop and test between phases and make room for us to discuss
- Backward compatibility is seldom a requirement, don't keep legacy code, don't make "V2s and FIXED" files, move the old to archive if unsure, or stop and ask
- **NEVER** use hardcodes, always use config patterns, ask if you are unsure
- Use `semgrep --config .semgrep/rules/ twin_model/` to scan for misplaced hardcodes
- Maintain a CHANGELOG.md file and remind me to use the custom claude code `/commit` command
- Never bypass an approach or plan we agree to when you hit an issue, stop and tell me so we can fix it!