twin_model.primitives.base
==========================

.. py:module:: twin_model.primitives.base

.. autoapi-nested-parse::

   Base primitive class for SimPy-based building blocks.

   This module defines the foundational primitive that all other primitives
   extend. It provides core functionality for observable emission and
   configuration management.



Attributes
----------

.. autoapisummary::

   twin_model.primitives.base.logger


Classes
-------

.. autoapisummary::

   twin_model.primitives.base.PrimitiveConfig
   twin_model.primitives.base.SimulationMode
   twin_model.primitives.base.SamplingConfig
   twin_model.primitives.base.ObservableBuffer
   twin_model.primitives.base.EventBatcher
   twin_model.primitives.base.IncrementalAggregator
   twin_model.primitives.base.MetricAggregator
   twin_model.primitives.base.ProgressCallback
   twin_model.primitives.base.ConsoleProgressReporter
   twin_model.primitives.base.SimulationMonitor
   twin_model.primitives.base.BasePrimitive


Module Contents
---------------

.. py:data:: logger

.. py:class:: PrimitiveConfig

   Configuration for a primitive instance.

   This dataclass holds all configuration values loaded from manifests,
   providing a clean separation between structure (ontology) and
   values (manifests).

   .. attribute:: id

      Unique identifier for this primitive instance

   .. attribute:: type

      Type of primitive (Equipment, Buffer, Source, etc.)

   .. attribute:: properties

      Type-checked properties from manifest

   .. attribute:: relationships

      Dict of relationship type to related primitive IDs

   .. attribute:: metadata

      Additional context for debugging and analysis


   .. py:attribute:: id
      :type:  str


   .. py:attribute:: type
      :type:  str


   .. py:attribute:: properties
      :type:  Dict[str, Any]


   .. py:attribute:: relationships
      :type:  Dict[str, List[str]]


   .. py:attribute:: metadata
      :type:  Dict[str, Any]


   .. py:method:: get_property(key, default = None)

      Get a property value with optional default.

      :param key: Property name to retrieve
      :param default: Value to return if property not found

      :returns: Property value or default



   .. py:method:: validate()

      Validate configuration against expected schema.

      :raises ValueError: If required properties are missing or invalid



.. py:class:: SimulationMode

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Simulation data collection modes.

   Modes:
       DETAILED: Full observables, every event recorded
       PRODUCTION: Sampled data at configurable intervals
       FAST: Minimal logging, critical events and KPIs only


   .. py:attribute:: DETAILED
      :value: 'detailed'



   .. py:attribute:: PRODUCTION
      :value: 'production'



   .. py:attribute:: FAST
      :value: 'fast'



.. py:class:: SamplingConfig(mode = SimulationMode.PRODUCTION, sampling_rate = 10, aggregation_interval = 5.0, buffer_size = 1000, enable_global_observables = False)

   Configuration for observable sampling and performance optimization.

   This class controls how events are collected and stored during simulation,
   providing trade-offs between data completeness and performance.

   .. attribute:: mode

      Simulation mode controlling data collection strategy

   .. attribute:: sampling_rate

      Record every Nth event (1 = all events)

   .. attribute:: aggregation_interval

      Time window for aggregating metrics (minutes)

   .. attribute:: critical_events

      Event types that bypass sampling (always recorded)

   .. attribute:: buffer_size

      Maximum events to keep in memory per primitive

   .. attribute:: enable_global_observables

      Whether to emit to global event bus


   .. py:attribute:: mode


   .. py:attribute:: sampling_rate


   .. py:attribute:: aggregation_interval
      :value: 5.0



   .. py:attribute:: buffer_size
      :value: 1000



   .. py:attribute:: enable_global_observables
      :value: False



   .. py:attribute:: critical_events
      :type:  Set[str]


   .. py:attribute:: event_counter
      :type:  int
      :value: 0



   .. py:method:: should_record_event(event_type, is_critical = False)

      Determine if an event should be recorded based on sampling config.

      :param event_type: Type of event being emitted
      :param is_critical: Override flag to mark event as critical

      :returns: True if event should be recorded, False otherwise



.. py:class:: ObservableBuffer(buffer_size = 1000, flush_callback = None)

   Circular buffer for observables with automatic memory management.

   Uses collections.deque with maxlen for efficient circular buffer behavior.
   When the buffer is full, oldest events are automatically discarded.
   Optionally supports flushing to external storage via callback.

   .. attribute:: buffer

      Deque with maximum length for circular behavior

   .. attribute:: buffer_size

      Maximum number of events to keep in memory

   .. attribute:: flush_callback

      Optional callback for persisting data

   .. attribute:: total_events

      Counter of all events seen (including discarded)

   .. attribute:: discarded_events

      Counter of events dropped due to buffer overflow


   .. py:attribute:: buffer
      :type:  Deque[Dict[str, Any]]


   .. py:attribute:: buffer_size
      :value: 1000



   .. py:attribute:: flush_callback
      :value: None



   .. py:attribute:: total_events
      :type:  int
      :value: 0



   .. py:attribute:: discarded_events
      :type:  int
      :value: 0



   .. py:method:: append(event)

      Add event to buffer, potentially discarding oldest.

      :param event: Event dictionary to add to buffer



   .. py:method:: flush()

      Flush buffer contents and optionally persist via callback.

      :returns: List of flushed events



   .. py:method:: get_recent(n)

      Get n most recent events without removing them.

      :param n: Number of recent events to retrieve

      :returns: List of n most recent events (or all if fewer than n)



   .. py:method:: get_stats()

      Get buffer statistics for monitoring.

      :returns: Dictionary with buffer statistics



.. py:class:: EventBatcher(batch_window = 5.0, batch_size = 100)

   Batch similar events for efficient processing.

   Groups events by type and time window to reduce individual callbacks
   and improve performance. This reduces the overhead of processing
   each event individually, especially useful for high-frequency events.

   .. attribute:: batch_window

      Time window for batching (simulation minutes)

   .. attribute:: batch_size

      Maximum events per batch before forcing flush

   .. attribute:: pending_batches

      Dict of pending event batches by type and window

   .. attribute:: current_window

      Current time window being processed


   .. py:attribute:: batch_window
      :value: 5.0



   .. py:attribute:: batch_size
      :value: 100



   .. py:attribute:: pending_batches
      :type:  DefaultDict[Tuple[str, int], List[Dict[str, Any]]]


   .. py:attribute:: current_window
      :type:  int
      :value: 0



   .. py:method:: add_event(event, timestamp)

      Add event to batch, return batch if ready.

      Groups events by type and time window. Returns completed batches
      when either the window changes or batch size is exceeded.

      :param event: Event data to batch
      :param timestamp: Current simulation time

      :returns: Completed batch if ready, None otherwise



   .. py:method:: flush_all()

      Force flush all pending batches.

      :returns: List of all flushed batches



   .. py:method:: get_stats()

      Get batcher statistics.

      :returns: Dictionary with batching statistics



.. py:class:: IncrementalAggregator(window_size = 5.0)

   Incremental statistics aggregator for time-windowed metrics.

   Efficiently computes running statistics without storing all data points.
   Uses Welford's algorithm for numerically stable variance calculation.
   This allows for constant memory usage regardless of data size.

   .. attribute:: window_size

      Time window for aggregation (simulation minutes)

   .. attribute:: metrics

      Dict of metric aggregators by name

   .. attribute:: current_window_start

      Start time of current aggregation window


   .. py:attribute:: window_size
      :value: 5.0



   .. py:attribute:: metrics
      :type:  Dict[str, MetricAggregator]


   .. py:attribute:: current_window_start
      :type:  float
      :value: 0.0



   .. py:attribute:: completed_windows
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:method:: add_value(metric_name, value, timestamp)

      Add value to aggregator, return window summary if complete.

      :param metric_name: Name of the metric being tracked
      :param value: Numeric value to add
      :param timestamp: Current simulation time

      :returns: Completed window statistics if window finished, None otherwise



   .. py:method:: get_current_stats()

      Get statistics for current incomplete window.

      :returns: Current window statistics



   .. py:method:: get_history(n = 10)

      Get last n completed windows.

      :param n: Number of windows to retrieve

      :returns: List of completed window summaries



.. py:class:: MetricAggregator

   Single metric aggregator using Welford's algorithm.

   Computes mean, variance, min, max incrementally without storing values.
   This provides O(1) memory usage and numerically stable calculations.

   Reference: Welford, B. P. (1962). "Note on a method for calculating
   corrected sums of squares and products". Technometrics. 4 (3): 419–420.


   .. py:attribute:: count
      :type:  int
      :value: 0



   .. py:attribute:: mean
      :type:  float
      :value: 0.0



   .. py:attribute:: m2
      :type:  float
      :value: 0.0



   .. py:attribute:: min_value
      :type:  Optional[float]
      :value: None



   .. py:attribute:: max_value
      :type:  Optional[float]
      :value: None



   .. py:method:: add(value)

      Add value using Welford's online algorithm.

      :param value: Numeric value to add to aggregation



   .. py:method:: get_stats()

      Get current aggregated statistics.

      :returns: Dictionary with count, mean, variance, stddev, min, max



   .. py:method:: merge(other)

      Merge another aggregator into this one.

      Uses parallel algorithm for combining statistics.

      :param other: Another MetricAggregator to merge



.. py:class:: ProgressCallback

   Bases: :py:obj:`abc.ABC`


   Abstract base class for progress reporting.

   Implement this class to create custom progress reporters
   for long-running simulations. Callbacks are invoked periodically
   during simulation execution.


   .. py:method:: __call__(current_time, total_time, events_processed, memory_usage_mb, **kwargs)
      :abstractmethod:


      Report simulation progress.

      :param current_time: Current simulation time
      :param total_time: Total simulation duration
      :param events_processed: Number of events processed so far
      :param memory_usage_mb: Current memory usage in MB
      :param \*\*kwargs: Additional metrics (e.g., cache_size, db_inserts)



.. py:class:: ConsoleProgressReporter(report_interval = 5.0)

   Bases: :py:obj:`ProgressCallback`


   Console-based progress reporter with configurable intervals.

   Prints progress updates to console showing percentage complete,
   time remaining, memory usage, and event processing rate.

   .. attribute:: report_interval

      Seconds between progress reports

   .. attribute:: last_report_time

      Last time progress was reported

   .. attribute:: start_time

      Real-world start time of simulation


   .. py:attribute:: report_interval
      :value: 5.0



   .. py:attribute:: last_report_time
      :type:  float
      :value: 0



   .. py:attribute:: start_time
      :type:  float


   .. py:attribute:: last_events
      :type:  int
      :value: 0



   .. py:method:: __call__(current_time, total_time, events_processed, memory_usage_mb, **kwargs)

      Report progress to console.

      :param current_time: Current simulation time
      :param total_time: Total simulation duration
      :param events_processed: Number of events processed
      :param memory_usage_mb: Current memory usage
      :param \*\*kwargs: Additional metrics



.. py:class:: SimulationMonitor(env, memory_threshold_mb = None, event_rate_threshold = None, check_interval = None)

   Monitor simulation health and performance metrics.

   Tracks memory usage, event rates, and simulation performance
   to detect issues and provide diagnostics during execution.

   .. attribute:: env

      SimPy environment

   .. attribute:: memory_threshold_mb

      Memory warning threshold

   .. attribute:: event_rate_threshold

      Minimum acceptable event rate

   .. attribute:: check_interval

      Minutes between health checks

   .. attribute:: metrics

      Performance metrics dictionary


   .. py:attribute:: env


   .. py:attribute:: memory_threshold_mb


   .. py:attribute:: event_rate_threshold


   .. py:attribute:: check_interval


   .. py:attribute:: metrics
      :type:  Dict[str, Any]


   .. py:method:: record_event()

      Record that an event was processed.



   .. py:method:: get_metrics()

      Get current monitoring metrics.

      :returns: Dictionary of performance metrics



.. py:class:: BasePrimitive(env, config, sampling_config = None)

   Bases: :py:obj:`abc.ABC`


   Base class for all SimPy primitives.

   All primitives must emit observables for discovery-based learning.
   This base class provides core functionality for:
   - Observable emission and storage
   - Configuration management
   - SimPy environment integration
   - Common event patterns

   The observable stream is the primary mechanism through which the
   LLM discovers relationships and patterns without prescriptive rules.


   .. py:attribute:: env


   .. py:attribute:: config


   .. py:attribute:: logger


   .. py:attribute:: sampling_config


   .. py:attribute:: observable_buffer


   .. py:attribute:: observables


   .. py:attribute:: process
      :type:  Optional[simpy.Process]
      :value: None



   .. py:attribute:: is_initialized
      :type:  bool
      :value: False



   .. py:attribute:: is_running
      :type:  bool
      :value: False



   .. py:attribute:: events_emitted
      :type:  int
      :value: 0



   .. py:attribute:: events_sampled
      :type:  int
      :value: 0



   .. py:attribute:: event_batcher


   .. py:attribute:: metric_aggregator


   .. py:method:: start()
      :abstractmethod:


      Start the primitive's processes.

      This method should be called after all primitives are created
      and wired together. It typically starts one or more SimPy
      processes that represent the primitive's behavior.



   .. py:method:: emit_observable(event_type, details, severity = 'INFO', is_critical = False)

      Emit an observable event with sampling and performance optimization.

      This is the primary mechanism for primitives to communicate
      their state and behavior. Events are now sampled based on
      configuration to prevent memory exhaustion in long simulations.

      :param event_type: Type of event (state_change, production, failure, etc.)
      :param details: Event-specific details with rich context
      :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
      :param is_critical: Mark event as critical to bypass sampling



   .. py:method:: get_observables(event_type = None, start_time = None, end_time = None)

      Retrieve observables with optional filtering from circular buffer.

      :param event_type: Filter by specific event type
      :param start_time: Filter events after this simulation time
      :param end_time: Filter events before this simulation time

      :returns: Filtered list of observable events



   .. py:method:: connect_to(other, relationship_type = 'feeds_into')

      Connect this primitive to another via relationship.

      :param other: Target primitive to connect to
      :param relationship_type: Type of relationship (feeds_into, controls, monitors)



   .. py:method:: initialize()

      Initialize primitive before starting processes.

      Override this method to perform setup that requires all
      primitives to be created first (e.g., wiring relationships).



   .. py:method:: shutdown()

      Gracefully shutdown the primitive.

      Override this method to perform cleanup when simulation ends.



   .. py:method:: emit_metric(metric_name, value)

      Emit a metric value for aggregation.

      This method tracks numeric metrics over time windows using
      incremental statistics. Useful for KPIs like OEE, throughput, etc.

      :param metric_name: Name of the metric (e.g., "oee", "throughput")
      :param value: Numeric value to aggregate

      :returns: Completed window statistics if window finished, None otherwise



   .. py:method:: batch_emit_observable(event_type, details, severity = 'INFO')

      Emit observable through batcher for efficient processing.

      Events are grouped by type and time window to reduce processing
      overhead. Use this for high-frequency events that can be processed
      in batches.

      :param event_type: Type of event
      :param details: Event details
      :param severity: Event severity

      :returns: Completed batch if ready, None otherwise



   .. py:method:: process_batches()

      Process any pending batches.

      Call this periodically to flush pending batches.

      :returns: List of completed batches



   .. py:method:: get_aggregated_metrics()

      Get current aggregated metrics.

      :returns: Current window statistics and history



   .. py:method:: flush_observables()

      Flush observable buffer and return events.

      This method can be called periodically to persist events to external
      storage and free memory. Useful for long-running simulations.

      :returns: List of flushed events



   .. py:method:: get_performance_metrics()

      Get detailed performance metrics for monitoring.

      :returns: Dictionary containing performance statistics



   .. py:method:: get_state()

      Get current primitive state including performance metrics.

      :returns: Dictionary describing current primitive state and performance



   .. py:method:: __repr__()

      String representation for debugging.



