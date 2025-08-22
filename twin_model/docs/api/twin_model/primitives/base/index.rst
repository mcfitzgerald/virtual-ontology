twin_model.primitives.base
==========================

.. py:module:: twin_model.primitives.base

.. autoapi-nested-parse::

   Base primitive class for SimPy-based building blocks.

   This module defines the foundational primitive that all other primitives
   extend. It provides core functionality for observable emission and
   configuration management.



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


   .. py:method:: get_property(key: str, default: Any = None) -> Any

      Get a property value with optional default.

      :param key: Property name to retrieve
      :param default: Value to return if property not found

      :returns: Property value or default



   .. py:method:: validate() -> None

      Validate configuration against expected schema.

      :raises ValueError: If required properties are missing or invalid



.. py:class:: SimulationMode

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Simulation data collection modes.

   Modes:
       DETAILED: Full observables, every event recorded
       PRODUCTION: Sampled data at configurable intervals
       FAST: Minimal logging, critical events and KPIs only

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: DETAILED
      :value: 'detailed'



   .. py:attribute:: PRODUCTION
      :value: 'production'



   .. py:attribute:: FAST
      :value: 'fast'



.. py:class:: SamplingConfig(mode: SimulationMode = SimulationMode.PRODUCTION, sampling_rate: int = 10, aggregation_interval: float = 5.0, buffer_size: int = 1000, enable_global_observables: bool = False)

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

   Initialize sampling configuration.

   :param mode: Data collection mode (DETAILED, PRODUCTION, or FAST)
   :param sampling_rate: Event sampling frequency (1 = every event, 10 = every 10th)
   :param aggregation_interval: Time window for metric aggregation in minutes
   :param buffer_size: Maximum events to keep in circular buffer
   :param enable_global_observables: Whether to duplicate events to global bus


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



   .. py:method:: should_record_event(event_type: str) -> bool

      Determine if an event should be recorded based on sampling config.

      :param event_type: Type of event being emitted

      :returns: True if event should be recorded, False otherwise



.. py:class:: ObservableBuffer(buffer_size: int = 1000, flush_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None)

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

   Initialize circular buffer with optional flush callback.

   :param buffer_size: Maximum events to keep (default 1000)
   :param flush_callback: Optional function to call when flushing data


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



   .. py:method:: append(event: Dict[str, Any]) -> None

      Add event to buffer, potentially discarding oldest.

      :param event: Event dictionary to add to buffer



   .. py:method:: flush() -> List[Dict[str, Any]]

      Flush buffer contents and optionally persist via callback.

      :returns: List of flushed events



   .. py:method:: get_recent(n: int) -> List[Dict[str, Any]]

      Get n most recent events without removing them.

      :param n: Number of recent events to retrieve

      :returns: List of n most recent events (or all if fewer than n)



   .. py:method:: get_stats() -> Dict[str, int]

      Get buffer statistics for monitoring.

      :returns: Dictionary with buffer statistics



.. py:class:: EventBatcher(batch_window: float = 5.0, batch_size: int = 100)

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

   Initialize event batcher with window and size parameters.

   :param batch_window: Time window for grouping events (default 5 minutes)
   :param batch_size: Maximum batch size before forcing flush (default 100)


   .. py:attribute:: batch_window
      :value: 5.0



   .. py:attribute:: batch_size
      :value: 100



   .. py:attribute:: pending_batches
      :type:  DefaultDict[Tuple[str, int], List[Dict[str, Any]]]


   .. py:attribute:: current_window
      :type:  int
      :value: 0



   .. py:method:: add_event(event: Dict[str, Any], timestamp: float) -> Optional[List[Dict[str, Any]]]

      Add event to batch, return batch if ready.

      Groups events by type and time window. Returns completed batches
      when either the window changes or batch size is exceeded.

      :param event: Event data to batch
      :param timestamp: Current simulation time

      :returns: Completed batch if ready, None otherwise



   .. py:method:: flush_all() -> List[List[Dict[str, Any]]]

      Force flush all pending batches.

      :returns: List of all flushed batches



   .. py:method:: get_stats() -> Dict[str, Any]

      Get batcher statistics.

      :returns: Dictionary with batching statistics



.. py:class:: IncrementalAggregator(window_size: float = 5.0)

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

   Initialize aggregator with window size.

   :param window_size: Time window for aggregation in minutes (default 5)


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



   .. py:method:: add_value(metric_name: str, value: float, timestamp: float) -> Optional[Dict[str, Any]]

      Add value to aggregator, return window summary if complete.

      :param metric_name: Name of the metric being tracked
      :param value: Numeric value to add
      :param timestamp: Current simulation time

      :returns: Completed window statistics if window finished, None otherwise



   .. py:method:: get_current_stats() -> Dict[str, Any]

      Get statistics for current incomplete window.

      :returns: Current window statistics



   .. py:method:: get_history(n: int = 10) -> List[Dict[str, Any]]

      Get last n completed windows.

      :param n: Number of windows to retrieve

      :returns: List of completed window summaries



.. py:class:: MetricAggregator

   Single metric aggregator using Welford's algorithm.

   Computes mean, variance, min, max incrementally without storing values.
   This provides O(1) memory usage and numerically stable calculations.

   Reference: Welford, B. P. (1962). "Note on a method for calculating
   corrected sums of squares and products". Technometrics. 4 (3): 419–420.

   Initialize empty aggregator.


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



   .. py:method:: add(value: float) -> None

      Add value using Welford's online algorithm.

      :param value: Numeric value to add to aggregation



   .. py:method:: get_stats() -> Dict[str, float]

      Get current aggregated statistics.

      :returns: Dictionary with count, mean, variance, stddev, min, max



   .. py:method:: merge(other: MetricAggregator) -> None

      Merge another aggregator into this one.

      Uses parallel algorithm for combining statistics.

      :param other: Another MetricAggregator to merge



.. py:class:: ProgressCallback

   Bases: :py:obj:`abc.ABC`


   Abstract base class for progress reporting.

   Implement this class to create custom progress reporters
   for long-running simulations. Callbacks are invoked periodically
   during simulation execution.


.. py:class:: ConsoleProgressReporter(report_interval: float = 5.0)

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

   Initialize console reporter.

   :param report_interval: Seconds between progress reports


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



.. py:class:: SimulationMonitor(env: simpy.Environment, memory_threshold_mb: float = 500.0, event_rate_threshold: float = 100.0, check_interval: float = 60.0)

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

   Initialize simulation monitor.

   :param env: SimPy environment to monitor
   :param memory_threshold_mb: Memory usage warning threshold
   :param event_rate_threshold: Minimum events/second threshold
   :param check_interval: Simulation minutes between checks


   .. py:attribute:: env


   .. py:attribute:: memory_threshold_mb
      :value: 500.0



   .. py:attribute:: event_rate_threshold
      :value: 100.0



   .. py:attribute:: check_interval
      :value: 60.0



   .. py:attribute:: metrics
      :type:  Dict[str, Any]


   .. py:method:: record_event() -> None

      Record that an event was processed.



   .. py:method:: get_metrics() -> Dict[str, Any]

      Get current monitoring metrics.

      :returns: Dictionary of performance metrics



.. py:class:: BasePrimitive(env: simpy.Environment, config: PrimitiveConfig, sampling_config: Optional[SamplingConfig] = None)

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

   Initialize primitive with configuration and performance optimization.

   :param env: SimPy environment for discrete event simulation
   :param config: Primitive configuration from manifest
   :param sampling_config: Optional sampling configuration for performance


   .. py:attribute:: env


   .. py:attribute:: config


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


   .. py:method:: start() -> None
      :abstractmethod:


      Start the primitive's processes.

      This method should be called after all primitives are created
      and wired together. It typically starts one or more SimPy
      processes that represent the primitive's behavior.



   .. py:method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO') -> None

      Emit an observable event with sampling and performance optimization.

      This is the primary mechanism for primitives to communicate
      their state and behavior. Events are now sampled based on
      configuration to prevent memory exhaustion in long simulations.

      :param event_type: Type of event (state_change, production, failure, etc.)
      :param details: Event-specific details with rich context
      :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)



   .. py:method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict[str, Any]]

      Retrieve observables with optional filtering from circular buffer.

      :param event_type: Filter by specific event type
      :param start_time: Filter events after this simulation time
      :param end_time: Filter events before this simulation time

      :returns: Filtered list of observable events



   .. py:method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into') -> None

      Connect this primitive to another via relationship.

      :param other: Target primitive to connect to
      :param relationship_type: Type of relationship (feeds_into, controls, monitors)



   .. py:method:: initialize() -> None

      Initialize primitive before starting processes.

      Override this method to perform setup that requires all
      primitives to be created first (e.g., wiring relationships).



   .. py:method:: shutdown() -> None

      Gracefully shutdown the primitive.

      Override this method to perform cleanup when simulation ends.



   .. py:method:: emit_metric(metric_name: str, value: float) -> Optional[Dict[str, Any]]

      Emit a metric value for aggregation.

      This method tracks numeric metrics over time windows using
      incremental statistics. Useful for KPIs like OEE, throughput, etc.

      :param metric_name: Name of the metric (e.g., "oee", "throughput")
      :param value: Numeric value to aggregate

      :returns: Completed window statistics if window finished, None otherwise



   .. py:method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO') -> Optional[List[Dict[str, Any]]]

      Emit observable through batcher for efficient processing.

      Events are grouped by type and time window to reduce processing
      overhead. Use this for high-frequency events that can be processed
      in batches.

      :param event_type: Type of event
      :param details: Event details
      :param severity: Event severity

      :returns: Completed batch if ready, None otherwise



   .. py:method:: process_batches() -> List[List[Dict[str, Any]]]

      Process any pending batches.

      Call this periodically to flush pending batches.

      :returns: List of completed batches



   .. py:method:: get_aggregated_metrics() -> Dict[str, Any]

      Get current aggregated metrics.

      :returns: Current window statistics and history



   .. py:method:: flush_observables() -> List[Dict[str, Any]]

      Flush observable buffer and return events.

      This method can be called periodically to persist events to external
      storage and free memory. Useful for long-running simulations.

      :returns: List of flushed events



   .. py:method:: get_performance_metrics() -> Dict[str, Any]

      Get detailed performance metrics for monitoring.

      :returns: Dictionary containing performance statistics



   .. py:method:: get_state() -> Dict[str, Any]

      Get current primitive state including performance metrics.

      :returns: Dictionary describing current primitive state and performance



