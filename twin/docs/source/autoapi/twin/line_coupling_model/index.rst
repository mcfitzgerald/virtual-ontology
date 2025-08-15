twin.line_coupling_model
========================

.. py:module:: twin.line_coupling_model

.. autoapi-nested-parse::

   Line Coupling Model
   Explicit cascade model with buffers and stochastic variation



Classes
-------

.. autoapisummary::

   twin.line_coupling_model.EquipmentStatus
   twin.line_coupling_model.Buffer
   twin.line_coupling_model.LineCoupling


Module Contents
---------------

.. py:class:: EquipmentStatus(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Equipment operational status


   .. py:attribute:: RUNNING
      :value: 'Running'



   .. py:attribute:: STOPPED
      :value: 'Stopped'



   .. py:attribute:: STARVED
      :value: 'Starved'



   .. py:attribute:: BLOCKED
      :value: 'Blocked'



.. py:class:: Buffer

   Material buffer between equipment


   .. py:attribute:: capacity
      :type:  int
      :value: 100



   .. py:attribute:: current_level
      :type:  int
      :value: 50



   .. py:attribute:: min_operating_level
      :type:  int
      :value: 10



   .. py:attribute:: max_operating_level
      :type:  int
      :value: 90



   .. py:method:: is_empty()

      Check if buffer is effectively empty



   .. py:method:: is_full()

      Check if buffer is effectively full



   .. py:method:: add(units)

      Add units to buffer
      Returns actual units added (may be less if buffer fills)



   .. py:method:: remove(units)

      Remove units from buffer
      Returns actual units removed (may be less if buffer empties)



.. py:class:: LineCoupling

   Explicit cascade model with buffers and stochastic variation
   Models how upstream stops affect downstream equipment


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: buffer_capacity


   .. py:attribute:: initial_buffer_level


   .. py:attribute:: depletion_rate


   .. py:attribute:: refill_rate


   .. py:attribute:: depletion_noise_std


   .. py:attribute:: refill_noise_std


   .. py:attribute:: use_probabilistic


   .. py:attribute:: cascade_sensitivity


   .. py:attribute:: cascade_delay_minutes


   .. py:attribute:: buffers
      :type:  Dict[str, Buffer]


   .. py:attribute:: equipment_status
      :type:  Dict[str, EquipmentStatus]


   .. py:attribute:: cascade_timers
      :type:  Dict[str, int]


   .. py:method:: initialize_line(equipment_ids)

      Initialize a production line with equipment and buffers

      :param equipment_ids: List of equipment IDs in order (upstream to downstream)



   .. py:method:: calculate_starvation(downstream_id, upstream_id, upstream_status, time_interval_minutes = None)

      Calculate if downstream equipment starves due to upstream stop

      :param downstream_id: ID of downstream equipment
      :param upstream_id: ID of upstream equipment
      :param upstream_status: Current status of upstream equipment
      :param time_interval_minutes: Time interval for calculation

      :returns: Tuple of (is_starved, probability_of_starvation)



   .. py:method:: calculate_blockage(upstream_id, downstream_id, downstream_status, time_interval_minutes = None)

      Calculate if upstream equipment blocks due to downstream stop

      :param upstream_id: ID of upstream equipment
      :param downstream_id: ID of downstream equipment
      :param downstream_status: Current status of downstream equipment
      :param time_interval_minutes: Time interval for calculation

      :returns: Tuple of (is_blocked, probability_of_blockage)



   .. py:method:: simulate_cascade(equipment_sequence, initial_failure, time_steps = None)

      Simulate cascade effects over time

      :param equipment_sequence: Ordered list of equipment IDs
      :param initial_failure: Equipment ID that initially fails
      :param time_steps: Number of 5-minute intervals to simulate

      :returns: Dictionary of equipment ID to list of statuses over time



   .. py:method:: get_buffer_status()

      Get current status of all buffers



