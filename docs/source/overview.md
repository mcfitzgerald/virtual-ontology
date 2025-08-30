# System Overview

## Virtual Twin Model Architecture

The Virtual Twin Model is a comprehensive discrete event simulation framework designed for manufacturing systems. It combines ontology-driven configuration with SimPy's powerful simulation capabilities.

## Core Concepts

### Ontology-Driven Design

The system uses YAML-based ontologies to define:
- Equipment types (TBox)
- Equipment relationships (RBox)
- Control parameters
- Failure characteristics

### NO BUFFERS Architecture

Unlike traditional simulation approaches, this system implements direct equipment-to-equipment connections:
- Equipment maintains internal queues
- No separate buffer entities
- Direct material flow between equipment

### Control System

Two-layer control mapping:
1. **Actionable Controls**: High-level parameters like "speed_setpoint", "quality_level"
2. **Parameter Effects**: Maps controls to simulation behaviors (cycle times, failure rates)

### Failure Modeling

Realistic failure distribution:
- 80% Micro-stops (< 1 minute)
- 15% Minor failures (1-10 minutes)
- 5% Major failures (> 10 minutes)

## Key Components

### Primitives

Base simulation entities:
- `EquipmentPrimitive`: Core equipment with processing and failure logic
- `SourcePrimitive`: Material generation with changeover support
- `SinkPrimitive`: Material consumption and tracking
- `SchedulerPrimitive`: Production order management
- `TransportPrimitive`: Material movement between equipment

### Control Manager

Manages the control system:
- Loads control mappings from YAML
- Calculates parameter effects
- Provides runtime control updates

### Model Builder

Constructs the simulation:
- Loads ontologies and manifests
- Creates equipment instances
- Establishes connections
- Initializes control system

## Configuration Hierarchy

1. **Ontology Defaults**: Base values from twin_ontology.yaml
2. **Manifest Properties**: Instance-specific overrides
3. **Runtime Configuration**: Dynamic updates during simulation

## Performance Metrics

Built-in OEE calculation:
- **Availability**: Equipment uptime percentage
- **Performance**: Actual vs theoretical throughput
- **Quality**: Good parts vs total parts
- **OEE**: Availability × Performance × Quality