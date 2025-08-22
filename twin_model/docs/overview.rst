Overview
========

Introduction
------------

The Twin Model framework is an ontology-driven simulation system designed for modeling complex manufacturing environments. 
It provides a separation between structure (defined by ontology) and configuration (provided by manifests), 
enabling discovery-based optimization and pattern learning.

Core Philosophy
---------------

**Discovery Over Prescription**
   The system doesn't prescribe how parameters affect outcomes. Instead, it provides:
   
   * Rich observables for pattern discovery
   * Controllable parameters without defined relationships
   * Comprehensive event streams for analysis

**Ontology-Driven Design**
   The ontology defines:
   
   * Class hierarchies (Equipment, Buffer, Source, etc.)
   * Relationships (feeds_into, draws_from, part_of)
   * Observable properties (what can be measured)
   * Controllable parameters (what can be adjusted)

**Performance First**
   Built with production-scale simulations in mind:
   
   * Memory-efficient circular buffers
   * Event batching and aggregation
   * Configurable sampling strategies
   * State persistence for long simulations

System Architecture
-------------------

The system follows a layered architecture:

.. code-block:: text

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

Key Features
------------

**Comprehensive Event System**
   Every state change and action generates observable events:
   
   * State transitions (RUNNING, IDLE, FAILED)
   * Production events (unit_produced, unit_scrapped)
   * Flow events (material_consumed, buffer_level)
   * Performance metrics (OEE, availability, quality)

**Flexible Configuration**
   Multiple levels of configuration:
   
   * Ontology: Defines structure and relationships
   * Manifests: Provide instance-specific values
   * Performance Config: Controls simulation behavior
   * Runtime Parameters: Adjustable during execution

**Scalable Performance**
   Optimized for large-scale simulations:
   
   * 30-day simulations with <500MB memory
   * Sub-5 minute completion for month-long runs
   * Configurable detail levels via sampling
   * Checkpoint/resume for very long simulations

Use Cases
---------

The framework is designed for:

1. **Production Optimization**
   - Discover optimal parameter settings
   - Identify bottlenecks and constraints
   - Test improvement hypotheses

2. **Predictive Maintenance**
   - Model failure patterns and cascades
   - Optimize maintenance schedules
   - Predict equipment degradation

3. **Capacity Planning**
   - Simulate different production scenarios
   - Evaluate equipment investments
   - Plan for demand variations

4. **Digital Twin Applications**
   - Real-time production monitoring
   - What-if scenario analysis
   - Performance prediction

Getting Started
---------------

To start using the Twin Model framework:

1. Define your system structure in the ontology
2. Configure equipment and products in manifests
3. Choose a performance preset for your use case
4. Build and run the simulation
5. Analyze the rich observable stream

See the :doc:`quickstart` guide for a complete example.