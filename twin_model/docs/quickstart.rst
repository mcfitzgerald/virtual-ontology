Quick Start Guide
=================

This guide will help you get started with the Twin Model framework.

Installation
------------

First, ensure you have the required dependencies:

.. code-block:: bash

   pip install simpy pyyaml pandas numpy

Basic Usage
-----------

Simple Simulation
^^^^^^^^^^^^^^^^^

Here's a minimal example to run a simulation:

.. code-block:: python

   import simpy
   from twin_model.model_builder import OntologyDrivenModelBuilder
   from pathlib import Path

   # Load ontology and manifests
   builder = OntologyDrivenModelBuilder(
       ontology_path=Path("ontology/twin_ontology.yaml"),
       manifest_dir=Path("manifests")
   )

   # Create SimPy environment
   env = simpy.Environment()

   # Build the model
   model = builder.build_model(env)

   # Run for 1 day (1440 minutes)
   env.run(until=1440)

   # Get results
   for primitive_id, primitive in builder.primitives.items():
       if hasattr(primitive, 'observables'):
           print(f"{primitive_id}: {len(primitive.observables)} events")

Performance-Optimized Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For production use with large simulations:

.. code-block:: python

   from twin_model.config import PerformanceConfig, ConfigPreset
   from twin_model.primitives.base import SamplingConfig
   
   # Choose appropriate preset
   config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
   
   # Apply sampling to primitives
   sampling = SamplingConfig(
       mode=config.simulation_mode,
       sampling_rate=config.sampling_rate,
       buffer_size=config.observable_buffer_size
   )
   
   # Build model (same as before)
   builder = OntologyDrivenModelBuilder(
       ontology_path=Path("ontology/twin_ontology.yaml"),
       manifest_dir=Path("manifests")
   )
   
   env = simpy.Environment()
   model = builder.build_model(env)
   
   # Apply sampling configuration
   for primitive in builder.primitives.values():
       if hasattr(primitive, 'sampling_config'):
           primitive.sampling_config = sampling
   
   # Run 30-day simulation
   env.run(until=30 * 24 * 60)

Working with Observables
------------------------

Extracting Events
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Collect all observables
   all_observables = []
   
   for primitive_id, primitive in builder.primitives.items():
       if hasattr(primitive, 'observable_buffer'):
           # From optimized buffer
           events = list(primitive.observable_buffer.buffer)
       elif hasattr(primitive, 'observables'):
           # From standard list
           events = primitive.observables
       else:
           continue
           
       for event in events:
           event['primitive_id'] = primitive_id
           all_observables.append(event)

Converting to MES Format
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from twin_model.transduction.mes_transducer import MESTransducer
   
   # Create transducer
   transducer = MESTransducer(time_bucket=5)  # 5-minute buckets
   
   # Process observables to MES format
   mes_df = transducer.process_observables(
       all_observables,
       builder.manifests
   )
   
   # Save to CSV
   mes_df.to_csv("simulation_results.csv", index=False)

Configuration Options
---------------------

Performance Presets
^^^^^^^^^^^^^^^^^^^

Choose the right preset for your use case:

.. code-block:: python

   from twin_model.config import ConfigPreset
   
   # For debugging and development
   config = PerformanceConfig.from_preset(ConfigPreset.DEVELOPMENT)
   
   # For production with balanced performance
   config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
   
   # For fastest execution
   config = PerformanceConfig.from_preset(ConfigPreset.FAST)
   
   # For minimal memory usage
   config = PerformanceConfig.from_preset(ConfigPreset.MEMORY_OPTIMIZED)
   
   # For very long simulations (30+ days)
   config = PerformanceConfig.from_preset(ConfigPreset.LONG_RUNNING)

Custom Configuration
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from twin_model.config import PerformanceConfig
   from twin_model.primitives.base import SimulationMode
   
   # Create custom configuration
   config = PerformanceConfig(
       name="custom",
       simulation_mode=SimulationMode.PRODUCTION,
       observable_buffer_size=1000,
       sampling_rate=10,  # Keep 1 in 10 events
       aggregation_interval=60,  # Aggregate every 60 minutes
       batch_size=100,
       cache_size=10000,
       checkpoint_interval=1440,  # Daily checkpoints
       max_memory_mb=500.0,
       enable_profiling=False
   )

Database Integration
--------------------

Storing Results
^^^^^^^^^^^^^^^

.. code-block:: python

   from database.integration import TwinDatabaseIntegration
   
   # Create integration
   integration = TwinDatabaseIntegration()
   
   # Run simulation and store in database
   run_id = integration.run_simulation_to_db(
       run_type="experiment",
       parameters={'param1': 1.5},
       days=7
   )
   
   print(f"Simulation stored as: {run_id}")

Running Experiments
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Run an experiment with parameter changes
   experiment_id = integration.run_experiment(
       name="Optimize OEE",
       hypothesis="Increasing performance_factor improves OEE",
       parameter_changes={'performance_factor': 1.2},
       days=7,
       num_runs=3
   )

Next Steps
----------

- Explore the :doc:`architecture` documentation for system design details
- Review :doc:`performance` for optimization techniques
- Check the API reference for detailed class documentation
- See example notebooks in the repository for practical applications