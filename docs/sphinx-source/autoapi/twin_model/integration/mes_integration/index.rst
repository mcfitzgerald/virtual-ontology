twin_model.integration.mes_integration
======================================

.. py:module:: twin_model.integration.mes_integration

.. autoapi-nested-parse::

   Integration module for MES simulation components.

   This module provides integration between the production scheduler,
   MES data collector, and simulation primitives.



Attributes
----------

.. autoapisummary::

   twin_model.integration.mes_integration.logger


Classes
-------

.. autoapisummary::

   twin_model.integration.mes_integration.MESSimulationCoordinator


Functions
---------

.. autoapisummary::

   twin_model.integration.mes_integration.setup_mes_simulation


Module Contents
---------------

.. py:data:: logger

.. py:class:: MESSimulationCoordinator(env: simpy.Environment, scheduler: twin_model.scheduling.production_scheduler.ProductionScheduler, collector: twin_model.transduction.mes_collector.MESDataCollector, primitives: Dict[str, twin_model.primitives.base_flow.BaseFlowPrimitive], lines: Dict[str, List[str]])

   Coordinates MES simulation components.

   This coordinator manages the interaction between:
   - Production scheduler (manages orders)
   - MES data collector (captures data)
   - Equipment primitives (execute production)


   .. py:attribute:: env


   .. py:attribute:: scheduler


   .. py:attribute:: collector


   .. py:attribute:: primitives


   .. py:attribute:: lines


   .. py:attribute:: line_sources
      :type:  Dict[str, twin_model.primitives.source_flow.SourceFlow]


   .. py:attribute:: process


   .. py:method:: coordinate()

      Main coordination process.



.. py:function:: setup_mes_simulation(env: simpy.Environment, model: Dict[str, Any], simulation_duration: float, random_seed: Optional[int] = None) -> Dict[str, Any]

   Set up complete MES simulation.

   :param env: SimPy environment
   :param model: Model dictionary from OntologyModelBuilder
   :param simulation_duration: Total simulation duration in minutes
   :param random_seed: Random seed for reproducibility

   :returns: Dictionary with scheduler, collector, and coordinator


