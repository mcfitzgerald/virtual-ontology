twin_model.logging_config
=========================

Centralized logging configuration for the twin_model framework.

This module provides a unified logging setup that:
- Uses Python's standard logging module with structured formatting
- Supports different log levels for different scenarios
- Includes file rotation and console output
- Provides context-aware logging with correlation IDs
- Optimizes performance in production mode


Classes
-------

EventInspector
~~~~~~~~~~~~~~

Analyze and debug event streams.

Provides utilities for inspecting and analyzing simulation events
for debugging and optimization purposes.

Initialize event inspector.

:param logger: Logger instance to use


**Attributes:**

- **logger** (attribute): 

**Methods:**

.. method:: __init__(logger: Optional[logging.Logger] = None)

   Initialize event inspector.

   :param logger: Logger instance to use



.. method:: analyze_event_distribution(events: list[Dict[str, Any]], sample_size: Optional[int] = None)

   Analyze distribution of event types.

   :param events: List of event dictionaries
   :param sample_size: Optional sample size limit

   :returns: Analysis results with statistics



.. method:: find_anomalies(events: list[Dict[str, Any]])

   Find anomalous events in the stream.

   :param events: List of event dictionaries

   :returns: List of anomalous events




LogLevel
~~~~~~~~

Logging levels for different scenarios.


**Attributes:**

- **CRITICAL** (attribute): 
- **DEBUG** (attribute): 
- **ERROR** (attribute): 
- **INFO** (attribute): 
- **WARNING** (attribute): 

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




SimulationLogger
~~~~~~~~~~~~~~~~

Centralized logger configuration for simulation framework.

Features:
- Hierarchical logger structure
- File and console handlers
- Structured logging with context
- Performance monitoring
- Event correlation


**Attributes:**

- **_configured** (attribute): 
- **_correlation_id** (attribute): 
- **_log_dir** (attribute): 

**Methods:**

.. method:: clear_correlation_id()

   Clear the correlation ID.



.. method:: get_logger(name: str)

   Get a logger instance with the given name.

   :param name: Logger name (usually __name__)

   :returns: Configured logger instance



.. method:: log_with_context(logger: logging.Logger, level: int, message: str, **context)

   Log a message with additional context.

   :param logger: Logger instance
   :param level: Log level
   :param message: Log message
   :param \*\*context: Additional context data



.. method:: set_correlation_id(correlation_id: str)

   Set the correlation ID for all subsequent logs.



.. method:: setup_logging(log_dir: pathlib.Path = Path('logs'), log_level: Union[LogLevel, str] = LogLevel.INFO, enable_console: bool = True, enable_file: bool = True, max_bytes: int = 10485760, backup_count: int = 5, correlation_id: Optional[str] = None, json_format: bool = False)

   Configure logging for the entire twin_model framework.

   :param log_dir: Directory for log files
   :param log_level: Minimum log level to capture
   :param enable_console: Enable console output
   :param enable_file: Enable file output
   :param max_bytes: Maximum size per log file
   :param backup_count: Number of backup files to keep
   :param correlation_id: Optional correlation ID for tracking
   :param json_format: Use JSON format for logs




StructuredFormatter
~~~~~~~~~~~~~~~~~~~

Custom formatter that outputs structured log records.

Features:
- JSON output for production
- Human-readable output for development
- Includes context and performance data
- Handles exceptions gracefully

Initialize the structured formatter.

:param json_format: Output JSON if True, human-readable if False
:param include_context: Include context data in output
:param include_timestamp: Include timestamps in output


**Attributes:**

- **_fmt** (attribute): 
- **_style** (attribute): 
- **converter** (attribute): 
- **datefmt** (attribute): 
- **default_msec_format** (attribute): 
- **default_time_format** (attribute): 
- **include_context** (attribute): 
- **include_timestamp** (attribute): 
- **json_format** (attribute): 

**Methods:**

.. method:: __init__(json_format: bool = False, include_context: bool = True, include_timestamp: bool = True)

   Initialize the structured formatter.

   :param json_format: Output JSON if True, human-readable if False
   :param include_context: Include context data in output
   :param include_timestamp: Include timestamps in output



.. method:: format(record: logging.LogRecord)

   Format the log record.

   :param record: The log record to format

   :returns: Formatted log string



.. method:: formatException(ei)

   Format and return the specified exception information as a string.

   This default implementation just uses
   traceback.print_exception()



.. method:: formatMessage(record)



.. method:: formatStack(stack_info)

   This method is provided as an extension point for specialized
   formatting of stack information.

   The input data is a string as returned from a call to
   :func:`traceback.print_stack`, but with the last trailing newline
   removed.

   The base implementation just returns the value passed in.



.. method:: formatTime(record, datefmt=None)

   Return the creation time of the specified LogRecord as formatted text.

   This method should be called from format() by a formatter which
   wants to make use of a formatted time. This method can be overridden
   in formatters to provide for any specific requirement, but the
   basic behaviour is as follows: if datefmt (a string) is specified,
   it is used with time.strftime() to format the creation time of the
   record. Otherwise, an ISO8601-like (or RFC 3339-like) format is used.
   The resulting string is returned. This function uses a user-configurable
   function to convert the creation time to a tuple. By default,
   time.localtime() is used; to change this for a particular formatter
   instance, set the 'converter' attribute to a function with the same
   signature as time.localtime() or time.gmtime(). To change it for all
   formatters, for example if you want all logging times to be shown in GMT,
   set the 'converter' attribute in the Formatter class.



.. method:: usesTime()

   Check if the format uses the creation time of the record.





Functions
---------

.. function:: log_performance(func)

   Log function performance.

   Usage:
       @log_performance
       def my_function():
           pass



.. function:: setup_default_logging(level: str = 'INFO', enable_file: bool = True, json_format: bool = False)

   Quick setup with sensible defaults.

   :param level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param enable_file: Enable file logging
   :param json_format: Use JSON format for file logs




