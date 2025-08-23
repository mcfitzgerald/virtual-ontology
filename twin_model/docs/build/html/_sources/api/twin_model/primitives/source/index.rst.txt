twin_model.primitives.source
============================

.. py:module:: twin_model.primitives.source

.. autoapi-nested-parse::

   Source primitive for material generation in manufacturing.

   This module provides a source primitive that generates materials/units
   entering the production system. It can model raw material arrival,
   customer orders, or other input streams with various arrival patterns.



Classes
-------

.. autoapisummary::

   twin_model.primitives.source.ArrivalPattern
   twin_model.primitives.source.SourcePrimitive


Module Contents
---------------

.. py:class:: ArrivalPattern

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types of arrival patterns for source generation.


   .. py:attribute:: CONSTANT
      :value: 'CONSTANT'



   .. py:attribute:: EXPONENTIAL
      :value: 'EXPONENTIAL'



   .. py:attribute:: NORMAL
      :value: 'NORMAL'



   .. py:attribute:: BATCH
      :value: 'BATCH'



   .. py:attribute:: SCHEDULE
      :value: 'SCHEDULE'



   .. py:attribute:: STOCHASTIC
      :value: 'STOCHASTIC'



.. py:class:: SourcePrimitive(env, config, downstream = None)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Generic source that generates materials.

   Emits observables for:
   - Material generation events
   - Arrival pattern variations
   - Batch characteristics
   - Supply disruptions
   - Schedule adherence


   .. py:attribute:: downstream
      :value: None



   .. py:attribute:: arrival_pattern


   .. py:attribute:: arrival_rate


   .. py:attribute:: batch_size


   .. py:attribute:: schedule


   .. py:attribute:: disruption_probability


   .. py:attribute:: product_mix


   .. py:attribute:: current_product
      :value: None



   .. py:attribute:: total_generated
      :value: 0



   .. py:attribute:: total_batches
      :value: 0



   .. py:attribute:: disruption_count
      :value: 0



   .. py:attribute:: blocked_count
      :value: 0



   .. py:attribute:: quality_rate


   .. py:attribute:: supply_variability


   .. py:method:: start()

      Start the source generation process.



   .. py:method:: generate()

      Main generation process for materials.



   .. py:method:: disruption_process()

      Background process for random supply disruptions.



   .. py:method:: set_arrival_rate(rate)

      Dynamically adjust arrival rate.

      :param rate: New arrival rate (units/minute)



   .. py:method:: set_product_mix(mix)

      Update product mix.

      :param mix: Dictionary of product IDs to weights



   .. py:method:: get_statistics()

      Get source statistics.

      :returns: Dictionary of source metrics



