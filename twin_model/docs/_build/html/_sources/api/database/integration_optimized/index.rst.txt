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

.. py:class:: OptimizedTwinDatabaseIntegration(db_manager: database.repositories.Optional[database.manager.TwinDatabaseManager] = None, perf_config: database.repositories.Optional[twin_model.config.PerformanceConfig] = None)

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

   Initialize optimized integration.

   :param db_manager: Database manager (creates default if None)
   :param perf_config: Performance configuration (uses PRODUCTION preset if None)


   .. py:attribute:: db_manager


   .. py:attribute:: perf_config


   .. py:attribute:: cache_dir


   .. py:attribute:: checkpoint_dir


   .. py:attribute:: monitor
      :type:  database.repositories.Optional[twin_model.primitives.base.SimulationMonitor]
      :value: None



   .. py:method:: run_simulation_to_db(run_type: str = 'experiment', parameters: database.repositories.Dict[str, database.repositories.Any] = None, days: float = 1, parent_run_id: database.repositories.Optional[str] = None, perf_config: database.repositories.Optional[twin_model.config.PerformanceConfig] = None, show_progress: bool = True) -> str

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



   .. py:method:: run_performance_benchmark(days: float = 1, num_primitives: database.repositories.Optional[int] = None) -> database.repositories.Dict[str, database.repositories.Any]

      Run performance benchmark with different configurations.

      Tests multiple performance configurations and compares results.

      :param days: Simulation duration
      :param num_primitives: Number of primitives (uses default model if None)

      :returns: Dictionary with benchmark results



   .. py:method:: auto_optimize_configuration(days: float, target_memory_mb: float = 500.0) -> twin_model.config.PerformanceConfig

      Automatically optimize configuration for simulation.

      Analyzes simulation requirements and recommends optimal configuration.

      :param days: Simulation duration
      :param target_memory_mb: Target memory budget

      :returns: Optimized PerformanceConfig



   .. py:method:: monitor_memory_pressure() -> bool

      Check if system is under memory pressure.

      :returns: True if memory usage exceeds threshold



   .. py:method:: adaptive_mode_switch() -> None

      Adaptively switch modes based on memory pressure.



