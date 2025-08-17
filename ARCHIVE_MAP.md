# Archive Map - Virtual Ontology Project

## Overview
This document provides an annotated map of archived files for reference during the SimPy twin model rebuild.

## Archive Structure

### 📁 `archive/twin_v1/twin/` - **Previous Twin Module Implementation**
The complete previous implementation using generator-based approach.

#### Key Files to Reference:
- **`simulation_runner.py`** - Monte Carlo simulation patterns, database integration
- **`optimization_engine.py`** - scipy optimization patterns  
- **`recommendation_engine.py`** - pymoo multi-objective optimization implementation
- **`cost_impact_calculator.py`** - PyMC Bayesian analysis patterns
- **`generator.py`** - Data generation approach (being replaced by SimPy)
- **`config_transformer.py`** - Parameter transformation logic
- **`virtual_sensors.py`** - Virtual sensor concepts (now transduction layer)
- **`actionable_parameters.py`** - Old parameter definitions

#### Optimization Library Usage:
- **`visualization/`** - Plotting utilities for results
  - `pareto_plots.py` - Pareto front visualization
  - `financial_plots.py` - ROI visualization
  - `time_series.py` - Time series plots

### 📁 `archive/docs/` - **Project Documentation**
All original documentation for understanding system design.

#### Essential Documents:
- **`IMPLEMENTATION_PLAN.md`** - Original detailed implementation plan
- **`SYSTEM_ARCHITECTURE.md`** - Complete system architecture
- **`DATABASE_AND_API.md`** - Database schema and API design
- **`README.md`** - Original project overview
- **`SYSTEM_PROMPT.md`** - LLM orchestration instructions

### 📁 `archive/config/` - **Configuration Files**
- **`CLAUDE.md`** - Claude Code configuration
- **`mypy.ini`** - Type checking configuration
- **`.gitignore`** - Git ignore patterns

### 📁 `archive/misc/` - **Miscellaneous Resources**

#### `data/` - Sample Data & Databases
- **`mes_database.db`** - Current database with tables
- **`mes_data_sample.csv`** - Sample MES data format
- **`baseline_config.json`** - Configuration examples

#### `learning_history/` - System Learning
- **`query_logs.json`** - SQL query patterns
- **`twin_operations.jsonl`** - Operation history

#### `reference_graveyard/` - Historical References
- **`virtual_ontology/`** - Original ontology concepts
- **`virtual_twin/`** - Twin system concepts

#### `sysview/` - Visualization Tools
- **`app.py`** - Ontology visualization app
- **`src/`** - Visualization components

## Quick Reference Guide

### For SimPy Primitives Adaptation
Look at: `twin_model/` (still in root - not archived)
- `equipment.py` - Equipment modeling patterns
- `buffer.py` - Buffer implementation
- `production_line.py` - Line composition

### For Optimization Patterns
Look at: `archive/twin_v1/twin/`
- `optimization_engine.py` - scipy usage
- `recommendation_engine.py` - pymoo NSGA-II
- `cost_impact_calculator.py` - PyMC Bayesian

### For Database Patterns
Look at: `archive/twin_v1/twin/`
- `simulation_runner.py` - Database writes
- `schema_manager.py` - Schema management

### For Parameter Mapping
Look at: `archive/twin_v1/twin/`
- `config_transformer.py` - Parameter transformation
- `actionable_parameters.py` - Parameter definitions

### For Visualization
Look at: `archive/twin_v1/twin/visualization/`
- All plotting utilities

## Files NOT Archived (Still Active)

### Root Directory
- `api/` - API implementation (keep)
- `ontology/` - Ontology specifications (keep)
- `templates/` - Template files (keep)
- `twin_model/` - SimPy model (adapt from)
- `api.sh` - API server script (keep)
- `query-log.sh` - Query logging script (keep)
- `revised_implementation_plan.md` - Current plan

## Usage Notes

1. **Reference Only**: Archived code is for reference - don't directly import
2. **Pattern Extraction**: Look for patterns, not direct code reuse
3. **Library Usage**: Focus on how libraries (pymoo, PyMC, scipy) are used
4. **Database Integration**: Study how database connections are handled
5. **Configuration**: Understand parameter transformation approaches

## Search Helpers

### To find optimization examples:
```bash
grep -r "pymoo\|scipy\|optimize" archive/twin_v1/twin/
```

### To find database patterns:
```bash
grep -r "sqlite3\|INSERT\|UPDATE" archive/twin_v1/twin/
```

### To find parameter mappings:
```bash
grep -r "parameter\|transform\|config" archive/twin_v1/twin/
```