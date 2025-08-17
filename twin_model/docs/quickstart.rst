Quickstart Guide
================

Installation
------------

First, install the required dependencies:

.. code-block:: bash

   pip install simpy

Basic Usage
-----------

The simplest way to run a simulation is using the default configuration:

.. code-block:: python

   from twin_model import SimulationRunner

   # Create runner with default 3-line configuration
   runner = SimulationRunner()

   # Run simulation for 7 days
   results = runner.run_simulation(duration_days=7)

   # Access results
   print(f"Mean OEE: {results.kpi_summary['mean_oee']:.1f}%")
   print(f"Total units produced: {results.kpi_summary['total_units_produced']}")

Adjusting Parameters
--------------------

The model provides 5 actionable parameters that affect system performance:

.. code-block:: python

   from twin_model import ActionableParameters

   params = ActionableParameters(
       micro_stop_probability=0.8,   # Reduce failure frequency
       performance_factor=1.1,        # 10% faster production
       scrap_multiplier=0.9,         # 10% less scrap
       material_reliability=1.0,     # Normal material flow
       cascade_sensitivity=1.5       # Tighter coupling (smaller buffers)
   )

   results = runner.run_simulation(parameters=params)

Custom Configuration
--------------------

Create custom equipment and line configurations:

.. code-block:: python

   from twin_model import (
       SimulationConfig, LineConfig, EquipmentConfig, 
       EquipmentType, SimulationRunner
   )

   # Define equipment
   filler = EquipmentConfig(
       equipment_id="CUSTOM_FILLER",
       equipment_type=EquipmentType.FILLER,
       base_rate=100.0,  # units per minute
       mtbf=600.0,       # minutes between failures
       mttr=30.0,        # minutes to repair
       downstream_buffer_capacity=300
   )

   packer = EquipmentConfig(
       equipment_id="CUSTOM_PACKER",
       equipment_type=EquipmentType.PACKER,
       base_rate=95.0,
       mtbf=800.0,
       mttr=20.0,
       upstream_buffer_capacity=300,
       downstream_buffer_capacity=200
   )

   # Create line configuration
   line_config = LineConfig(
       line_id="CUSTOM_LINE",
       equipment_configs=[filler, packer],
       source_arrival_rate=110.0
   )

   # Create simulation configuration
   config = SimulationConfig(
       duration_days=7,
       mes_logging_interval=5.0,
       line_configs=[line_config],
       random_seed=42
   )

   # Run simulation
   runner = SimulationRunner(config)
   results = runner.run_simulation()

Analyzing Results
-----------------

The simulation returns comprehensive results including:

.. code-block:: python

   # Overall KPIs
   print(f"Mean OEE: {results.kpi_summary['mean_oee']:.1f}%")
   print(f"Mean Availability: {results.kpi_summary['mean_availability']:.1f}%")
   print(f"Mean Performance: {results.kpi_summary['mean_performance']:.1f}%")
   print(f"Mean Quality: {results.kpi_summary['mean_quality']:.1f}%")

   # Line-specific summaries
   for line_id, summary in results.line_summaries.items():
       print(f"\n{line_id}:")
       print(f"  Total Input: {summary['total_input']}")
       print(f"  Total Output: {summary['total_output']}")
       print(f"  Line OEE: {summary['line_oee']['oee']:.1f}%")
       print(f"  Bottleneck: {summary['bottleneck']}")

   # MES data for time-series analysis
   for snapshot in results.mes_data[:5]:  # First 5 snapshots
       print(f"Time {snapshot['timestamp']:.1f}: {snapshot['line_id']} OEE={snapshot['line_oee']['oee']:.1f}%")

Parameter Sweep
---------------

Run multiple simulations to analyze parameter sensitivity:

.. code-block:: python

   parameter_ranges = {
       'performance_factor': [0.8, 1.0, 1.2],
       'scrap_multiplier': [0.5, 1.0, 1.5]
   }

   results = runner.run_parameter_sweep(
       parameter_ranges=parameter_ranges,
       duration_days=1,
       replications=3
   )

   for result in results:
       params = result['parameters']
       oee = result['kpis']['mean_oee']
       print(f"Performance={params['performance_factor']}, Scrap={params['scrap_multiplier']}: OEE={oee:.1f}%")