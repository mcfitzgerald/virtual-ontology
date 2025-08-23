database.integration_optimized
==============================

.. py:module:: database.integration_optimized

.. autoapi-nested-parse::

   Optimized database integration with performance configuration.

   This module provides enhanced database integration using the performance
   optimization features developed in Phases 1-5.



Classes
-------

.. autoapisummary::

   database.integration_optimized.OptimizedTwinDatabaseIntegration


Module Contents
---------------

.. py:class:: OptimizedTwinDatabaseIntegration(db_manager = None, perf_config = None)

   Enhanced database integration with performance optimizations.

   This class integrates all performance optimizations from Phases 1-5:
   - Configurable performance settings
   - Memory-efficient event handling
   - Batched database operations
   - Progress reporting
   - State persistence
   - Automatic mode switching on memory pressure

   .. attribute:: db_manager

      Database manager instance

   .. attribute:: perf_config

      Performance configuration

   .. attribute:: cache_dir

      Directory for event caching

   .. attribute:: checkpoint_dir

      Directory for state checkpoints

   .. attribute:: monitor

      Optional simulation monitor


   .. py:attribute:: db_manager


   .. py:attribute:: perf_config


   .. py:attribute:: cache_dir


   .. py:attribute:: checkpoint_dir


   .. py:attribute:: monitor
      :type:  Optional[twin_model.primitives.base.SimulationMonitor]
      :value: None



   .. py:method:: __del__()

      Cleanup temporary directories on deletion.



   .. py:method:: run_simulation_to_db(run_type = 'experiment', parameters = None, days = 1, parent_run_id = None, perf_config = None, show_progress = True)

      Run optimized simulation and store results in database.

      Uses all performance optimizations including:
      - Circular buffers for memory efficiency
      - Event sampling based on configuration
      - Batched database operations
      - Cache-based event storage
      - Progress reporting
      - Automatic checkpointing

      :param run_type: Type of simulation run
      :param parameters: Simulation parameters
      :param days: Duration in days
      :param parent_run_id: Optional parent run ID
      :param perf_config: Override performance configuration
      :param show_progress: Show progress updates

      :returns: Run ID of completed simulation

      :raises Exception: If simulation fails



   .. py:method:: run_performance_benchmark(days = 1, num_primitives = None)

      Run performance benchmark with different configurations.

      Tests multiple performance configurations and compares results.

      :param days: Simulation duration
      :param num_primitives: Number of primitives (uses default model if None)

      :returns: Dictionary with benchmark results



   .. py:method:: auto_optimize_configuration(days, target_memory_mb = 500.0)

      Automatically optimize configuration for simulation.

      Analyzes simulation requirements and recommends optimal configuration.

      :param days: Simulation duration
      :param target_memory_mb: Target memory budget

      :returns: Optimized PerformanceConfig



   .. py:method:: monitor_memory_pressure()

      Check if system is under memory pressure.

      :returns: True if memory usage exceeds threshold



   .. py:method:: adaptive_mode_switch()

      Adaptively switch modes based on memory pressure.



