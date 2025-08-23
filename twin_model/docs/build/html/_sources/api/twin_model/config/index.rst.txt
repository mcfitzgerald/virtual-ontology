twin_model.config
=================

.. py:module:: twin_model.config

.. autoapi-nested-parse::

   Configuration system for performance optimization.

   This module provides configuration management for simulation performance
   settings, including presets for different scenarios and validation.



Classes
-------

.. autoapisummary::

   twin_model.config.ConfigPreset
   twin_model.config.PerformanceConfig


Module Contents
---------------

.. py:class:: ConfigPreset(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Pre-defined configuration presets for common scenarios.


   .. py:attribute:: DEVELOPMENT
      :value: 'development'



   .. py:attribute:: PRODUCTION
      :value: 'production'



   .. py:attribute:: FAST
      :value: 'fast'



   .. py:attribute:: MEMORY_OPTIMIZED
      :value: 'memory_optimized'



   .. py:attribute:: LONG_RUNNING
      :value: 'long_running'



   .. py:attribute:: REAL_TIME
      :value: 'real_time'



.. py:class:: PerformanceConfig

   Performance configuration for simulations.

   Controls memory usage, sampling, and optimization settings
   for different simulation scenarios. All settings can be
   customized or loaded from presets.

   .. attribute:: observable_buffer_size

      Max events per primitive buffer

   .. attribute:: sampling_rate

      Event sampling frequency (1 = keep all, 100 = keep 1%)

   .. attribute:: aggregation_interval

      Minutes between metric aggregations

   .. attribute:: flush_interval

      Minutes between database flushes

   .. attribute:: cache_max_size

      Max events per cache file

   .. attribute:: enable_global_observables

      Use global event collection

   .. attribute:: simulation_mode

      Data collection mode (DETAILED/PRODUCTION/FAST)

   .. attribute:: max_memory_mb

      Memory usage limit before warning

   .. attribute:: enable_progress

      Show progress updates during simulation

   .. attribute:: checkpoint_interval

      Minutes between auto-checkpoints

   .. attribute:: chunk_size_days

      Days per execution chunk

   .. attribute:: batch_size

      Events per batch for processing

   .. attribute:: enable_monitoring

      Enable health monitoring

   .. attribute:: monitoring_interval

      Minutes between health checks


   .. py:attribute:: observable_buffer_size
      :type:  int


   .. py:attribute:: cache_max_size
      :type:  int


   .. py:attribute:: max_memory_mb
      :type:  float


   .. py:attribute:: sampling_rate
      :type:  int


   .. py:attribute:: simulation_mode
      :type:  twin_model.primitives.base.SimulationMode


   .. py:attribute:: enable_global_observables
      :type:  bool
      :value: False



   .. py:attribute:: aggregation_interval
      :type:  float


   .. py:attribute:: flush_interval
      :type:  float


   .. py:attribute:: batch_size
      :type:  int


   .. py:attribute:: enable_progress
      :type:  bool
      :value: True



   .. py:attribute:: checkpoint_interval
      :type:  Optional[float]


   .. py:attribute:: chunk_size_days
      :type:  float


   .. py:attribute:: enable_monitoring
      :type:  bool
      :value: True



   .. py:attribute:: monitoring_interval
      :type:  float


   .. py:attribute:: name
      :type:  str
      :value: 'custom'



   .. py:attribute:: description
      :type:  str
      :value: ''



   .. py:method:: from_preset(preset)
      :classmethod:


      Create configuration from a preset.

      :param preset: Preset name or ConfigPreset enum

      :returns: PerformanceConfig instance with preset values



   .. py:method:: from_json(path)
      :classmethod:


      Load configuration from JSON file.

      :param path: Path to configuration file

      :returns: PerformanceConfig instance

      :raises ValueError: If configuration is invalid



   .. py:method:: from_yaml(path)
      :classmethod:


      Load configuration from YAML file.

      :param path: Path to configuration file

      :returns: PerformanceConfig instance



   .. py:method:: to_json(path)

      Save configuration to JSON file.

      :param path: Path to save configuration



   .. py:method:: to_yaml(path)

      Save configuration to YAML file.

      :param path: Path to save configuration



   .. py:method:: validate()

      Validate configuration settings.

      :returns: List of validation errors, empty if valid



   .. py:method:: estimate_memory_usage(num_primitives, simulation_days)

      Estimate memory usage for given simulation parameters.

      :param num_primitives: Number of primitives in simulation
      :param simulation_days: Duration of simulation in days

      :returns: Dictionary with memory estimates in MB



   .. py:method:: recommend_settings(num_primitives, simulation_days, available_memory_mb)

      Recommend configuration based on simulation parameters.

      :param num_primitives: Number of primitives
      :param simulation_days: Simulation duration
      :param available_memory_mb: Available memory budget

      :returns: Recommended PerformanceConfig



   .. py:method:: get_summary()

      Get human-readable configuration summary.

      :returns: Configuration summary string



