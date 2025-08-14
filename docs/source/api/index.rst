.. _api:

=============
API Reference
=============

This section contains the complete API reference for the Virtual Twin module.

The documentation is automatically generated from the source code docstrings using Sphinx AutoAPI.

.. toctree::
   :maxdepth: 2
   :caption: API Modules:

Core Modules
------------

These modules form the core of the Virtual Twin system:

.. autosummary::
   :toctree: generated
   :recursive:

   twin.simulation_runner
   twin.actionable_parameters
   twin.twin_state
   twin.config_transformer
   twin.config_manager
   twin.sync_health

Optimization Modules
--------------------

Modules for optimization and recommendation generation:

.. autosummary::
   :toctree: generated
   :recursive:

   twin.optimization_engine
   twin.recommendation_engine
   twin.cost_impact_calculator
   twin.line_coupling_model

Configuration Modules
---------------------

Configuration management and validation:

.. autosummary::
   :toctree: generated
   :recursive:

   twin.config_loader
   twin.config_validator

Visualization Modules
---------------------

Interactive visualization components:

.. autosummary::
   :toctree: generated
   :recursive:

   twin.visualization.pareto_plots
   twin.visualization.time_series
   twin.visualization.heatmaps
   twin.visualization.financial_plots