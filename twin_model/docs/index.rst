.. SimPy Twin Model documentation master file

SimPy Twin Model Documentation
===============================

A discrete event simulation model for manufacturing production lines using SimPy.

This model simulates material flow through production lines with realistic equipment behavior,
failures, and buffer management. It provides configurable parameters for optimization and
analysis of manufacturing systems.

Key Features
------------

* **Realistic Material Flow**: Discrete units flow through equipment and buffers
* **Equipment Modeling**: Configurable failure rates (MTBF/MTTR), production rates, and quality
* **Buffer Management**: Work-in-process tracking with starvation and blockage detection
* **Parameter Sensitivity**: 5 actionable parameters with measurable impact on OEE
* **Multi-Line Support**: Simulate multiple production lines simultaneously
* **MES Data Logging**: Capture equipment states and metrics at regular intervals

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   api/modules
   examples

Quick Example
-------------

.. code-block:: python

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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
