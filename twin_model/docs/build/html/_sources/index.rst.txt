.. Virtual Ontology Twin Model documentation master file

Virtual Ontology Twin Model Documentation
==========================================

Welcome to the Virtual Ontology Twin Model documentation. This module provides an
ontology-driven simulation framework for generating synthetic MES (Manufacturing 
Execution System) data using SimPy discrete event simulation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   quickstart
   api/index
   primitives
   ontology_driven
   usage

Overview
--------

The twin model module provides:

* **Ontology-Driven Architecture**: Build simulations from ontology definitions
* **Primitive Components**: Reusable simulation building blocks
* **SimPy Integration**: Discrete event simulation with rich observables
* **Pattern Discovery**: Generate data for pattern analysis
* **MES Transduction**: Convert simulation events to MES-compatible data

Key Features
------------

* **Modular Primitives**: Equipment, Buffer, Source, Sink, Scheduler, Monitor
* **Ontology Mapping**: Automatic model construction from YAML ontologies
* **State Management**: Track and persist simulation state
* **KPI Monitoring**: Real-time OEE, availability, performance, quality metrics
* **Event Logging**: Comprehensive event capture for analysis

Architecture
------------

The twin model follows a layered architecture:

1. **Primitives Layer** (:mod:`twin_model.primitives`): Core simulation components
2. **Model Builder** (:mod:`twin_model.model_builder`): Ontology-driven construction
3. **State Management** (:mod:`twin_model.state_manager`): Simulation state tracking
4. **Transduction Layer** (:mod:`twin_model.transduction`): MES data generation
5. **Configuration** (:mod:`twin_model.config`): Runtime configuration
6. **Logging** (:mod:`twin_model.logging_config`): Structured logging

Primitive Components
--------------------

Equipment Primitive
~~~~~~~~~~~~~~~~~~~
Models production equipment with states (idle, processing, maintenance, failed).

Buffer Primitive
~~~~~~~~~~~~~~~~
FIFO/LIFO queues for work-in-progress items with capacity constraints.

Source Primitive
~~~~~~~~~~~~~~~~
Generates items based on arrival patterns (constant, exponential, normal).

Sink Primitive
~~~~~~~~~~~~~~
Collects finished products and calculates quality metrics.

Scheduler Primitive
~~~~~~~~~~~~~~~~~~~
Manages production orders and maintenance schedules.

Monitor Primitive
~~~~~~~~~~~~~~~~~
Tracks KPIs and generates performance metrics.

Dependencies
------------

This module depends on:

* **manifests/**: Equipment and production configurations
* **ontology/**: Twin and MES ontology definitions
* **config/**: System configuration files
* **SimPy**: Discrete event simulation framework

Quick Start
-----------

.. code-block:: python

   from pathlib import Path
   from twin_model import OntologyDrivenModelBuilder
   import simpy
   
   # Load ontology and build model
   builder = OntologyDrivenModelBuilder(
       ontology_path=Path("ontology/twin_ontology.yaml"),
       manifest_dir=Path("manifests/")
   )
   
   # Build and configure model
   env = simpy.Environment()
   model = builder.build_model(env)
   
   # Run simulation
   env.run(until=100)
   
   # Get results
   results = model.get_results()

API Reference
-------------

The complete API documentation is automatically generated from the source code:

.. toctree::
   :maxdepth: 2

   api/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`