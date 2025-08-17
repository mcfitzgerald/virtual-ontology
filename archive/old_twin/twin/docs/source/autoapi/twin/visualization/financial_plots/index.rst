twin.visualization.financial_plots
==================================

.. py:module:: twin.visualization.financial_plots

.. autoapi-nested-parse::

   Financial Visualization for ROI and Cost Impact



Functions
---------

.. autoapisummary::

   twin.visualization.financial_plots.plot_roi_distribution
   twin.visualization.financial_plots.plot_sensitivity_tornado
   twin.visualization.financial_plots.plot_roi_waterfall
   twin.visualization.financial_plots.plot_risk_reward_quadrant


Module Contents
---------------

.. py:function:: plot_roi_distribution(roi_summary)

   Create ROI distribution visualization with confidence intervals

   :param roi_summary: ROI calculation results from CostImpactCalculator

   :returns: Plotly figure with ROI distributions


.. py:function:: plot_sensitivity_tornado(parameter_impacts, baseline_value = 100000)

   Create tornado chart for parameter sensitivity on financial impact



.. py:function:: plot_roi_waterfall(cost_breakdown)

   Create waterfall chart showing ROI components



.. py:function:: plot_risk_reward_quadrant(scenarios)

   Create risk-reward quadrant chart for different scenarios



