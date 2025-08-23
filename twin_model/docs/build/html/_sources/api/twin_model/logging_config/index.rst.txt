twin_model.logging_config
=========================

.. py:module:: twin_model.logging_config

.. autoapi-nested-parse::

   Centralized logging configuration for the twin_model framework.

   This module provides a unified logging setup that:
   - Uses Python's standard logging module with structured formatting
   - Supports different log levels for different scenarios
   - Includes file rotation and console output
   - Provides context-aware logging with correlation IDs
   - Optimizes performance in production mode



Attributes
----------

.. autoapisummary::

   twin_model.logging_config.logger


Classes
-------

.. autoapisummary::

   twin_model.logging_config.LogLevel
   twin_model.logging_config.StructuredFormatter
   twin_model.logging_config.SimulationLogger
   twin_model.logging_config.EventInspector


Functions
---------

.. autoapisummary::

   twin_model.logging_config.log_performance
   twin_model.logging_config.setup_default_logging


Module Contents
---------------

.. py:class:: LogLevel(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Logging levels for different scenarios.


   .. py:attribute:: DEBUG
      :value: 10



   .. py:attribute:: INFO
      :value: 20



   .. py:attribute:: WARNING
      :value: 30



   .. py:attribute:: ERROR
      :value: 40



   .. py:attribute:: CRITICAL
      :value: 50



.. py:class:: StructuredFormatter(json_format = False, include_context = True, include_timestamp = True)

   Bases: :py:obj:`logging.Formatter`


   Custom formatter that outputs structured log records.

   Features:
   - JSON output for production
   - Human-readable output for development
   - Includes context and performance data
   - Handles exceptions gracefully


   .. py:attribute:: json_format
      :value: False



   .. py:attribute:: include_context
      :value: True



   .. py:attribute:: include_timestamp
      :value: True



   .. py:method:: format(record)

      Format the log record.

      :param record: The log record to format

      :returns: Formatted log string



.. py:class:: SimulationLogger

   Centralized logger configuration for simulation framework.

   Features:
   - Hierarchical logger structure
   - File and console handlers
   - Structured logging with context
   - Performance monitoring
   - Event correlation


   .. py:method:: setup_logging(log_dir = Path('logs'), log_level = LogLevel.INFO, enable_console = True, enable_file = True, max_bytes = 10485760, backup_count = 5, correlation_id = None, json_format = False)
      :classmethod:


      Configure logging for the entire twin_model framework.

      :param log_dir: Directory for log files
      :param log_level: Minimum log level to capture
      :param enable_console: Enable console output
      :param enable_file: Enable file output
      :param max_bytes: Maximum size per log file
      :param backup_count: Number of backup files to keep
      :param correlation_id: Optional correlation ID for tracking
      :param json_format: Use JSON format for logs



   .. py:method:: get_logger(name)
      :classmethod:


      Get a logger instance with the given name.

      :param name: Logger name (usually __name__)

      :returns: Configured logger instance



   .. py:method:: log_with_context(logger, level, message, **context)
      :classmethod:


      Log a message with additional context.

      :param logger: Logger instance
      :param level: Log level
      :param message: Log message
      :param \*\*context: Additional context data



   .. py:method:: set_correlation_id(correlation_id)
      :classmethod:


      Set the correlation ID for all subsequent logs.



   .. py:method:: clear_correlation_id()
      :classmethod:


      Clear the correlation ID.



.. py:function:: log_performance(func)

   Decorator to log function performance.

   Usage:
       @log_performance
       def my_function():
           pass


.. py:class:: EventInspector(logger = None)

   Analyze and debug event streams.

   Provides utilities for inspecting and analyzing simulation events
   for debugging and optimization purposes.


   .. py:attribute:: logger


   .. py:method:: analyze_event_distribution(events, sample_size = None)

      Analyze distribution of event types.

      :param events: List of event dictionaries
      :param sample_size: Optional sample size limit

      :returns: Analysis results with statistics



   .. py:method:: find_anomalies(events)

      Find anomalous events in the stream.

      :param events: List of event dictionaries

      :returns: List of anomalous events



.. py:function:: setup_default_logging(level = 'INFO', enable_file = True, json_format = False)

   Quick setup with sensible defaults.

   :param level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param enable_file: Enable file logging
   :param json_format: Use JSON format for file logs


.. py:data:: logger

