.. Virtual Twin documentation master file

======================================
Virtual Twin Documentation
======================================

.. image:: https://img.shields.io/badge/Python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

**Virtual Twin** is a comprehensive digital twin framework for manufacturing systems, 
enabling simulation, optimization, and intelligent recommendation capabilities.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   guides/index
   api/index
   autoapi/index

Overview
--------

The Virtual Twin module provides a powerful suite of tools for creating and managing 
digital twins of manufacturing systems. It combines state-of-the-art simulation, 
optimization, and analysis capabilities to help improve operational efficiency and 
decision-making.

Key Features
------------

* **Monte Carlo Simulation** - Run uncertainty analysis with parameter variations
* **Multi-Objective Optimization** - Use pymoo's NSGA-II algorithm for Pareto-optimal solutions
* **Bayesian ROI Analysis** - Calculate financial impact with PyMC probabilistic modeling
* **Real-time Synchronization** - Monitor synchronization health between virtual and physical systems
* **Interactive Visualizations** - Create insightful plots with Plotly
* **Configurable Parameters** - Centralized configuration management system

Core Components
---------------

Simulation & State Management
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* :mod:`twin.simulation_runner` - Execute what-if scenarios with Monte Carlo support
* :mod:`twin.actionable_parameters` - Manage and validate simulation parameters
* :mod:`twin.twin_state` - Track and synchronize virtual twin state
* :mod:`twin.config_transformer` - Transform parameters into simulation configurations
* :mod:`twin.config_manager` - Store and retrieve configuration history

Analysis & Optimization
^^^^^^^^^^^^^^^^^^^^^^^^

* :mod:`twin.optimization_engine` - Single/weighted multi-objective optimization
* :mod:`twin.recommendation_engine` - pymoo-based NSGA-II multi-objective optimization
* :mod:`twin.cost_impact_calculator` - PyMC-based Bayesian ROI analysis

Support Components
^^^^^^^^^^^^^^^^^^

* :mod:`twin.sync_health` - Monitor synchronization health
* :mod:`twin.line_coupling_model` - Model production line interactions
* :mod:`twin.config_loader` - Load and manage configuration files
* :mod:`twin.config_validator` - Validate configuration integrity

Visualization
^^^^^^^^^^^^^

* :mod:`twin.visualization.pareto_plots` - Pareto front visualizations
* :mod:`twin.visualization.time_series` - KPI trend analysis
* :mod:`twin.visualization.heatmaps` - Parameter sensitivity analysis
* :mod:`twin.visualization.financial_plots` - ROI and cost impact charts

Quick Start
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/your-org/virtual-twin.git
   cd virtual-twin

   # Install dependencies
   pip install -r requirements.txt

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from twin import SimulationRunner, ActionableParameters

   # Initialize the simulation runner
   runner = SimulationRunner(verbose=False)

   # Create and configure parameters
   params = ActionableParameters()
   params.set_value("micro_stop_probability", 0.05)

   # Run a simulation
   result = runner.run_simulation(params, duration_days=7)
   print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")

Monte Carlo Simulation
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Define uncertainty ranges
   uncertainty = {"micro_stop_probability": (-0.02, 0.02)}  # ±2%

   # Run Monte Carlo simulation
   mc_results = runner.run_monte_carlo_simulation(
       params, 
       uncertainty, 
       n_simulations=100
   )

   print(f"Mean OEE: {mc_results['statistics']['mean_oee']:.1f}%")
   print(f"95% CI: {mc_results['confidence_intervals']['mean_oee']}")

Multi-Objective Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from twin import RecommendationEngine, Objective

   # Define objectives
   objectives = [
       Objective(name="maximize_oee", direction="maximize", kpi_name="mean_oee"),
       Objective(name="minimize_cost", direction="minimize", kpi_name="total_cost")
   ]

   # Run optimization
   engine = RecommendationEngine()
   results = engine.optimize(
       objectives=objectives,
       population_size=50,
       generations=100
   )

   # Visualize Pareto front
   engine.visualize_pareto_front(results)

Configuration
-------------

The Virtual Twin system uses a centralized configuration management approach. 
All operational parameters are defined in ``twin/config/defaults.yaml``.

Key configuration sections:

* **database** - Database paths and connections
* **paths** - File and directory paths
* **simulation** - Simulation parameters and limits
* **parameters** - The 5 actionable parameters with bounds and defaults
* **scenarios** - Pre-configured test scenarios
* **cost_parameters** - Financial parameters for ROI calculations

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`