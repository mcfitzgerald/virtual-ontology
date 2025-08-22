twin_model.primitives.sink
==========================

.. py:module:: twin_model.primitives.sink

.. autoapi-nested-parse::

   Sink primitive for product collection in manufacturing.

   This module provides a sink primitive that collects finished products
   exiting the production system. It tracks throughput, quality metrics,
   and delivery performance.



Classes
-------

.. autoapisummary::

   twin_model.primitives.sink.CollectedProduct
   twin_model.primitives.sink.SinkPrimitive


Module Contents
---------------

.. py:class:: CollectedProduct

   Product collected by sink with metadata.

   .. attribute:: product_id

      Product identifier

   .. attribute:: order_id

      Associated production order

   .. attribute:: collection_time

      Simulation time when collected

   .. attribute:: quality

      Quality status

   .. attribute:: lead_time

      Time from order to collection

   .. attribute:: metadata

      Additional product data


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: order_id
      :type:  Optional[str]


   .. py:attribute:: collection_time
      :type:  float


   .. py:attribute:: quality
      :type:  str
      :value: 'good'



   .. py:attribute:: lead_time
      :type:  Optional[float]
      :value: None



   .. py:attribute:: metadata
      :type:  Dict[str, Any]


.. py:class:: SinkPrimitive(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, upstream: Optional[Any] = None)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Generic sink that collects finished products.

   Emits observables for:
   - Product collection events
   - Throughput metrics
   - Quality statistics
   - Order fulfillment
   - Delivery performance

   Initialize sink with configuration.

   :param env: SimPy environment
   :param config: Sink configuration containing:
                  - collection_rate: Maximum collection rate (units/minute)
                  - quality_threshold: Minimum quality score for acceptance
                  - target_throughput: Expected throughput for KPI
                  - order_tracking: Whether to track order fulfillment
   :param upstream: Input buffer or equipment


   .. py:attribute:: upstream
      :value: None



   .. py:attribute:: collection_rate


   .. py:attribute:: quality_threshold


   .. py:attribute:: target_throughput


   .. py:attribute:: order_tracking


   .. py:attribute:: collected_products
      :type:  List[CollectedProduct]
      :value: []



   .. py:attribute:: total_collected
      :value: 0



   .. py:attribute:: total_rejected
      :value: 0



   .. py:attribute:: products_by_type
      :type:  Dict[str, int]


   .. py:attribute:: products_by_order
      :type:  Dict[str, int]


   .. py:attribute:: throughput_history
      :type:  List[float]
      :value: []



   .. py:attribute:: quality_history
      :type:  List[float]
      :value: []



   .. py:attribute:: pending_orders
      :type:  Dict[str, Dict[str, Any]]


   .. py:attribute:: completed_orders
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:method:: start() -> None

      Start the sink collection process.



   .. py:method:: collect() -> Generator

      Main collection process for products.



   .. py:method:: monitor_process() -> Generator

      Background monitoring process.



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get sink statistics.

      :returns: Dictionary of sink metrics



   .. py:method:: get_order_metrics() -> Dict[str, Any]

      Get order fulfillment metrics.

      :returns: Dictionary of order-related metrics



