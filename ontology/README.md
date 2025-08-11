# Ontology & Schema Files

## Overview

This directory contains the semantic layer that enables natural language to SQL translation. Files are organized in **layers** that build on each other conceptually.

## The "LLM Import" Pattern

Since YAML doesn't support native imports, we use a **documentation-based layering** approach:
- Files reference each other via `extends:` or `related_ontologies:` fields
- These are **semantic hints** for the LLM, not technical imports
- The LLM loads multiple files and understands their relationships

Think of it like transparent overlays - each layer adds detail while sharing the same coordinate system (IDs, timestamps, etc.).

## File Manifest

### Base Layer (Historical MES Data)
- **`ontology_spec.yaml`** - Core MES business concepts (Equipment, Products, Events)
- **`database_schema.yaml`** - MES data table structure (mes_data table)

### Twin Layer (Simulation Extension)
- **`twin_ontology_spec.yaml`** - Virtual twin concepts (extends MES ontology)
  - Adds: VirtualSensors, SimulationRuns, ActionableParameters
  - Shares: Equipment, ProductionLine concepts from base
  
- **`twin_database_schema.yaml`** - Twin simulation tables (companion to MES schema)
  - Adds: twin_runs, simulation_data, parameter_history, etc.
  - References: Same mes_database.db file

### Supporting Files
- **`disambiguation_patterns.yaml`** - NLP patterns for query interpretation
- **`learned_patterns.yaml`** - Successful query patterns (grows over time)

## Loading Pattern for LLMs

When working with:
- **Historical analysis only**: Load base layer files
- **Twin simulation**: Load BOTH base + twin layers
- **Any queries**: Always load disambiguation_patterns.yaml

## Shared Concepts

Key concepts that connect the layers:
- `equipment_id` - Same equipment in MES and simulations
- `line_id` - Production lines (LINE1, LINE2, LINE3)
- `timestamp` - Temporal alignment
- `product_id` - Products being manufactured
- OEE metrics - Calculated in both historical and simulated data

## Templates

The `../templates/` directory contains templates for creating new ontologies and schemas that follow this pattern.