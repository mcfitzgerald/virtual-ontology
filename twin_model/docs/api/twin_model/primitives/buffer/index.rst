twin_model.primitives.buffer
============================

.. py:module:: twin_model.primitives.buffer

.. autoapi-nested-parse::

   Buffer primitive for material storage between equipment.

   This module provides a buffer primitive that represents material storage
   locations (queues, conveyors, accumulation tables) between processing equipment.
   It emits observables about material flow, levels, and dwell times.



Classes
-------

.. autoapisummary::

   twin_model.primitives.buffer.BufferItem
   twin_model.primitives.buffer.BufferPrimitive


Module Contents
---------------

.. py:class:: BufferItem

   Item stored in buffer with metadata for tracking.

   .. attribute:: product_id

      Product identifier

   .. attribute:: entry_time

      Simulation time when item entered buffer

   .. attribute:: quality

      Quality status (good/scrap)

   .. attribute:: metadata

      Additional item-specific data


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: entry_time
      :type:  float


   .. py:attribute:: quality
      :type:  str
      :value: 'good'



   .. py:attribute:: metadata
      :type:  Dict[str, Any]


.. py:class:: BufferPrimitive(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Generic buffer for material storage.

   Emits observables for:
   - Level changes (material in/out)
   - Dwell time distribution
   - Overflow/underflow events
   - Capacity utilization patterns
   - Product mix in buffer

   Initialize buffer with configuration.

   :param env: SimPy environment
   :param config: Buffer configuration containing:
                  - capacity: Maximum buffer capacity (units)
                  - initial_level: Starting inventory level
                  - buffer_type: Type of buffer (FIFO, LIFO, priority)
                  - min_level: Minimum level for warnings
                  - max_dwell_time: Maximum allowed dwell time


   .. py:attribute:: capacity


   .. py:attribute:: initial_level


   .. py:attribute:: buffer_type


   .. py:attribute:: min_level


   .. py:attribute:: max_dwell_time


   .. py:attribute:: total_items_in
      :value: 0



   .. py:attribute:: total_items_out
      :value: 0



   .. py:attribute:: max_level_reached
      :value: 0



   .. py:attribute:: min_level_reached


   .. py:attribute:: overflow_count
      :value: 0



   .. py:attribute:: underflow_count
      :value: 0



   .. py:attribute:: dwell_times
      :type:  List[float]
      :value: []



   .. py:attribute:: level


   .. py:attribute:: last_level_change
      :value: 0.0



   .. py:attribute:: product_counts
      :type:  Dict[str, int]


   .. py:method:: start() -> None

      Start buffer monitoring processes.



   .. py:method:: put(quantity: int = 1, product_id: Optional[str] = None, **kwargs) -> Generator

      Put items into buffer.

      :param quantity: Number of items to add
      :param product_id: Product identifier
      :param \*\*kwargs: Additional item metadata

      :Yields: Store put event



   .. py:method:: get(quantity: int = 1) -> Any

      Get items from buffer.

      :param quantity: Number of items to retrieve

      :Yields: Store get event

      :returns: List of retrieved items



   .. py:method:: monitor_process() -> Generator

      Background process for buffer monitoring.



   .. py:method:: is_full() -> bool

      Check if buffer is at capacity.

      :returns: True if buffer is full



   .. py:method:: is_empty() -> bool

      Check if buffer is empty.

      :returns: True if buffer is empty



   .. py:method:: get_utilization() -> float

      Get current buffer utilization.

      :returns: Utilization percentage (0-100)



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get buffer statistics.

      :returns: Dictionary of buffer metrics



   .. py:method:: flush() -> List[BufferItem]

      Remove all items from buffer (e.g., for changeover).

      :returns: List of flushed items



