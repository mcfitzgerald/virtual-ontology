"""
Centralized logging configuration for the twin_model framework.

This module provides a unified logging setup that:
- Uses Python's standard logging module with structured formatting
- Supports different log levels for different scenarios
- Includes file rotation and console output
- Provides context-aware logging with correlation IDs
- Optimizes performance in production mode
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime, timezone
import json
import traceback
from functools import wraps
import time


class LogLevel(Enum):
    """Logging levels for different scenarios."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured log records.
    
    Features:
    - JSON output for production
    - Human-readable output for development
    - Includes context and performance data
    - Handles exceptions gracefully
    """
    
    def __init__(
        self,
        json_format: bool = False,
        include_context: bool = True,
        include_timestamp: bool = True
    ):
        """
        Initialize the structured formatter.
        
        Args:
            json_format: Output JSON if True, human-readable if False
            include_context: Include context data in output
            include_timestamp: Include timestamps in output
        """
        super().__init__()
        self.json_format = json_format
        self.include_context = include_context
        self.include_timestamp = include_timestamp
        
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log string
        """
        # Base log data
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat() if self.include_timestamp else None,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add location information
        log_data['location'] = f"{record.filename}:{record.lineno}"
        log_data['function'] = record.funcName
        
        # Add context data if available
        if self.include_context and hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if self.json_format else None
            }
            
        # Add performance data if present
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
            
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Format output
        if self.json_format:
            return json.dumps(log_data, default=str)
        else:
            # Human-readable format
            parts = []
            if self.include_timestamp:
                parts.append(f"[{log_data.get('timestamp', '')}]")
            parts.append(f"[{log_data['level']}]")
            parts.append(f"[{log_data['logger']}]")
            parts.append(log_data['message'])
            
            # Add key context fields
            for key in ['primitive_id', 'event_type', 'state', 'duration_ms']:
                if key in log_data:
                    parts.append(f"{key}={log_data[key]}")
                    
            base_message = " ".join(parts)
            
            # Add exception on new line if present
            if record.exc_info:
                base_message += "\n" + "".join(traceback.format_exception(*record.exc_info))
                
            return base_message


class SimulationLogger:
    """
    Centralized logger configuration for simulation framework.
    
    Features:
    - Hierarchical logger structure
    - File and console handlers
    - Structured logging with context
    - Performance monitoring
    - Event correlation
    """
    
    _configured = False
    _correlation_id: Optional[str] = None
    _log_dir: Optional[Path] = None
    
    @classmethod
    def setup_logging(
        cls,
        log_dir: Path = Path("logs"),
        log_level: Union[LogLevel, str] = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        max_bytes: int = 10_485_760,  # 10MB
        backup_count: int = 5,
        correlation_id: Optional[str] = None,
        json_format: bool = False
    ) -> None:
        """
        Configure logging for the entire twin_model framework.
        
        Args:
            log_dir: Directory for log files
            log_level: Minimum log level to capture
            enable_console: Enable console output
            enable_file: Enable file output
            max_bytes: Maximum size per log file
            backup_count: Number of backup files to keep
            correlation_id: Optional correlation ID for tracking
            json_format: Use JSON format for logs
        """
        if cls._configured:
            logging.getLogger(__name__).warning("Logging already configured, skipping setup")
            return
            
        # Convert string log level if needed
        if isinstance(log_level, str):
            log_level = LogLevel[log_level.upper()]
            
        # Store configuration
        cls._correlation_id = correlation_id
        cls._log_dir = log_dir
        
        # Create log directory if needed
        if enable_file:
            log_dir.mkdir(parents=True, exist_ok=True)
            
        # Get root logger
        root_logger = logging.getLogger('twin_model')
        root_logger.setLevel(log_level.value)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        console_formatter = StructuredFormatter(
            json_format=False,
            include_context=True,
            include_timestamp=True
        )
        
        file_formatter = StructuredFormatter(
            json_format=json_format,
            include_context=True,
            include_timestamp=True
        )
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level.value)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
            
        # File handler with rotation
        if enable_file:
            log_file = log_dir / "twin_model.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(log_level.value)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            # Add a separate error log
            error_file = log_dir / "twin_model_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)
            
        cls._configured = True
        
        # Log configuration
        logger = logging.getLogger(__name__)
        logger.info(
            "Logging configured",
            extra={'extra_data': {
                'log_level': log_level.name,
                'log_dir': str(log_dir) if enable_file else None,
                'console': enable_console,
                'file': enable_file,
                'json_format': json_format,
                'correlation_id': correlation_id
            }}
        )
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with the given name.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Configured logger instance
        """
        if not cls._configured:
            cls.setup_logging()
            
        # Ensure it's under twin_model namespace
        if not name.startswith('twin_model'):
            name = f'twin_model.{name}'
            
        return logging.getLogger(name)
    
    @classmethod
    def log_with_context(
        cls,
        logger: logging.Logger,
        level: int,
        message: str,
        **context
    ) -> None:
        """
        Log a message with additional context.
        
        Args:
            logger: Logger instance
            level: Log level
            message: Log message
            **context: Additional context data
        """
        # Add correlation ID if set
        if cls._correlation_id:
            context['correlation_id'] = cls._correlation_id
            
        # Log with extra data
        logger.log(level, message, extra={'extra_data': context})
    
    @classmethod
    def set_correlation_id(cls, correlation_id: str) -> None:
        """Set the correlation ID for all subsequent logs."""
        cls._correlation_id = correlation_id
    
    @classmethod
    def clear_correlation_id(cls) -> None:
        """Clear the correlation ID."""
        cls._correlation_id = None


def log_performance(func):
    """
    Decorator to log function performance.
    
    Usage:
        @log_performance
        def my_function():
            pass
    """
    logger = logging.getLogger(func.__module__)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            logger.debug(
                f"Function {func.__name__} completed",
                extra={'extra_data': {
                    'function': func.__name__,
                    'duration_ms': elapsed_ms,
                    'status': 'success'
                }}
            )
            
            return result
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            logger.error(
                f"Function {func.__name__} failed",
                extra={'extra_data': {
                    'function': func.__name__,
                    'duration_ms': elapsed_ms,
                    'status': 'error',
                    'error': str(e)
                }},
                exc_info=True
            )
            raise
            
    return wrapper


class EventInspector:
    """
    Analyze and debug event streams.
    
    Provides utilities for inspecting and analyzing simulation events
    for debugging and optimization purposes.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize event inspector.
        
        Args:
            logger: Logger instance to use
        """
        self.logger = logger or SimulationLogger.get_logger(__name__)
        
    def analyze_event_distribution(
        self,
        events: list[Dict[str, Any]],
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze distribution of event types.
        
        Args:
            events: List of event dictionaries
            sample_size: Optional sample size limit
            
        Returns:
            Analysis results with statistics
        """
        from collections import Counter
        
        self.logger.info(f"Analyzing {len(events)} events")
        
        # Sample if requested
        if sample_size and len(events) > sample_size:
            import random
            events = random.sample(events, sample_size)
            self.logger.info(f"Sampled {sample_size} events for analysis")
        
        # Event type distribution
        event_types = Counter(e.get('event_type') for e in events)
        
        # State change analysis
        state_changes = [e for e in events if e.get('event_type') == 'state_change']
        state_transitions = Counter(
            (e.get('old_state'), e.get('new_state'))
            for e in state_changes
        )
        
        # Production analysis
        production_events = [
            e for e in events
            if e.get('event_type') in ['unit_produced', 'unit_scrapped']
        ]
        
        # Equipment analysis
        equipment_events = {}
        for event in events:
            eq_id = event.get('primitive_id', 'unknown')
            if eq_id not in equipment_events:
                equipment_events[eq_id] = []
            equipment_events[eq_id].append(event)
        
        analysis = {
            'total_events': len(events),
            'event_types': dict(event_types),
            'state_changes': len(state_changes),
            'state_transitions': dict(state_transitions),
            'production_events': len(production_events),
            'unique_equipment': len(equipment_events),
            'events_per_equipment': {
                eq_id: len(eq_events)
                for eq_id, eq_events in equipment_events.items()
            }
        }
        
        self.logger.info(
            "Event analysis complete",
            extra={'extra_data': analysis}
        )
        
        return analysis
    
    def find_anomalies(
        self,
        events: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Find anomalous events in the stream.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of anomalous events
        """
        anomalies = []
        
        # Check for events with missing critical fields
        for event in events:
            issues = []
            
            if not event.get('timestamp'):
                issues.append('missing_timestamp')
            if not event.get('event_type'):
                issues.append('missing_event_type')
            if not event.get('primitive_id'):
                issues.append('missing_primitive_id')
                
            # Check for production without runtime
            if event.get('event_type') == 'unit_produced':
                if event.get('runtime_minutes', 0) == 0:
                    issues.append('production_without_runtime')
                    
            if issues:
                anomalies.append({
                    'event': event,
                    'issues': issues
                })
                
        if anomalies:
            self.logger.warning(
                f"Found {len(anomalies)} anomalous events",
                extra={'extra_data': {
                    'anomaly_count': len(anomalies),
                    'sample': anomalies[:5]  # Log first 5 as sample
                }}
            )
            
        return anomalies


# Convenience function for quick setup
def setup_default_logging(
    level: str = "INFO",
    enable_file: bool = True,
    json_format: bool = False
) -> None:
    """
    Quick setup with sensible defaults.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file: Enable file logging
        json_format: Use JSON format for file logs
    """
    SimulationLogger.setup_logging(
        log_level=level,
        enable_console=True,
        enable_file=enable_file,
        json_format=json_format
    )


# Module-level logger for this file
logger = SimulationLogger.get_logger(__name__)