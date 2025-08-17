twin.visualization.heatmaps
===========================

.. py:module:: twin.visualization.heatmaps

.. autoapi-nested-parse::

   Heatmap Visualizations for Parameter Sensitivity and Correlations



Functions
---------

.. autoapisummary::

   twin.visualization.heatmaps.create_sensitivity_heatmap
   twin.visualization.heatmaps.calculate_sensitivity
   twin.visualization.heatmaps.create_correlation_heatmap
   twin.visualization.heatmaps.create_equipment_performance_heatmap


Module Contents
---------------

.. py:function:: create_sensitivity_heatmap(run_ids, db_path = 'data/mes_database.db')

   Create parameter sensitivity heatmap showing impact on KPIs

   :param run_ids: List of simulation run IDs to analyze
   :param db_path: Path to database

   :returns: Plotly heatmap figure


.. py:function:: calculate_sensitivity(run_ids, parameters, kpis, db_path)

   Calculate sensitivity matrix from runs


.. py:function:: create_correlation_heatmap(run_id, db_path = 'data/mes_database.db')

   Create correlation heatmap between different KPIs



.. py:function:: create_equipment_performance_heatmap(run_ids, db_path = 'data/mes_database.db')

   Create heatmap showing equipment performance across lines



