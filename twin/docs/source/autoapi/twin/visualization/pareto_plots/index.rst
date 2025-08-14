twin.visualization.pareto_plots
===============================

.. py:module:: twin.visualization.pareto_plots

.. autoapi-nested-parse::

   Pareto Front Visualization for Multi-objective Optimization



Functions
---------

.. autoapisummary::

   twin.visualization.pareto_plots.create_pareto_plot
   twin.visualization.pareto_plots.identify_pareto_front
   twin.visualization.pareto_plots.create_pareto_3d


Module Contents
---------------

.. py:function:: create_pareto_plot(run_ids, objectives = ['oee', 'energy'], db_path = 'data/mes_database.db')

   Create interactive Pareto front visualization

   :param run_ids: List of simulation run IDs to compare
   :param objectives: List of objectives to plot (default: OEE vs Energy)
   :param db_path: Path to database

   :returns: Plotly figure object


.. py:function:: identify_pareto_front(points)

   Identify Pareto optimal points (non-dominated solutions)
   Assumes maximizing OEE and minimizing energy


.. py:function:: create_pareto_3d(run_ids, objectives = ['oee', 'energy', 'quality'], db_path = 'data/mes_database.db')

   Create 3D Pareto front visualization for three objectives



