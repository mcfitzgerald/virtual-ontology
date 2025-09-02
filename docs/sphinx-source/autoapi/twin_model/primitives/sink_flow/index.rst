twin_model.primitives.sink_flow
===============================

.. py:module:: twin_model.primitives.sink_flow

.. autoapi-nested-parse::

   Sink flow primitive for collecting finished products and calculating OEE.

   This module implements sinks that collect finished products and provide
   comprehensive OEE (Overall Equipment Effectiveness) calculations.



Classes
-------

.. autoapisummary::

   twin_model.primitives.sink_flow.ProductionWindow
   twin_model.primitives.sink_flow.OEEMetrics
   twin_model.primitives.sink_flow.SinkFlow


Module Contents
---------------

.. py:class:: ProductionWindow

   Represents a production time window for metrics calculation.


   .. py:attribute:: timestamp
      :type:  float


   .. py:attribute:: duration
      :type:  float


   .. py:attribute:: volume
      :type:  float


   .. py:attribute:: good_volume
      :type:  float


   .. py:attribute:: scrap_volume
      :type:  float


   .. py:attribute:: downtime
      :type:  float


   .. py:attribute:: product_id
      :type:  str
      :value: 'default'



   .. py:property:: quality_rate
      :type: float


      Calculate quality rate for this window.


.. py:class:: OEEMetrics

   OEE metrics for a time period.


   .. py:attribute:: oee
      :type:  float


   .. py:attribute:: availability
      :type:  float


   .. py:attribute:: performance
      :type:  float


   .. py:attribute:: quality
      :type:  float


   .. py:attribute:: timestamp
      :type:  float


   .. py:attribute:: window_duration
      :type:  float


   .. py:method:: to_dict() -> dict[str, float]

      Convert to dictionary.



.. py:class:: SinkFlow(env: simpy.Environment, config: dict[str, Any], flow_capacity: twin_model.primitives.base_flow.FlowCapacity, collection_rate: float, collection_interval: float = 0.1)

   Bases: :py:obj:`twin_model.primitives.base_flow.BaseFlowPrimitive`


   Sink collecting finished products and calculating OEE.


   .. py:attribute:: collection_rate


   .. py:attribute:: collection_interval
      :value: 0.1



   .. py:attribute:: total_collected
      :value: 0.0



   .. py:attribute:: total_good
      :value: 0.0



   .. py:attribute:: total_scrap
      :value: 0.0



   .. py:attribute:: production_windows
      :type:  list[ProductionWindow]
      :value: []



   .. py:attribute:: current_window_start
      :value: 0.0



   .. py:attribute:: window_duration


   .. py:attribute:: oee_history
      :type:  list[OEEMetrics]
      :value: []



   .. py:attribute:: products_collected
      :type:  dict[str, float]


   .. py:attribute:: current_product


   .. py:attribute:: nominal_rate


   .. py:attribute:: upstream_equipment
      :type:  list[Any]
      :value: []



   .. py:method:: process_flow() -> Generator[Any, None, None]

      Collect products and track metrics.



   .. py:method:: window_tracker() -> Generator[Any, None, None]

      Track production windows for OEE calculation.



   .. py:method:: calculate_oee(window_minutes: float = 60) -> tuple[float, float, float, float]

      Calculate OEE components for time window.

      :param window_minutes: Time window in minutes

      :returns: Tuple of (OEE, Availability, Performance, Quality) as percentages



   .. py:method:: get_production_summary() -> dict[str, Any]

      Get production summary statistics.

      :returns: Dictionary with production summary



   .. py:method:: set_product(product_id: str) -> None

      Set current product being collected.

      :param product_id: Product identifier



