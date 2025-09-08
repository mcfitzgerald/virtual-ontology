twin_model.primitives.source_flow
=================================

.. py:module:: twin_model.primitives.source_flow

.. autoapi-nested-parse::

   Source flow primitive for continuous material generation.

   This module implements sources that generate continuous material flow
   based on production orders or continuous generation patterns.



Attributes
----------

.. autoapisummary::

   twin_model.primitives.source_flow.logger


Classes
-------

.. autoapisummary::

   twin_model.primitives.source_flow.ProductionOrder
   twin_model.primitives.source_flow.SourceFlow


Module Contents
---------------

.. py:data:: logger

.. py:class:: ProductionOrder

   Production order for material generation.


   .. py:attribute:: order_id
      :type:  str


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: target_volume
      :type:  float


   .. py:attribute:: due_time
      :type:  float


   .. py:attribute:: priority
      :type:  int
      :value: 0



   .. py:attribute:: completed_volume
      :type:  float
      :value: 0.0



   .. py:property:: remaining_volume
      :type: float


      Calculate remaining volume to complete.


   .. py:property:: completion_percentage
      :type: float


      Calculate order completion percentage.


.. py:class:: SourceFlow(env: simpy.Environment, config: dict[str, Any], flow_capacity: twin_model.primitives.base_flow.FlowCapacity, generation_rate: float, generation_interval: float = 0.1)

   Bases: :py:obj:`twin_model.primitives.base_flow.BaseFlowPrimitive`


   Source generating continuous material flow.


   .. py:attribute:: generation_rate


   .. py:attribute:: generation_interval
      :value: 0.1



   .. py:attribute:: order_queue
      :type:  list[ProductionOrder]
      :value: []



   .. py:attribute:: current_order
      :type:  ProductionOrder | None
      :value: None



   .. py:attribute:: completed_orders
      :type:  list[ProductionOrder]
      :value: []



   .. py:attribute:: continuous_mode


   .. py:attribute:: default_product


   .. py:method:: process_flow() -> Generator[Any, None, None]

      Generate material based on orders or continuously.



   .. py:method:: add_order(order: ProductionOrder) -> None

      Add a production order to the queue.

      :param order: Production order to add



   .. py:method:: cancel_order(order_id: str) -> bool

      Cancel a production order.

      :param order_id: ID of order to cancel

      :returns: True if order was cancelled, False if not found



   .. py:method:: get_queue_status() -> dict[str, Any]

      Get current queue status.

      :returns: Dictionary with queue status information



