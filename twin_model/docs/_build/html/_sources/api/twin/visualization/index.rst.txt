twin.visualization
==================

.. py:module:: twin.visualization

.. autoapi-nested-parse::

   Visualization Module for Virtual Twin
   Interactive plots using Plotly



Submodules
----------

.. toctree::
   :maxdepth: 1

   /api/twin/visualization/financial_plots/index
   /api/twin/visualization/heatmaps/index
   /api/twin/visualization/pareto_plots/index
   /api/twin/visualization/time_series/index


Functions
---------

.. autoapisummary::

   twin.visualization.create_pareto_plot
   twin.visualization.plot_kpi_trends
   twin.visualization.create_sensitivity_heatmap
   twin.visualization.plot_roi_distribution


Package Contents
----------------

.. py:function:: create_pareto_plot(run_ids: List[str], objectives: List[str] = ['oee', 'energy'], db_path: str = 'data/mes_database.db') -> plotly.graph_objects.Figure

   Create interactive Pareto front visualization

   :param run_ids: List of simulation run IDs to compare
   :param objectives: List of objectives to plot (default: OEE vs Energy)
   :param db_path: Path to database

   :returns: Plotly figure object


.. py:function:: plot_kpi_trends(run_ids: List[str], kpis: List[str] = ['oee', 'availability', 'performance', 'quality'], db_path: str = 'data/mes_database.db') -> plotly.graph_objects.Figure

   Create interactive time series plots for KPI trends

   :param run_ids: List of simulation run IDs to plot
   :param kpis: List of KPIs to visualize
   :param db_path: Path to database

   :returns: Plotly figure with time series plots


.. py:function:: create_sensitivity_heatmap(run_ids: List[str], db_path: str = 'data/mes_database.db') -> plotly.graph_objects.Figure

   Create parameter sensitivity heatmap showing impact on KPIs

   :param run_ids: List of simulation run IDs to analyze
   :param db_path: Path to database

   :returns: Plotly heatmap figure


.. py:function:: plot_roi_distribution(roi_summary: Dict[str, Any]) -> plotly.graph_objects.Figure

   Create ROI distribution visualization with confidence intervals

   :param roi_summary: ROI calculation results from CostImpactCalculator

   :returns: Plotly figure with ROI distributions


