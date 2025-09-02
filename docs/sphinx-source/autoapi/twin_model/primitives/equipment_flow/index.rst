twin_model.primitives.equipment_flow
====================================

.. py:module:: twin_model.primitives.equipment_flow

.. autoapi-nested-parse::

   Equipment flow primitive for continuous processing simulation.

   This module implements equipment with continuous flow processing using
   SimPy Containers, modeling realistic production constraints and failures.



Classes
-------

.. autoapisummary::

   twin_model.primitives.equipment_flow.ProcessingParameters
   twin_model.primitives.equipment_flow.FailureParameters
   twin_model.primitives.equipment_flow.EquipmentFlow


Module Contents
---------------

.. py:class:: ProcessingParameters

   Equipment processing parameters.


   .. py:attribute:: nominal_rate
      :type:  float


   .. py:attribute:: quality_rate
      :type:  float


   .. py:attribute:: performance_factor
      :type:  float


   .. py:attribute:: batch_size
      :type:  float


   .. py:attribute:: processing_interval
      :type:  float


.. py:class:: FailureParameters

   Equipment failure parameters.


   .. py:attribute:: mtbf
      :type:  float


   .. py:attribute:: mttr
      :type:  float


   .. py:attribute:: micro_stop_rate
      :type:  float


   .. py:attribute:: micro_stop_duration
      :type:  float


.. py:class:: EquipmentFlow(env: simpy.Environment, config: dict[str, Any], flow_capacity: twin_model.primitives.base_flow.FlowCapacity, processing: ProcessingParameters, failures: FailureParameters)

   Bases: :py:obj:`twin_model.primitives.base_flow.BaseFlowPrimitive`


   Equipment with continuous flow processing.


   .. py:attribute:: processing


   .. py:attribute:: failures


   .. py:attribute:: internal_buffer


   .. py:attribute:: is_failed
      :value: False



   .. py:attribute:: is_processing
      :value: False



   .. py:attribute:: current_product


   .. py:method:: process_flow() -> Generator[Any, None, None]

      Process material in continuous batches.



   .. py:method:: failure_process() -> Generator[Any, None, None]

      Simulate random failures.



   .. py:method:: micro_stop_process() -> Generator[Any, None, None]

      Simulate micro-stops.



   .. py:method:: changeover(new_product: str, changeover_time: float) -> Generator[Any, None, None]

      Perform product changeover.

      :param new_product: New product identifier
      :param changeover_time: Time required for changeover (minutes)



