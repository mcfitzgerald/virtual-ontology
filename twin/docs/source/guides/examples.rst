.. _examples:

========
Examples
========

This page provides practical examples of using the Virtual Twin system for various scenarios.

Complete Example Scripts
------------------------

All example scripts are available in the ``twin/examples/`` directory:

* ``basic_simulation.py`` - Simple what-if simulation
* ``monte_carlo_example.py`` - Uncertainty analysis with Monte Carlo
* ``optimization_example.py`` - Multi-objective optimization
* ``financial_analysis.py`` - ROI and cost impact analysis
* ``pareto_visualization.py`` - Interactive Pareto front exploration

Basic Simulation Example
------------------------

Running a Simple What-If Scenario
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin import SimulationRunner, ActionableParameters

   # Initialize the runner
   runner = SimulationRunner(verbose=False)

   # Create parameters and modify one
   params = ActionableParameters()
   params.set_value("micro_stop_probability", 0.05)  # 50% reduction

   # Run simulation
   result = runner.run_simulation(
       params, 
       duration_days=7,
       notes="Testing micro-stop reduction"
   )

   # Display results
   print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")
   print(f"Good Units: {result.kpi_summary['total_good_units']:,}")

Comparing Multiple Scenarios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   scenarios = {
       "baseline": {},
       "reduced_stops": {"micro_stop_probability": 0.05},
       "improved_performance": {"performance_factor": 0.95},
       "combined": {
           "micro_stop_probability": 0.05,
           "performance_factor": 0.95
       }
   }

   results = {}
   for name, changes in scenarios.items():
       params = ActionableParameters()
       for param, value in changes.items():
           params.set_value(param, value)
       
       results[name] = runner.run_simulation(params, duration_days=7)
       print(f"{name}: OEE = {results[name].kpi_summary['mean_oee']:.1f}%")

Monte Carlo Analysis
--------------------

Basic Uncertainty Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin import SimulationRunner, ActionableParameters

   runner = SimulationRunner(verbose=False)
   params = ActionableParameters()

   # Define uncertainty ranges (as deltas)
   uncertainty = {
       "micro_stop_probability": (-0.02, 0.02),  # ±2%
       "performance_factor": (-0.05, 0.05),      # ±5%
       "scrap_multiplier": (-0.1, 0.1),          # ±10%
   }

   # Run Monte Carlo
   mc_results = runner.run_monte_carlo_simulation(
       parameters=params,
       uncertainty_ranges=uncertainty,
       n_simulations=100,
       duration_days=7
   )

   # Display statistics
   stats = mc_results['statistics']
   ci = mc_results['confidence_intervals']
   
   print(f"Mean OEE: {stats['mean_oee_mean']:.1f}% ± {stats['mean_oee_std']:.1f}%")
   print(f"95% CI: [{ci['mean_oee'][0]:.1f}%, {ci['mean_oee'][1]:.1f}%]")

Advanced Monte Carlo with Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import plotly.graph_objects as go
   from plotly.subplots import make_subplots

   # Run Monte Carlo simulation
   mc_results = runner.run_monte_carlo_simulation(
       parameters=params,
       uncertainty_ranges=uncertainty,
       n_simulations=500,
       duration_days=30
   )

   # Create visualization
   fig = make_subplots(
       rows=2, cols=2,
       subplot_titles=('OEE Distribution', 'Downtime Distribution',
                       'Production Output', 'Quality Metrics')
   )

   # OEE histogram
   fig.add_trace(
       go.Histogram(x=mc_results['results']['mean_oee'], nbinsx=30),
       row=1, col=1
   )

   # Downtime histogram
   fig.add_trace(
       go.Histogram(x=mc_results['results']['downtime_percentage'], nbinsx=30),
       row=1, col=2
   )

   # Production scatter
   fig.add_trace(
       go.Scatter(
           x=mc_results['results']['mean_oee'],
           y=mc_results['results']['total_good_units'],
           mode='markers'
       ),
       row=2, col=1
   )

   # Quality box plot
   fig.add_trace(
       go.Box(y=mc_results['results']['mean_quality'], name='Quality'),
       row=2, col=2
   )

   fig.update_layout(height=800, showlegend=False)
   fig.show()

Multi-Objective Optimization
-----------------------------

Basic Pareto Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin import RecommendationEngine, Objective

   engine = RecommendationEngine()

   # Define competing objectives
   objectives = [
       Objective(
           name="maximize_oee",
           direction="maximize",
           kpi_name="mean_oee"
       ),
       Objective(
           name="minimize_variability",
           direction="minimize",
           kpi_name="oee_std"
       )
   ]

   # Run optimization
   results = engine.optimize(
       objectives=objectives,
       population_size=100,
       generations=50
   )

   # Get Pareto front
   pareto_solutions = results['pareto_front']
   print(f"Found {len(pareto_solutions)} Pareto-optimal solutions")

   # Display top solutions
   for i, sol in enumerate(pareto_solutions[:5]):
       print(f"Solution {i+1}:")
       print(f"  OEE: {sol['objectives']['mean_oee']:.1f}%")
       print(f"  Variability: {sol['objectives']['oee_std']:.2f}")
       print(f"  Parameters: {sol['parameters']}")

Scenario-Based Recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get recommendations for specific scenarios
   scenarios = [
       "maximize_oee",
       "maximize_throughput",
       "minimize_downtime",
       "balanced_improvement"
   ]

   for scenario in scenarios:
       result = engine.recommend_for_scenario(scenario)
       
       if result and 'recommended_parameters' in result:
           print(f"\n{scenario}:")
           print("Recommended changes:")
           for param, value in result['recommended_parameters'].items():
               current = params.get_value(param)
               change = ((value - current) / current) * 100
               print(f"  {param}: {current:.3f} → {value:.3f} ({change:+.1f}%)")
           
           if 'expected_improvements' in result:
               imp = result['expected_improvements']
               print(f"Expected OEE gain: {imp.get('oee_improvement', 0)*100:.1f}%")

Financial Impact Analysis
-------------------------

Basic ROI Calculation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin import CostImpactCalculator

   calculator = CostImpactCalculator()

   # Run baseline and improved scenarios
   baseline = runner.create_baseline(duration_days=30)
   
   params = ActionableParameters()
   params.set_value("micro_stop_probability", 0.07)
   params.set_value("performance_factor", 0.90)
   improved = runner.run_simulation(params, duration_days=30)

   # Calculate financial impact
   impact = calculator.calculate_simple_roi(
       baseline_simulation=baseline,
       improved_simulation=improved,
       implementation_cost=150000,
       time_horizon_days=365
   )

   print(f"Annual Revenue Impact: ${impact['annual_revenue_impact']:,.0f}")
   print(f"ROI: {impact['roi_percentage']:.1f}%")
   print(f"Payback Period: {impact['payback_days']:.0f} days")

Bayesian ROI Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Bayesian analysis with uncertainty quantification
   bayesian_results = calculator.calculate_bayesian_roi(
       baseline_simulation=baseline,
       improved_simulation=improved,
       implementation_cost=150000,
       cost_uncertainty=0.2,  # 20% uncertainty
       revenue_per_unit=25.50,
       time_horizon_days=365,
       n_samples=2000
   )

   # Display credible intervals
   print(f"Expected ROI: {bayesian_results['expected_roi']:.1f}%")
   print(f"95% Credible Interval: [{bayesian_results['roi_ci_lower']:.1f}%, "
         f"{bayesian_results['roi_ci_upper']:.1f}%]")
   print(f"Probability of Positive ROI: {bayesian_results['prob_positive_roi']:.2%}")

   # Visualize posterior distribution
   import plotly.graph_objects as go

   fig = go.Figure()
   fig.add_trace(go.Histogram(
       x=bayesian_results['posterior_samples']['roi'],
       nbinsx=50,
       name='ROI Distribution'
   ))
   fig.add_vline(x=0, line_dash="dash", line_color="red")
   fig.update_layout(
       title="Posterior ROI Distribution",
       xaxis_title="ROI (%)",
       yaxis_title="Frequency"
   )
   fig.show()

Advanced Visualizations
-----------------------

Interactive Parameter Explorer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import plotly.graph_objects as go
   from plotly.subplots import make_subplots
   import numpy as np

   # Create parameter sweep
   param_name = "micro_stop_probability"
   param_range = np.linspace(0.05, 0.15, 20)
   
   results = []
   for value in param_range:
       params = ActionableParameters()
       params.set_value(param_name, value)
       result = runner.run_simulation(params, duration_days=7)
       results.append({
           'value': value,
           'oee': result.kpi_summary['mean_oee'],
           'downtime': result.kpi_summary['downtime_percentage'],
           'units': result.kpi_summary['total_good_units']
       })

   # Create subplots
   fig = make_subplots(
       rows=2, cols=2,
       subplot_titles=('OEE Impact', 'Downtime Impact', 
                       'Production Impact', 'Combined View')
   )

   # OEE trace
   fig.add_trace(
       go.Scatter(x=[r['value'] for r in results],
                  y=[r['oee'] for r in results],
                  mode='lines+markers', name='OEE'),
       row=1, col=1
   )

   # Downtime trace
   fig.add_trace(
       go.Scatter(x=[r['value'] for r in results],
                  y=[r['downtime'] for r in results],
                  mode='lines+markers', name='Downtime'),
       row=1, col=2
   )

   # Production trace
   fig.add_trace(
       go.Scatter(x=[r['value'] for r in results],
                  y=[r['units'] for r in results],
                  mode='lines+markers', name='Units'),
       row=2, col=1
   )

   # Combined normalized view
   oee_norm = [(r['oee'] - min(r['oee'] for r in results)) / 
               (max(r['oee'] for r in results) - min(r['oee'] for r in results)) 
               for r in results]
   units_norm = [(r['units'] - min(r['units'] for r in results)) / 
                 (max(r['units'] for r in results) - min(r['units'] for r in results)) 
                 for r in results]
   
   fig.add_trace(
       go.Scatter(x=[r['value'] for r in results], y=oee_norm,
                  mode='lines', name='OEE (normalized)'),
       row=2, col=2
   )
   fig.add_trace(
       go.Scatter(x=[r['value'] for r in results], y=units_norm,
                  mode='lines', name='Units (normalized)'),
       row=2, col=2
   )

   fig.update_layout(height=800, title_text=f"Sensitivity Analysis: {param_name}")
   fig.show()

Best Practices
--------------

Parameter Validation
~~~~~~~~~~~~~~~~~~~~

Always validate parameters before running simulations:

.. code-block:: python

   params = ActionableParameters()
   
   # Check bounds before setting
   param_name = "micro_stop_probability"
   new_value = 0.05
   
   bounds = params.get_bounds(param_name)
   if bounds['min'] <= new_value <= bounds['max']:
       params.set_value(param_name, new_value)
   else:
       print(f"Value {new_value} outside bounds [{bounds['min']}, {bounds['max']}]")

   # Use describe() to see all parameters
   params.describe()

Error Handling
~~~~~~~~~~~~~~

Implement proper error handling for production use:

.. code-block:: python

   from typing import Optional
   import logging

   def run_safe_simulation(params: ActionableParameters, 
                          duration: int = 7) -> Optional[SimulationRun]:
       """Run simulation with error handling."""
       try:
           runner = SimulationRunner(verbose=False)
           result = runner.run_simulation(params, duration_days=duration)
           
           # Validate results
           if result.kpi_summary['mean_oee'] > 100:
               logging.warning(f"Invalid OEE: {result.kpi_summary['mean_oee']}")
               return None
               
           return result
           
       except Exception as e:
           logging.error(f"Simulation failed: {e}")
           return None

Performance Tips
~~~~~~~~~~~~~~~~

For large-scale analyses:

.. code-block:: python

   # 1. Use parallel processing for Monte Carlo
   mc_results = runner.run_monte_carlo_simulation(
       parameters=params,
       uncertainty_ranges=uncertainty,
       n_simulations=1000,
       parallel=True,  # Enable parallel processing
       n_workers=4      # Number of parallel workers
   )

   # 2. Cache baseline results
   baseline = runner.create_baseline(duration_days=30)
   baseline_id = baseline.run_id  # Store this for reuse

   # 3. Batch parameter sweeps
   param_sets = [...]  # List of parameter configurations
   results = runner.batch_simulate(param_sets, duration_days=7)

   # 4. Use appropriate population sizes for optimization
   # Smaller for quick exploration
   quick_results = engine.optimize(objectives, population_size=20, generations=10)
   
   # Larger for production
   final_results = engine.optimize(objectives, population_size=200, generations=100)

Next Steps
----------

1. Explore the full example scripts in ``twin/examples/``
2. Review the API documentation for detailed method signatures
3. Check the configuration guide for customization options
4. See the migration guide for recent changes