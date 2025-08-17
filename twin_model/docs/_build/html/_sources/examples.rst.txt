Examples
========

This section provides practical examples of using the SimPy Twin Model.

Basic Simulation
----------------

Run a simple simulation with default settings:

.. code-block:: python

   from twin_model import SimulationRunner

   runner = SimulationRunner()
   results = runner.run_simulation(duration_days=1, seed=42)
   
   print(f"Total units produced: {results.kpi_summary['total_units_produced']}")
   print(f"Mean OEE: {results.kpi_summary['mean_oee']:.1f}%")

Parameter Optimization
----------------------

Find optimal parameters for maximizing OEE:

.. code-block:: python

   from twin_model import SimulationRunner, ActionableParameters

   runner = SimulationRunner()
   best_oee = 0
   best_params = None

   # Test different parameter combinations
   for perf in [0.9, 1.0, 1.1]:
       for scrap in [0.8, 1.0, 1.2]:
           params = ActionableParameters(
               performance_factor=perf,
               scrap_multiplier=scrap
           )
           
           results = runner.run_simulation(
               parameters=params,
               duration_days=1,
               seed=42
           )
           
           oee = results.kpi_summary['mean_oee']
           if oee > best_oee:
               best_oee = oee
               best_params = (perf, scrap)
   
   print(f"Best OEE: {best_oee:.1f}%")
   print(f"Best parameters: performance={best_params[0]}, scrap={best_params[1]}")

Bottleneck Analysis
-------------------

Identify and analyze production bottlenecks:

.. code-block:: python

   from twin_model import SimulationRunner
   
   runner = SimulationRunner()
   results = runner.run_simulation(duration_days=1)
   
   # Analyze each line
   for line_id, summary in results.line_summaries.items():
       print(f"\n{line_id}:")
       print(f"  Bottleneck: {summary['bottleneck']}")
       print(f"  Line efficiency: {summary['line_efficiency']:.1f}%")
       
       # Check equipment utilization
       for eq_stats in summary['equipment_stats']:
           eq_id = eq_stats['equipment_id']
           oee = eq_stats['oee']
           state_durations = eq_stats['state_durations']
           
           # Calculate utilization
           total_time = sum(state_durations.values())
           if total_time > 0:
               running_pct = (state_durations.get('RUNNING', 0) / total_time) * 100
               blocked_pct = (state_durations.get('BLOCKED', 0) / total_time) * 100
               starved_pct = (state_durations.get('STARVED', 0) / total_time) * 100
               
               print(f"  {eq_id}:")
               print(f"    OEE: {oee:.1f}%")
               print(f"    Running: {running_pct:.1f}%")
               print(f"    Blocked: {blocked_pct:.1f}%")
               print(f"    Starved: {starved_pct:.1f}%")

Buffer Analysis
---------------

Monitor buffer levels and identify constraints:

.. code-block:: python

   from twin_model import SimulationRunner

   runner = SimulationRunner()
   results = runner.run_simulation(duration_days=1)
   
   for line_id, summary in results.line_summaries.items():
       print(f"\n{line_id} Buffer Analysis:")
       
       for buf_stats in summary['buffer_stats']:
           buf_id = buf_stats['buffer_id']
           capacity = buf_stats['capacity']
           max_level = buf_stats['max_level']
           utilization = buf_stats['utilization']
           starved_pct = buf_stats['starved_percentage']
           blocked_pct = buf_stats['blocked_percentage']
           
           print(f"  {buf_id}:")
           print(f"    Capacity: {capacity}")
           print(f"    Max level reached: {max_level}")
           print(f"    Current utilization: {utilization:.1f}%")
           print(f"    Time empty (starved): {starved_pct:.1f}%")
           print(f"    Time full (blocked): {blocked_pct:.1f}%")

Time Series Analysis
--------------------

Analyze OEE trends over time using MES data:

.. code-block:: python

   from twin_model import SimulationRunner
   import statistics

   runner = SimulationRunner()
   results = runner.run_simulation(duration_days=1)
   
   # Group MES data by line
   line_data = {}
   for snapshot in results.mes_data:
       line_id = snapshot['line_id']
       if line_id not in line_data:
           line_data[line_id] = []
       line_data[line_id].append({
           'time': snapshot['timestamp'],
           'oee': snapshot['line_oee']['oee']
       })
   
   # Analyze OEE stability
   for line_id, data in line_data.items():
       oee_values = [d['oee'] for d in data]
       
       if oee_values:
           mean_oee = statistics.mean(oee_values)
           stdev_oee = statistics.stdev(oee_values) if len(oee_values) > 1 else 0
           min_oee = min(oee_values)
           max_oee = max(oee_values)
           
           print(f"\n{line_id} OEE Statistics:")
           print(f"  Mean: {mean_oee:.1f}%")
           print(f"  Std Dev: {stdev_oee:.1f}%")
           print(f"  Min: {min_oee:.1f}%")
           print(f"  Max: {max_oee:.1f}%")

Multi-Scenario Comparison
--------------------------

Compare different operational scenarios:

.. code-block:: python

   from twin_model import SimulationRunner, ActionableParameters

   scenarios = {
       'Baseline': ActionableParameters(),
       'High Performance': ActionableParameters(
           performance_factor=1.2,
           micro_stop_probability=0.8
       ),
       'High Quality': ActionableParameters(
           scrap_multiplier=0.5,
           performance_factor=0.9
       ),
       'Tight Coupling': ActionableParameters(
           cascade_sensitivity=2.0
       ),
       'Loose Coupling': ActionableParameters(
           cascade_sensitivity=0.5
       )
   }

   runner = SimulationRunner()
   results_comparison = {}

   for scenario_name, params in scenarios.items():
       results = runner.run_simulation(
           parameters=params,
           duration_days=1,
           seed=42
       )
       
       results_comparison[scenario_name] = {
           'oee': results.kpi_summary['mean_oee'],
           'output': results.kpi_summary['total_units_produced'],
           'scrap': results.kpi_summary['total_units_scrapped']
       }

   # Display comparison
   print("Scenario Comparison:")
   print("-" * 60)
   print(f"{'Scenario':<20} {'OEE':<10} {'Output':<10} {'Scrap':<10}")
   print("-" * 60)
   
   for scenario, metrics in results_comparison.items():
       print(f"{scenario:<20} {metrics['oee']:<10.1f} {metrics['output']:<10.0f} {metrics['scrap']:<10.0f}")