twin.visualization.time_series
==============================

.. py:module:: twin.visualization.time_series

.. autoapi-nested-parse::

   Time Series Visualization for KPI Trends



Functions
---------

.. autoapisummary::

   twin.visualization.time_series.plot_kpi_trends
   twin.visualization.time_series.get_time_series_data
   twin.visualization.time_series.plot_kpi_comparison


Module Contents
---------------

.. py:function:: plot_kpi_trends(run_ids: List[str], kpis: List[str] = ['oee', 'availability', 'performance', 'quality'], db_path: str = 'data/mes_database.db') -> plotly.graph_objects.Figure

   Create interactive time series plots for KPI trends

   :param run_ids: List of simulation run IDs to plot
   :param kpis: List of KPIs to visualize
   :param db_path: Path to database

   :returns: Plotly figure with time series plots


.. py:function:: get_time_series_data(run_id: str, db_path: str) -> List[Dict[str, Any]]

   Get time series data for a run


.. py:function:: plot_kpi_comparison(run_ids: List[str], kpi: str = 'oee', db_path: str = 'data/mes_database.db') -> plotly.graph_objects.Figure

   Create comparison plot for a single KPI across multiple runs



