twin_model
==========

Ontology-driven virtual twin model.

This package provides an ontology-driven simulation framework for generating
synthetic MES (Manufacturing Execution System) data using SimPy discrete event
simulation with rich observables for pattern discovery.


Classes
-------

ArrivalPattern
~~~~~~~~~~~~~~

Material arrival patterns.

Initialize self.  See help(type(self)) for accurate signature.


**Attributes:**

- **BATCH** (attribute): 
- **CONSTANT** (attribute): 
- **EXPONENTIAL** (attribute): 
- **NORMAL** (attribute): 

**Methods:**

.. method:: __add__()

   Return self+value.



.. method:: __contains__()

   Return bool(key in self).



.. method:: __copy__()



.. method:: __deepcopy__(memo)



.. method:: __delattr__()

   Implement delattr(self, name).



.. method:: __dir__()

   Default dir() implementation.



.. method:: __eq__()

   Return self==value.



.. method:: __format__()

   Return a formatted version of the string as described by format_spec.



.. method:: __ge__()

   Return self>=value.



.. method:: __getattribute__()

   Return getattr(self, name).



.. method:: __getitem__()

   Return self[key].



.. method:: __getnewargs__()



.. method:: __getstate__()

   Helper for pickle.



.. method:: __gt__()

   Return self>value.



.. method:: __hash__()

   Return hash(self).



.. method:: __init__()

   Initialize self.  See help(type(self)) for accurate signature.



.. method:: __iter__()

   Implement iter(self).



.. method:: __le__()

   Return self<=value.



.. method:: __len__()

   Return len(self).



.. method:: __lt__()

   Return self<value.



.. method:: __mod__()

   Return self%value.



.. method:: __mul__()

   Return self*value.



.. method:: __ne__()

   Return self!=value.



.. method:: __new__()

   Create and return a new object.  See help(type) for accurate signature.



.. method:: __reduce__()

   Helper for pickle.



.. method:: __reduce_ex__()

   Helper for pickle.



.. method:: __repr__()

   Return repr(self).



.. method:: __rmod__()

   Return value%self.



.. method:: __rmul__()

   Return value*self.



.. method:: __setattr__()

   Implement setattr(self, name, value).



.. method:: __signature__()



.. method:: __sizeof__()

   Return the size of the string in memory, in bytes.



.. method:: __str__()

   Return str(self).



.. method:: __subclasshook__()

   Abstract classes can override this to customize issubclass().

   This is invoked early on by abc.ABCMeta.__subclasscheck__().
   It should return True, False or NotImplemented.  If it returns
   NotImplemented, the normal algorithm is used.  Otherwise, it
   overrides the normal algorithm (and the outcome is cached).



.. method:: _generate_next_value_(name, start, count, last_values)

   Generate the next value when not given.

   name: the name of the member
   start: the initial start value or None
   count: the number of existing members
   last_values: the list of values assigned



.. method:: _missing_(value)



.. method:: capitalize()

   Return a capitalized version of the string.

   More specifically, make the first character have upper case and the rest lower
   case.



.. method:: casefold()

   Return a version of the string suitable for caseless comparisons.



.. method:: center()

   Return a centered string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: count()

   S.count(sub[, start[, end]]) -> int

   Return the number of non-overlapping occurrences of substring sub in
   string S[start:end].  Optional arguments start and end are
   interpreted as in slice notation.



.. method:: encode()

   Encode the string using the codec registered for encoding.

   encoding
     The encoding in which to encode the string.
   errors
     The error handling scheme to use for encoding errors.
     The default is 'strict' meaning that encoding errors raise a
     UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
     'xmlcharrefreplace' as well as any other name registered with
     codecs.register_error that can handle UnicodeEncodeErrors.



.. method:: endswith()

   S.endswith(suffix[, start[, end]]) -> bool

   Return True if S ends with the specified suffix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   suffix can also be a tuple of strings to try.



.. method:: expandtabs()

   Return a copy where all tab characters are expanded using spaces.

   If tabsize is not given, a tab size of 8 characters is assumed.



.. method:: find()

   S.find(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: format()

   S.format(*args, **kwargs) -> str

   Return a formatted version of S, using substitutions from args and kwargs.
   The substitutions are identified by braces ('{' and '}').



.. method:: format_map()

   S.format_map(mapping) -> str

   Return a formatted version of S, using substitutions from mapping.
   The substitutions are identified by braces ('{' and '}').



.. method:: index()

   S.index(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: isalnum()

   Return True if the string is an alpha-numeric string, False otherwise.

   A string is alpha-numeric if all characters in the string are alpha-numeric and
   there is at least one character in the string.



.. method:: isalpha()

   Return True if the string is an alphabetic string, False otherwise.

   A string is alphabetic if all characters in the string are alphabetic and there
   is at least one character in the string.



.. method:: isascii()

   Return True if all characters in the string are ASCII, False otherwise.

   ASCII characters have code points in the range U+0000-U+007F.
   Empty string is ASCII too.



.. method:: isdecimal()

   Return True if the string is a decimal string, False otherwise.

   A string is a decimal string if all characters in the string are decimal and
   there is at least one character in the string.



.. method:: isdigit()

   Return True if the string is a digit string, False otherwise.

   A string is a digit string if all characters in the string are digits and there
   is at least one character in the string.



.. method:: isidentifier()

   Return True if the string is a valid Python identifier, False otherwise.

   Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
   such as "def" or "class".



.. method:: islower()

   Return True if the string is a lowercase string, False otherwise.

   A string is lowercase if all cased characters in the string are lowercase and
   there is at least one cased character in the string.



.. method:: isnumeric()

   Return True if the string is a numeric string, False otherwise.

   A string is numeric if all characters in the string are numeric and there is at
   least one character in the string.



.. method:: isprintable()

   Return True if all characters in the string are printable, False otherwise.

   A character is printable if repr() may use it in its output.



.. method:: isspace()

   Return True if the string is a whitespace string, False otherwise.

   A string is whitespace if all characters in the string are whitespace and there
   is at least one character in the string.



.. method:: istitle()

   Return True if the string is a title-cased string, False otherwise.

   In a title-cased string, upper- and title-case characters may only
   follow uncased characters and lowercase characters only cased ones.



.. method:: isupper()

   Return True if the string is an uppercase string, False otherwise.

   A string is uppercase if all cased characters in the string are uppercase and
   there is at least one cased character in the string.



.. method:: join()

   Concatenate any number of strings.

   The string whose method is called is inserted in between each given string.
   The result is returned as a new string.

   Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'



.. method:: ljust()

   Return a left-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: lower()

   Return a copy of the string converted to lowercase.



.. method:: lstrip()

   Return a copy of the string with leading whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: name()

   The name of the Enum member.



.. method:: partition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string.  If the separator is found,
   returns a 3-tuple containing the part before the separator, the separator
   itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing the original string
   and two empty strings.



.. method:: removeprefix()

   Return a str with the given prefix string removed if present.

   If the string starts with the prefix string, return string[len(prefix):].
   Otherwise, return a copy of the original string.



.. method:: removesuffix()

   Return a str with the given suffix string removed if present.

   If the string ends with the suffix string and that suffix is not empty,
   return string[:-len(suffix)]. Otherwise, return a copy of the original
   string.



.. method:: replace()

   Return a copy with all occurrences of substring old replaced by new.

     count
       Maximum number of occurrences to replace.
       -1 (the default value) means replace all occurrences.

   If the optional argument count is given, only the first count occurrences are
   replaced.



.. method:: rfind()

   S.rfind(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: rindex()

   S.rindex(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: rjust()

   Return a right-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: rpartition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string, starting at the end. If
   the separator is found, returns a 3-tuple containing the part before the
   separator, the separator itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing two empty strings
   and the original string.



.. method:: rsplit()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the end of the string and works to the front.



.. method:: rstrip()

   Return a copy of the string with trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: split()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the front of the string and works to the end.

   Note, str.split() is mainly useful for data that has been intentionally
   delimited.  With natural text that includes punctuation, consider using
   the regular expression module.



.. method:: splitlines()

   Return a list of the lines in the string, breaking at line boundaries.

   Line breaks are not included in the resulting list unless keepends is given and
   true.



.. method:: startswith()

   S.startswith(prefix[, start[, end]]) -> bool

   Return True if S starts with the specified prefix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   prefix can also be a tuple of strings to try.



.. method:: strip()

   Return a copy of the string with leading and trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: swapcase()

   Convert uppercase characters to lowercase and lowercase characters to uppercase.



.. method:: title()

   Return a version of the string where each word is titlecased.

   More specifically, words start with uppercased characters and all remaining
   cased characters have lower case.



.. method:: translate()

   Replace each character in the string using the given translation table.

     table
       Translation table, which must be a mapping of Unicode ordinals to
       Unicode ordinals, strings, or None.

   The table must implement lookup/indexing via __getitem__, for instance a
   dictionary or list.  If this operation raises LookupError, the character is
   left untouched.  Characters mapped to None are deleted.



.. method:: upper()

   Return a copy of the string converted to uppercase.



.. method:: value()

   The value of the Enum member.



.. method:: zfill()

   Pad a numeric string with zeros on the left, to fill a field of the given width.

   The string is never truncated.




BasePrimitive
~~~~~~~~~~~~~

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


**Attributes:**

- **__slots__** (attribute): 
- **config** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **process** (attribute): 
- **sampling_config** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: PrimitiveConfig, sampling_config: Optional[SamplingConfig] = None)

   Initialize primitive with configuration and performance optimization.

   :param env: SimPy environment for discrete event simulation
   :param config: Primitive configuration from manifest
   :param sampling_config: Optional sampling configuration for performance



.. method:: __repr__()

   Return string representation for debugging.



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the primitive's processes.

   This method should be called after all primitives are created
   and wired together. It typically starts one or more SimPy
   processes that represent the primitive's behavior.




CollectedProduct
~~~~~~~~~~~~~~~~

Represents a collected finished product.


**Attributes:**

- **collected_time** (attribute): 
- **order_id** (attribute): 
- **product_id** (attribute): 
- **quality** (attribute): 
- **source_equipment** (attribute): 


Equipment
~~~~~~~~~

Equipment with internal queues only - no external buffers.

Key features:
- Internal input and output queues (SimPy Stores)
- Direct equipment-to-equipment connections
- Realistic failure modeling
- Product-specific performance
- State-based operation

Initialize equipment with internal queues.

:param env: SimPy environment
:param config: Equipment configuration
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **base_rate** (attribute): 
- **config** (attribute): 
- **current_order** (attribute): 
- **current_product** (attribute): 
- **downstream_equipment** (attribute): 
- **env** (attribute): 
- **equipment_type** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **failure_count** (attribute): 
- **failure_process** (attribute): 
- **input_queue** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **line_id** (attribute): 
- **logger** (attribute): 
- **major_failure_count** (attribute): 
- **metric_aggregator** (attribute): 
- **micro_stop_count** (attribute): 
- **micro_stop_duration_mean** (attribute): 
- **micro_stop_duration_sigma** (attribute): 
- **micro_stop_probability** (attribute): 
- **minor_failure_count** (attribute): 
- **mtbf** (attribute): 
- **mttr** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **output_queue** (attribute): 
- **performance_factor** (attribute): 
- **position** (attribute): 
- **previous_state** (attribute): 
- **process** (attribute): 
- **sampling_config** (attribute): 
- **scrap_rate** (attribute): 
- **state** (attribute): 
- **state_durations** (attribute): 
- **state_start_time** (attribute): 
- **units_produced** (attribute): 
- **units_scrapped** (attribute): 
- **upstream_equipment** (attribute): 
- **warmup_complete** (attribute): 
- **warmup_period** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize equipment with internal queues.

   :param env: SimPy environment
   :param config: Equipment configuration
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _change_state(new_state: EquipmentState)

   Change equipment state and track duration.

   :param new_state: New equipment state



.. method:: _failure_process()

   Generate equipment failures based on realistic patterns.



.. method:: _get_next_failure()

   Determine next failure using competing risks model.

   Based on research findings:
   - 80% of stops are micro-stops (jams, sensor trips, adjustments)
   - 15% are minor failures (component issues, calibration)
   - 5% are major failures (equipment breakdown)

   :returns: Tuple of (failure_type, time_to_failure)



.. method:: _get_repair_duration(failure_type: FailureType)

   Get repair duration based on failure type and root causes.

   Based on research:
   - Micro-stops (80%): 0.5-3 minutes (jams, sensor trips)
   - Minor failures (15%): 5-30 minutes (component adjust, calibration)
   - Major failures (5%): 30+ minutes (breakdown, part replacement)

   :param failure_type: Type of failure

   :returns: Repair duration in minutes



.. method:: _handle_blocked()

   Handle blocked state (output queue full).



.. method:: _handle_interrupt(interrupt: simpy.Interrupt)

   Handle process interruption.

   :param interrupt: Interruption cause



.. method:: _handle_starved()

   Handle starved state (no input material).



.. method:: _is_blocked()

   Check if equipment is blocked by downstream.

   :returns: True if blocked, False otherwise



.. method:: _process_unit()

   Process a single unit of production.



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: twin_model.primitives.base.BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this equipment to downstream equipment.

   :param other: Next equipment in line
   :param relationship_type: Type of relationship (default: feeds_into)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_kpis()

   Calculate equipment KPIs.

   :returns: KPI dictionary



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_queue_status()

   Get current queue status.

   :returns: Queue status dictionary



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: run()

   Run main equipment process.



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the equipment processes.

   Implements the abstract start method from BasePrimitive.




EquipmentState
~~~~~~~~~~~~~~

Equipment operational states.

Initialize self.  See help(type(self)) for accurate signature.


**Attributes:**

- **BLOCKED** (attribute): 
- **CHANGEOVER** (attribute): 
- **IDLE** (attribute): 
- **RUNNING** (attribute): 
- **SHUTDOWN** (attribute): 
- **STARTUP** (attribute): 
- **STARVED** (attribute): 
- **STOPPED_FAILURE** (attribute): 
- **STOPPED_MAINTENANCE** (attribute): 

**Methods:**

.. method:: __add__()

   Return self+value.



.. method:: __contains__()

   Return bool(key in self).



.. method:: __copy__()



.. method:: __deepcopy__(memo)



.. method:: __delattr__()

   Implement delattr(self, name).



.. method:: __dir__()

   Default dir() implementation.



.. method:: __eq__()

   Return self==value.



.. method:: __format__()

   Return a formatted version of the string as described by format_spec.



.. method:: __ge__()

   Return self>=value.



.. method:: __getattribute__()

   Return getattr(self, name).



.. method:: __getitem__()

   Return self[key].



.. method:: __getnewargs__()



.. method:: __getstate__()

   Helper for pickle.



.. method:: __gt__()

   Return self>value.



.. method:: __hash__()

   Return hash(self).



.. method:: __init__()

   Initialize self.  See help(type(self)) for accurate signature.



.. method:: __iter__()

   Implement iter(self).



.. method:: __le__()

   Return self<=value.



.. method:: __len__()

   Return len(self).



.. method:: __lt__()

   Return self<value.



.. method:: __mod__()

   Return self%value.



.. method:: __mul__()

   Return self*value.



.. method:: __ne__()

   Return self!=value.



.. method:: __new__()

   Create and return a new object.  See help(type) for accurate signature.



.. method:: __reduce__()

   Helper for pickle.



.. method:: __reduce_ex__()

   Helper for pickle.



.. method:: __repr__()

   Return repr(self).



.. method:: __rmod__()

   Return value%self.



.. method:: __rmul__()

   Return value*self.



.. method:: __setattr__()

   Implement setattr(self, name, value).



.. method:: __signature__()



.. method:: __sizeof__()

   Return the size of the string in memory, in bytes.



.. method:: __str__()

   Return str(self).



.. method:: __subclasshook__()

   Abstract classes can override this to customize issubclass().

   This is invoked early on by abc.ABCMeta.__subclasscheck__().
   It should return True, False or NotImplemented.  If it returns
   NotImplemented, the normal algorithm is used.  Otherwise, it
   overrides the normal algorithm (and the outcome is cached).



.. method:: _generate_next_value_(name, start, count, last_values)

   Generate the next value when not given.

   name: the name of the member
   start: the initial start value or None
   count: the number of existing members
   last_values: the list of values assigned



.. method:: _missing_(value)



.. method:: capitalize()

   Return a capitalized version of the string.

   More specifically, make the first character have upper case and the rest lower
   case.



.. method:: casefold()

   Return a version of the string suitable for caseless comparisons.



.. method:: center()

   Return a centered string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: count()

   S.count(sub[, start[, end]]) -> int

   Return the number of non-overlapping occurrences of substring sub in
   string S[start:end].  Optional arguments start and end are
   interpreted as in slice notation.



.. method:: encode()

   Encode the string using the codec registered for encoding.

   encoding
     The encoding in which to encode the string.
   errors
     The error handling scheme to use for encoding errors.
     The default is 'strict' meaning that encoding errors raise a
     UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
     'xmlcharrefreplace' as well as any other name registered with
     codecs.register_error that can handle UnicodeEncodeErrors.



.. method:: endswith()

   S.endswith(suffix[, start[, end]]) -> bool

   Return True if S ends with the specified suffix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   suffix can also be a tuple of strings to try.



.. method:: expandtabs()

   Return a copy where all tab characters are expanded using spaces.

   If tabsize is not given, a tab size of 8 characters is assumed.



.. method:: find()

   S.find(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: format()

   S.format(*args, **kwargs) -> str

   Return a formatted version of S, using substitutions from args and kwargs.
   The substitutions are identified by braces ('{' and '}').



.. method:: format_map()

   S.format_map(mapping) -> str

   Return a formatted version of S, using substitutions from mapping.
   The substitutions are identified by braces ('{' and '}').



.. method:: index()

   S.index(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: isalnum()

   Return True if the string is an alpha-numeric string, False otherwise.

   A string is alpha-numeric if all characters in the string are alpha-numeric and
   there is at least one character in the string.



.. method:: isalpha()

   Return True if the string is an alphabetic string, False otherwise.

   A string is alphabetic if all characters in the string are alphabetic and there
   is at least one character in the string.



.. method:: isascii()

   Return True if all characters in the string are ASCII, False otherwise.

   ASCII characters have code points in the range U+0000-U+007F.
   Empty string is ASCII too.



.. method:: isdecimal()

   Return True if the string is a decimal string, False otherwise.

   A string is a decimal string if all characters in the string are decimal and
   there is at least one character in the string.



.. method:: isdigit()

   Return True if the string is a digit string, False otherwise.

   A string is a digit string if all characters in the string are digits and there
   is at least one character in the string.



.. method:: isidentifier()

   Return True if the string is a valid Python identifier, False otherwise.

   Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
   such as "def" or "class".



.. method:: islower()

   Return True if the string is a lowercase string, False otherwise.

   A string is lowercase if all cased characters in the string are lowercase and
   there is at least one cased character in the string.



.. method:: isnumeric()

   Return True if the string is a numeric string, False otherwise.

   A string is numeric if all characters in the string are numeric and there is at
   least one character in the string.



.. method:: isprintable()

   Return True if all characters in the string are printable, False otherwise.

   A character is printable if repr() may use it in its output.



.. method:: isspace()

   Return True if the string is a whitespace string, False otherwise.

   A string is whitespace if all characters in the string are whitespace and there
   is at least one character in the string.



.. method:: istitle()

   Return True if the string is a title-cased string, False otherwise.

   In a title-cased string, upper- and title-case characters may only
   follow uncased characters and lowercase characters only cased ones.



.. method:: isupper()

   Return True if the string is an uppercase string, False otherwise.

   A string is uppercase if all cased characters in the string are uppercase and
   there is at least one cased character in the string.



.. method:: join()

   Concatenate any number of strings.

   The string whose method is called is inserted in between each given string.
   The result is returned as a new string.

   Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'



.. method:: ljust()

   Return a left-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: lower()

   Return a copy of the string converted to lowercase.



.. method:: lstrip()

   Return a copy of the string with leading whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: name()

   The name of the Enum member.



.. method:: partition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string.  If the separator is found,
   returns a 3-tuple containing the part before the separator, the separator
   itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing the original string
   and two empty strings.



.. method:: removeprefix()

   Return a str with the given prefix string removed if present.

   If the string starts with the prefix string, return string[len(prefix):].
   Otherwise, return a copy of the original string.



.. method:: removesuffix()

   Return a str with the given suffix string removed if present.

   If the string ends with the suffix string and that suffix is not empty,
   return string[:-len(suffix)]. Otherwise, return a copy of the original
   string.



.. method:: replace()

   Return a copy with all occurrences of substring old replaced by new.

     count
       Maximum number of occurrences to replace.
       -1 (the default value) means replace all occurrences.

   If the optional argument count is given, only the first count occurrences are
   replaced.



.. method:: rfind()

   S.rfind(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: rindex()

   S.rindex(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: rjust()

   Return a right-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: rpartition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string, starting at the end. If
   the separator is found, returns a 3-tuple containing the part before the
   separator, the separator itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing two empty strings
   and the original string.



.. method:: rsplit()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the end of the string and works to the front.



.. method:: rstrip()

   Return a copy of the string with trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: split()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the front of the string and works to the end.

   Note, str.split() is mainly useful for data that has been intentionally
   delimited.  With natural text that includes punctuation, consider using
   the regular expression module.



.. method:: splitlines()

   Return a list of the lines in the string, breaking at line boundaries.

   Line breaks are not included in the resulting list unless keepends is given and
   true.



.. method:: startswith()

   S.startswith(prefix[, start[, end]]) -> bool

   Return True if S starts with the specified prefix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   prefix can also be a tuple of strings to try.



.. method:: strip()

   Return a copy of the string with leading and trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: swapcase()

   Convert uppercase characters to lowercase and lowercase characters to uppercase.



.. method:: title()

   Return a version of the string where each word is titlecased.

   More specifically, words start with uppercased characters and all remaining
   cased characters have lower case.



.. method:: translate()

   Replace each character in the string using the given translation table.

     table
       Translation table, which must be a mapping of Unicode ordinals to
       Unicode ordinals, strings, or None.

   The table must implement lookup/indexing via __getitem__, for instance a
   dictionary or list.  If this operation raises LookupError, the character is
   left untouched.  Characters mapped to None are deleted.



.. method:: upper()

   Return a copy of the string converted to uppercase.



.. method:: value()

   The value of the Enum member.



.. method:: zfill()

   Pad a numeric string with zeros on the left, to fill a field of the given width.

   The string is never truncated.




KPIMetric
~~~~~~~~~

A KPI metric with history.

.. attribute:: name

   KPI name

.. attribute:: type

   KPI type

.. attribute:: value

   Current value

.. attribute:: target

   Target value

.. attribute:: history

   Historical values

.. attribute:: unit

   Measurement unit

.. attribute:: aggregation

   How to aggregate (avg, sum, max, min)


**Attributes:**

- **aggregation** (attribute): 
- **history** (attribute): 
- **name** (attribute): 
- **target** (attribute): 
- **type** (attribute): 
- **unit** (attribute): 
- **value** (attribute): 

**Methods:**

.. method:: add_value(timestamp: float, value: float)

   Add a value to history.



.. method:: get_average(window: Optional[float] = None, current_time: Optional[float] = None)

   Get average value over time window.



.. method:: get_trend()

   Get trend direction.




KPIType
~~~~~~~

Types of KPIs tracked.

Initialize self.  See help(type(self)) for accurate signature.


**Attributes:**

- **AVAILABILITY** (attribute): 
- **CYCLE_TIME** (attribute): 
- **ENERGY_CONSUMPTION** (attribute): 
- **LEAD_TIME** (attribute): 
- **MTBF** (attribute): 
- **MTTR** (attribute): 
- **OEE** (attribute): 
- **PERFORMANCE** (attribute): 
- **QUALITY** (attribute): 
- **SCRAP_RATE** (attribute): 
- **THROUGHPUT** (attribute): 
- **UTILIZATION** (attribute): 

**Methods:**

.. method:: __add__()

   Return self+value.



.. method:: __contains__()

   Return bool(key in self).



.. method:: __copy__()



.. method:: __deepcopy__(memo)



.. method:: __delattr__()

   Implement delattr(self, name).



.. method:: __dir__()

   Default dir() implementation.



.. method:: __eq__()

   Return self==value.



.. method:: __format__()

   Return a formatted version of the string as described by format_spec.



.. method:: __ge__()

   Return self>=value.



.. method:: __getattribute__()

   Return getattr(self, name).



.. method:: __getitem__()

   Return self[key].



.. method:: __getnewargs__()



.. method:: __getstate__()

   Helper for pickle.



.. method:: __gt__()

   Return self>value.



.. method:: __hash__()

   Return hash(self).



.. method:: __init__()

   Initialize self.  See help(type(self)) for accurate signature.



.. method:: __iter__()

   Implement iter(self).



.. method:: __le__()

   Return self<=value.



.. method:: __len__()

   Return len(self).



.. method:: __lt__()

   Return self<value.



.. method:: __mod__()

   Return self%value.



.. method:: __mul__()

   Return self*value.



.. method:: __ne__()

   Return self!=value.



.. method:: __new__()

   Create and return a new object.  See help(type) for accurate signature.



.. method:: __reduce__()

   Helper for pickle.



.. method:: __reduce_ex__()

   Helper for pickle.



.. method:: __repr__()

   Return repr(self).



.. method:: __rmod__()

   Return value%self.



.. method:: __rmul__()

   Return value*self.



.. method:: __setattr__()

   Implement setattr(self, name, value).



.. method:: __signature__()



.. method:: __sizeof__()

   Return the size of the string in memory, in bytes.



.. method:: __str__()

   Return str(self).



.. method:: __subclasshook__()

   Abstract classes can override this to customize issubclass().

   This is invoked early on by abc.ABCMeta.__subclasscheck__().
   It should return True, False or NotImplemented.  If it returns
   NotImplemented, the normal algorithm is used.  Otherwise, it
   overrides the normal algorithm (and the outcome is cached).



.. method:: _generate_next_value_(name, start, count, last_values)

   Generate the next value when not given.

   name: the name of the member
   start: the initial start value or None
   count: the number of existing members
   last_values: the list of values assigned



.. method:: _missing_(value)



.. method:: capitalize()

   Return a capitalized version of the string.

   More specifically, make the first character have upper case and the rest lower
   case.



.. method:: casefold()

   Return a version of the string suitable for caseless comparisons.



.. method:: center()

   Return a centered string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: count()

   S.count(sub[, start[, end]]) -> int

   Return the number of non-overlapping occurrences of substring sub in
   string S[start:end].  Optional arguments start and end are
   interpreted as in slice notation.



.. method:: encode()

   Encode the string using the codec registered for encoding.

   encoding
     The encoding in which to encode the string.
   errors
     The error handling scheme to use for encoding errors.
     The default is 'strict' meaning that encoding errors raise a
     UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
     'xmlcharrefreplace' as well as any other name registered with
     codecs.register_error that can handle UnicodeEncodeErrors.



.. method:: endswith()

   S.endswith(suffix[, start[, end]]) -> bool

   Return True if S ends with the specified suffix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   suffix can also be a tuple of strings to try.



.. method:: expandtabs()

   Return a copy where all tab characters are expanded using spaces.

   If tabsize is not given, a tab size of 8 characters is assumed.



.. method:: find()

   S.find(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: format()

   S.format(*args, **kwargs) -> str

   Return a formatted version of S, using substitutions from args and kwargs.
   The substitutions are identified by braces ('{' and '}').



.. method:: format_map()

   S.format_map(mapping) -> str

   Return a formatted version of S, using substitutions from mapping.
   The substitutions are identified by braces ('{' and '}').



.. method:: index()

   S.index(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: isalnum()

   Return True if the string is an alpha-numeric string, False otherwise.

   A string is alpha-numeric if all characters in the string are alpha-numeric and
   there is at least one character in the string.



.. method:: isalpha()

   Return True if the string is an alphabetic string, False otherwise.

   A string is alphabetic if all characters in the string are alphabetic and there
   is at least one character in the string.



.. method:: isascii()

   Return True if all characters in the string are ASCII, False otherwise.

   ASCII characters have code points in the range U+0000-U+007F.
   Empty string is ASCII too.



.. method:: isdecimal()

   Return True if the string is a decimal string, False otherwise.

   A string is a decimal string if all characters in the string are decimal and
   there is at least one character in the string.



.. method:: isdigit()

   Return True if the string is a digit string, False otherwise.

   A string is a digit string if all characters in the string are digits and there
   is at least one character in the string.



.. method:: isidentifier()

   Return True if the string is a valid Python identifier, False otherwise.

   Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
   such as "def" or "class".



.. method:: islower()

   Return True if the string is a lowercase string, False otherwise.

   A string is lowercase if all cased characters in the string are lowercase and
   there is at least one cased character in the string.



.. method:: isnumeric()

   Return True if the string is a numeric string, False otherwise.

   A string is numeric if all characters in the string are numeric and there is at
   least one character in the string.



.. method:: isprintable()

   Return True if all characters in the string are printable, False otherwise.

   A character is printable if repr() may use it in its output.



.. method:: isspace()

   Return True if the string is a whitespace string, False otherwise.

   A string is whitespace if all characters in the string are whitespace and there
   is at least one character in the string.



.. method:: istitle()

   Return True if the string is a title-cased string, False otherwise.

   In a title-cased string, upper- and title-case characters may only
   follow uncased characters and lowercase characters only cased ones.



.. method:: isupper()

   Return True if the string is an uppercase string, False otherwise.

   A string is uppercase if all cased characters in the string are uppercase and
   there is at least one cased character in the string.



.. method:: join()

   Concatenate any number of strings.

   The string whose method is called is inserted in between each given string.
   The result is returned as a new string.

   Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'



.. method:: ljust()

   Return a left-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: lower()

   Return a copy of the string converted to lowercase.



.. method:: lstrip()

   Return a copy of the string with leading whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: name()

   The name of the Enum member.



.. method:: partition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string.  If the separator is found,
   returns a 3-tuple containing the part before the separator, the separator
   itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing the original string
   and two empty strings.



.. method:: removeprefix()

   Return a str with the given prefix string removed if present.

   If the string starts with the prefix string, return string[len(prefix):].
   Otherwise, return a copy of the original string.



.. method:: removesuffix()

   Return a str with the given suffix string removed if present.

   If the string ends with the suffix string and that suffix is not empty,
   return string[:-len(suffix)]. Otherwise, return a copy of the original
   string.



.. method:: replace()

   Return a copy with all occurrences of substring old replaced by new.

     count
       Maximum number of occurrences to replace.
       -1 (the default value) means replace all occurrences.

   If the optional argument count is given, only the first count occurrences are
   replaced.



.. method:: rfind()

   S.rfind(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: rindex()

   S.rindex(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: rjust()

   Return a right-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: rpartition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string, starting at the end. If
   the separator is found, returns a 3-tuple containing the part before the
   separator, the separator itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing two empty strings
   and the original string.



.. method:: rsplit()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the end of the string and works to the front.



.. method:: rstrip()

   Return a copy of the string with trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: split()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the front of the string and works to the end.

   Note, str.split() is mainly useful for data that has been intentionally
   delimited.  With natural text that includes punctuation, consider using
   the regular expression module.



.. method:: splitlines()

   Return a list of the lines in the string, breaking at line boundaries.

   Line breaks are not included in the resulting list unless keepends is given and
   true.



.. method:: startswith()

   S.startswith(prefix[, start[, end]]) -> bool

   Return True if S starts with the specified prefix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   prefix can also be a tuple of strings to try.



.. method:: strip()

   Return a copy of the string with leading and trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: swapcase()

   Convert uppercase characters to lowercase and lowercase characters to uppercase.



.. method:: title()

   Return a version of the string where each word is titlecased.

   More specifically, words start with uppercased characters and all remaining
   cased characters have lower case.



.. method:: translate()

   Replace each character in the string using the given translation table.

     table
       Translation table, which must be a mapping of Unicode ordinals to
       Unicode ordinals, strings, or None.

   The table must implement lookup/indexing via __getitem__, for instance a
   dictionary or list.  If this operation raises LookupError, the character is
   left untouched.  Characters mapped to None are deleted.



.. method:: upper()

   Return a copy of the string converted to uppercase.



.. method:: value()

   The value of the Enum member.



.. method:: zfill()

   Pad a numeric string with zeros on the left, to fill a field of the given width.

   The string is never truncated.




MESTransducer
~~~~~~~~~~~~~

Converts SimPy observables to MES data format.

The transducer extracts MES-visible events from the comprehensive
observable stream and formats them into the standard MES structure.

Initialize MES transducer.

:param time_bucket: Time bucket in minutes (default 5 for 5-minute intervals)


**Attributes:**

- **bucket_metrics** (attribute): 
- **equipment_states** (attribute): 
- **mes_records** (attribute): 
- **time_bucket** (attribute): 

**Methods:**

.. method:: __init__(time_bucket: int = 5)

   Initialize MES transducer.

   :param time_bucket: Time bucket in minutes (default 5 for 5-minute intervals)



.. method:: _calculate_availability(metrics: Dict[str, Any])

   Calculate availability score.

   :param metrics: Bucket metrics

   :returns: Availability percentage



.. method:: _calculate_performance(metrics: Dict[str, Any], equipment_info: Dict[str, Any], product_info: Dict[str, Any])

   Calculate performance score with safety checks.

   :param metrics: Bucket metrics
   :param equipment_info: Equipment manifest data
   :param product_info: Product manifest data

   :returns: Performance percentage



.. method:: _calculate_quality(metrics: Dict[str, Any])

   Calculate quality score.

   :param metrics: Bucket metrics

   :returns: Quality percentage



.. method:: _determine_equipment_type(equipment_id: str, equipment_info: Dict[str, Any])

   Determine equipment type from ID or manifest.

   :param equipment_id: Equipment identifier
   :param equipment_info: Equipment manifest data

   :returns: Equipment type string



.. method:: _extract_line_id(equipment_id: str, equipment_info: Dict[str, Any])

   Extract line ID from equipment ID or manifest.

   :param equipment_id: Equipment identifier
   :param equipment_info: Equipment manifest data

   :returns: Line ID



.. method:: _generate_mes_records(manifests: Optional[Dict[str, Any]] = None)

   Generate MES records from bucket metrics.

   :param manifests: Optional manifests for equipment details

   :returns: List of MES records



.. method:: _get_product_name(product_id: str, manifests: Optional[Dict[str, Any]] = None)

   Get product name from manifests.

   :param product_id: Product identifier
   :param manifests: Optional manifests

   :returns: Product name



.. method:: _map_state_to_mes(state: str)

   Map SimPy state to MES status.

   :param state: SimPy equipment state

   :returns: MES machine status



.. method:: _process_equipment_event(obs: Dict[str, Any], bucket_key: Tuple[int, str], manifests: Optional[Dict[str, Any]] = None)

   Process equipment-specific events.

   :param obs: Equipment observable
   :param bucket_key: Time bucket and equipment ID
   :param manifests: Optional manifests



.. method:: _process_observable(obs: Dict[str, Any], manifests: Optional[Dict[str, Any]] = None)

   Process single observable event.

   :param obs: Observable event
   :param manifests: Optional manifests for context



.. method:: _process_order_assignment(obs: Dict[str, Any], bucket_key: Tuple[int, str])

   Process order assignment events.

   :param obs: Order assignment observable
   :param bucket_key: Time bucket and equipment ID



.. method:: generate_summary_statistics(df: pandas.DataFrame)

   Generate summary statistics from MES data.

   :param df: MES DataFrame

   :returns: Dictionary of summary statistics



.. method:: process_observables(observables: List[Dict[str, Any]], manifests: Optional[Dict[str, Any]] = None)

   Process observables into MES format.

   :param observables: List of observable events from simulation
   :param manifests: Optional manifests for product/equipment details

   :returns: DataFrame in MES format



.. method:: save_to_csv(df: pandas.DataFrame, filepath: pathlib.Path)

   Save MES data to CSV file.

   :param df: MES DataFrame
   :param filepath: Output file path




Monitor
~~~~~~~

Monitor for tracking system-wide KPIs and metrics.

Emits observables for:
- KPI updates and trends
- Target violations
- Performance alerts
- Aggregated metrics
- Real-time dashboards

Initialize monitor with configuration.

:param env: SimPy environment
:param config: Monitor configuration containing:
               - kpi_definitions: KPIs to track
               - update_interval: How often to update KPIs (minutes)
               - aggregation_window: Time window for aggregations
               - alert_thresholds: Thresholds for alerts
               - monitored_primitives: List of primitives to monitor


**Attributes:**

- **__slots__** (attribute): 
- **active_alerts** (attribute): 
- **aggregation_window** (attribute): 
- **alert_history** (attribute): 
- **alert_thresholds** (attribute): 
- **config** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **kpis** (attribute): 
- **line_metrics** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **monitored_primitives** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **process** (attribute): 
- **product_metrics** (attribute): 
- **sampling_config** (attribute): 
- **shift_metrics** (attribute): 
- **update_interval** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

   Initialize monitor with configuration.

   :param env: SimPy environment
   :param config: Monitor configuration containing:
                  - kpi_definitions: KPIs to track
                  - update_interval: How often to update KPIs (minutes)
                  - aggregation_window: Time window for aggregations
                  - alert_thresholds: Thresholds for alerts
                  - monitored_primitives: List of primitives to monitor



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _aggregate_availability(primitives: List[Any])

   Calculate aggregated availability for a group of primitives.



.. method:: _aggregate_cycle_time(primitives: List[Any])

   Calculate average cycle time for a group of primitives.



.. method:: _aggregate_oee(primitives: List[Any])

   Calculate aggregated OEE for a group of primitives.



.. method:: _aggregate_quality(primitives: List[Any])

   Calculate aggregated quality for a group of primitives.



.. method:: _aggregate_throughput(primitives: List[Any])

   Calculate aggregated throughput for a group of primitives.



.. method:: _aggregate_volume(primitives: List[Any])

   Calculate total volume for a group of primitives.



.. method:: _calculate_availability(primitive: Any)

   Calculate availability for a primitive.

   :param primitive: Primitive to calculate for

   :returns: Availability percentage



.. method:: _check_thresholds()

   Check KPIs against configured thresholds.



.. method:: _create_alert(kpi_name: str, severity: str, message: str)

   Create an alert.

   :param kpi_name: KPI that triggered alert
   :param severity: Alert severity
   :param message: Alert message



.. method:: _get_current_shift()

   Determine current shift based on time.



.. method:: _get_production_in_window(primitive: Any)

   Get production count in recent window.

   :param primitive: Primitive to check

   :returns: Production count in window



.. method:: _group_by_line()

   Group monitored primitives by production line.



.. method:: _group_by_product()

   Group monitored primitives by current product.



.. method:: _init_kpis()

   Initialize KPI definitions from config.



.. method:: _update_aggregations()

   Update aggregated metrics by line, product, shift.



.. method:: _update_kpis()

   Update all KPI values from monitored primitives.



.. method:: alert_process()

   Process for managing alerts.



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_dashboard()

   Get dashboard summary of all metrics.

   :returns: Dictionary with dashboard data



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_kpi_history(kpi_name: str, window: Optional[float] = None)

   Get historical values of a KPI.

   :param kpi_name: Name of KPI
   :param window: Time window to retrieve

   :returns: List of (timestamp, value) tuples



.. method:: get_kpi_value(kpi_name: str)

   Get current value of a KPI.

   :param kpi_name: Name of KPI

   :returns: Current KPI value or None



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_statistics()

   Get monitor statistics.

   :returns: Dictionary of monitor metrics



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: monitor_process()

   Run monitoring process.



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: register_primitive(name: str, primitive: Any)

   Register a primitive to monitor.

   :param name: Primitive identifier
   :param primitive: Primitive instance



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the monitoring process.




OntologyDrivenModelBuilder
~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds SimPy models from ontology structure and manifests.

This builder:
1. Interprets the twin ontology to understand structure
2. Loads configuration from manifests
3. Creates primitives with internal queues only
4. Wires direct equipment connections
5. Integrates two-layer control system

Initialize model builder.

:param env: SimPy environment
:param ontology_path: Path to twin_ontology.yaml
:param manifest_dir: Directory containing manifest files
:param control_manager: Optional control manager for two-layer system
:param config_path: Optional path to twin_model.yaml config file


**Attributes:**

- **PRIMITIVE_CLASSES** (attribute): 
- **built** (attribute): 
- **classes** (attribute): 
- **config_path** (attribute): 
- **control_manager** (attribute): 
- **entities** (attribute): 
- **env** (attribute): 
- **lines** (attribute): 
- **manifest_dir** (attribute): 
- **manifests** (attribute): 
- **mappings** (attribute): 
- **ontology** (attribute): 
- **ontology_path** (attribute): 
- **primitives** (attribute): 
- **relationships** (attribute): 
- **system_config** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, ontology_path: pathlib.Path, manifest_dir: pathlib.Path, control_manager: Optional[twin_model.control.ControlManager] = None, config_path: Optional[pathlib.Path] = None)

   Initialize model builder.

   :param env: SimPy environment
   :param ontology_path: Path to twin_ontology.yaml
   :param manifest_dir: Directory containing manifest files
   :param control_manager: Optional control manager for two-layer system
   :param config_path: Optional path to twin_model.yaml config file



.. method:: _apply_control_parameters()

   Apply control system parameters to primitives.



.. method:: _create_monitors()

   Create monitors for KPI tracking.



.. method:: _create_primitives()

   Create SimPy primitives from entity definitions.



.. method:: _create_scheduler()

   Create scheduler with order management.



.. method:: _get_ontology_defaults(class_name: str)

   Get default property values from ontology class definition.

   :param class_name: Name of the class to get defaults for

   :returns: Dictionary of property defaults



.. method:: _load_entities()

   Load entity definitions from manifests.



.. method:: _load_manifests(manifest_dir: pathlib.Path)

   Load all manifest files from directory.



.. method:: _load_yaml(path: pathlib.Path)

   Load YAML file.



.. method:: _organize_lines()

   Organize entities into production lines.



.. method:: _parse_classes()

   Parse class definitions from TBox.



.. method:: _parse_mappings()

   Parse primitive mappings.



.. method:: _parse_relationships()

   Parse relationships from RBox.



.. method:: _wire_connections()

   Wire direct equipment-to-equipment connections using internal queues.

   This is the key architecture:
   - NO separate buffer entities
   - Direct equipment connections via internal queues
   - Source feeds first equipment's input queue
   - Sink collects from last equipment's output queue



.. method:: build_model()

   Build complete simulation model from ontology and manifests.

   :returns: Dictionary containing model components



.. method:: describe_model()

   Get human-readable description of the model.

   :returns: Description string



.. method:: get_line_status(line_id: str)

   Get current status of a production line.

   :param line_id: Line identifier

   :returns: Status dictionary



.. method:: start_processes()

   Start all simulation processes.




PrimitiveConfig
~~~~~~~~~~~~~~~

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


**Attributes:**

- **id** (attribute): 
- **metadata** (attribute): 
- **properties** (attribute): 
- **relationships** (attribute): 
- **type** (attribute): 

**Methods:**

.. method:: get_property(key: str, default: Any = None)

   Get a property value with optional default.

   :param key: Property name to retrieve
   :param default: Value to return if property not found

   :returns: Property value or default



.. method:: validate()

   Validate configuration against expected schema.

   :raises ValueError: If required properties are missing or invalid




Product
~~~~~~~

Product definition with changeover characteristics.


**Attributes:**

- **category** (attribute): 
- **complexity** (attribute): 
- **family** (attribute): 
- **margin** (attribute): 
- **max_batch_size** (attribute): 
- **min_batch_size** (attribute): 
- **product_id** (attribute): 
- **typical_batch_size** (attribute): 
- **volume_rank** (attribute): 


ProductCategory
~~~~~~~~~~~~~~~

ABC analysis categories.


**Attributes:**

- **A** (attribute): 
- **B** (attribute): 
- **C** (attribute): 

**Methods:**

.. method:: __copy__()



.. method:: __deepcopy__(memo)



.. method:: __dir__()

   Returns public methods and other interesting attributes.



.. method:: __format__(format_spec)



.. method:: __hash__()



.. method:: __init__(*args, **kwds)



.. method:: __new__(value)



.. method:: __reduce_ex__(proto)



.. method:: __repr__()



.. method:: __signature__()



.. method:: __str__()



.. method:: _generate_next_value_(name, start, count, last_values)

   Generate the next value when not given.

   name: the name of the member
   start: the initial start value or None
   count: the number of existing members
   last_values: the list of values assigned



.. method:: _missing_(value)



.. method:: name()

   The name of the Enum member.



.. method:: value()

   The value of the Enum member.




ProductionOrder
~~~~~~~~~~~~~~~

Enhanced production order with scheduling metadata.


**Attributes:**

- **actual_end** (attribute): 
- **actual_start** (attribute): 
- **completed_quantity** (attribute): 
- **due_date** (attribute): 
- **order_id** (attribute): 
- **priority** (attribute): 
- **product** (attribute): 
- **quantity** (attribute): 
- **release_date** (attribute): 
- **scheduled_start** (attribute): 
- **scrap_quantity** (attribute): 


ProductionUnit
~~~~~~~~~~~~~~

Represents a unit of production.


**Attributes:**

- **order_id** (attribute): 
- **product_id** (attribute): 
- **quality** (attribute): 
- **timestamp** (attribute): 


Scheduler
~~~~~~~~~

Enhanced scheduler with intelligent production sequencing.

Key features:
- Multiple sequencing strategies
- Changeover optimization
- Campaign production support
- Shift-aware scheduling
- ABC prioritization
- Control system integration

Initialize enhanced scheduler.

:param env: SimPy environment
:param config: Scheduler configuration
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **active_orders** (attribute): 
- **campaign_size** (attribute): 
- **changeover_count** (attribute): 
- **changeover_matrix** (attribute): 
- **completed_orders** (attribute): 
- **config** (attribute): 
- **current_product** (attribute): 
- **current_shift** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **last_changeover_time** (attribute): 
- **line_sources** (attribute): 
- **logger** (attribute): 
- **lookahead_horizon** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **order_queue** (attribute): 
- **orders_completed** (attribute): 
- **orders_scheduled** (attribute): 
- **pending_orders** (attribute): 
- **process** (attribute): 
- **products** (attribute): 
- **sampling_config** (attribute): 
- **schedule_adherence** (attribute): 
- **shift_start_time** (attribute): 
- **shifts_config** (attribute): 
- **strategy** (attribute): 
- **total_changeover_time** (attribute): 
- **total_tardiness** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize enhanced scheduler.

   :param env: SimPy environment
   :param config: Scheduler configuration
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _create_campaigns(orders: List[ProductionOrder])

   Create production campaigns by grouping same products.

   :param orders: Orders to group into campaigns

   :returns: Orders sequenced in campaigns



.. method:: _initialize_changeover_matrix()

   Initialize product changeover matrix with realistic times.

   Changeover times based on:
   - Product family (cleaning requirements)
   - Complexity difference (setup adjustments)
   - Allergen considerations (deep cleaning)

   :returns: ChangeoverMatrix with product-to-product times



.. method:: _initialize_products()

   Initialize product catalog from configuration.



.. method:: _optimize_changeovers(orders: List[ProductionOrder])

   Optimize order sequence to minimize changeover time.

   Uses a greedy nearest-neighbor approach for simplicity.

   :param orders: Orders to sequence

   :returns: Optimized order sequence



.. method:: _sequence_orders()

   Sequence orders based on current strategy.

   :returns: List of orders in execution sequence



.. method:: _update_shift()

   Update current shift based on simulation time.



.. method:: add_order(order: ProductionOrder)

   Add a production order to the schedule.

   :param order: Production order to add



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: complete_order(order: ProductionOrder, completed_quantity: int, scrap_quantity: int = 0)

   Mark an order as complete.

   :param order: Order that was completed
   :param completed_quantity: Good units produced
   :param scrap_quantity: Scrapped units



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_next_order()

   Get next order from schedule.

   :returns: Next production order or None



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_schedule_metrics()

   Calculate scheduling performance metrics.

   :returns: Dictionary of scheduling KPIs



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: register_source(line_id: str, source: twin_model.primitives.source.SourcePrimitive)

   Register a source for a production line.

   :param line_id: Production line ID (e.g., 'LINE1')
   :param source: Source primitive for the line



.. method:: request_changeover(from_product: str, to_product: str)

   Request changeover time for product switch.

   :param from_product: Current product
   :param to_product: Next product

   :returns: Required changeover time in minutes



.. method:: run()

   Run scheduler process.



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the scheduler process.

   Implements the abstract start method from BasePrimitive.




Sink
~~~~

Sink that collects from equipment output queues.

Key features:
- Direct connection to last equipment's output queue
- Order tracking and completion
- Throughput monitoring
- Quality tracking
- Collection rate limiting

Initialize sink primitive.

:param env: SimPy environment
:param config: Sink configuration
:param upstream: Equipment output queue or equipment with output_queue
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **active_orders** (attribute): 
- **collected_products** (attribute): 
- **collection_rate** (attribute): 
- **completed_orders** (attribute): 
- **config** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_collecting** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **line_id** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **order_tracking_enabled** (attribute): 
- **process** (attribute): 
- **quality_threshold** (attribute): 
- **recent_collections** (attribute): 
- **sampling_config** (attribute): 
- **target_throughput** (attribute): 
- **throughput_window** (attribute): 
- **total_collected** (attribute): 
- **total_rejected** (attribute): 
- **total_units_collected** (attribute): 
- **upstream** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, upstream: Optional[Union[simpy.Store, Any]] = None, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize sink primitive.

   :param env: SimPy environment
   :param config: Sink configuration
   :param upstream: Equipment output queue or equipment with output_queue
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _clean_throughput_window()

   Remove old timestamps from throughput tracking.



.. method:: _collect_product()

   Collect a single product from upstream.



.. method:: _update_order_tracking(order_id: str)

   Update order tracking for collected product.

   :param order_id: Order identifier



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_current_throughput()

   Calculate current throughput rate.

   :returns: Units per minute



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_order_status(order_id: Optional[str] = None)

   Get status of specific order or all orders.

   :param order_id: Optional specific order ID

   :returns: Order tracking information



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_products_by_order(order_id: str)

   Get all products collected for a specific order.

   :param order_id: Order identifier

   :returns: List of collected products



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_statistics()

   Get sink statistics.

   :returns: Statistics dictionary



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: register_order(order_id: str, target_quantity: int)

   Register a production order for tracking.

   :param order_id: Order identifier
   :param target_quantity: Expected quantity



.. method:: reset_statistics()

   Reset collection statistics.



.. method:: run()

   Run sink collection process.



.. method:: set_upstream(upstream: Union[simpy.Store, Any])

   Set upstream connection.

   :param upstream: Equipment output queue or equipment with output_queue



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the sink collection process.

   Implements the abstract start method from BasePrimitive.



.. method:: stop()

   Stop sink collection.




Source
~~~~~~

Source that feeds directly into equipment input queues.

Key features:
- Direct connection to first equipment's input queue
- Order-driven generation
- Multiple arrival patterns
- Quality inspection at source
- Supply disruption modeling

Initialize source primitive.

:param env: SimPy environment
:param config: Source configuration
:param downstream: Equipment input queue or equipment with input_queue
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **arrival_pattern** (attribute): 
- **arrival_rate** (attribute): 
- **batch_size** (attribute): 
- **changeover_count** (attribute): 
- **changeover_start_time** (attribute): 
- **config** (attribute): 
- **current_order** (attribute): 
- **disruption_probability** (attribute): 
- **downstream** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_changing_over** (attribute): 
- **is_disrupted** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **last_product** (attribute): 
- **line_id** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **order_mode** (attribute): 
- **order_queue** (attribute): 
- **process** (attribute): 
- **quality_rate** (attribute): 
- **sampling_config** (attribute): 
- **setup_units_produced** (attribute): 
- **setup_units_scrapped** (attribute): 
- **supply_variability** (attribute): 
- **total_changeover_time** (attribute): 
- **total_generated** (attribute): 
- **total_rejected** (attribute): 
- **units_generated** (attribute): 
- **units_remaining** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, downstream: Optional[Union[simpy.Store, Any]] = None, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize source primitive.

   :param env: SimPy environment
   :param config: Source configuration
   :param downstream: Equipment input queue or equipment with input_queue
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _complete_current_order()

   Complete the current production order.



.. method:: _continuous_generation()

   Generate material continuously.



.. method:: _execute_changeover()

   Execute product changeover process.

   :Yields: Changeover duration and setup production



.. method:: _generate_batch(size: int)

   Generate a batch of units.

   :param size: Batch size



.. method:: _generate_unit()

   Generate a single unit.

   Sets self.last_unit_generated to indicate success.



.. method:: _handle_disruption()

   Handle supply disruption.



.. method:: _order_driven_generation()

   Generate material based on production orders.



.. method:: add_order_to_queue(order: twin_model.primitives.scheduler.ProductionOrder)

   Add order to queue for processing.

   :param order: Production order to queue



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_statistics()

   Get source statistics.

   :returns: Statistics dictionary



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: initialize_wip(level: float = 0.5)

   Initialize work-in-progress in downstream equipment.

   :param level: Fill level as fraction of capacity (0-1)



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: run()

   Run source generation process.



.. method:: set_downstream(downstream: Union[simpy.Store, Any])

   Set downstream connection.

   :param downstream: Equipment input queue or equipment with input_queue



.. method:: set_production_order(order: twin_model.primitives.scheduler.ProductionOrder)

   Set current production order and check if changeover is needed.

   :param order: Production order to process



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the source generation process.

   Implements the abstract start method from BasePrimitive.



.. method:: stop()

   Stop source generation.






