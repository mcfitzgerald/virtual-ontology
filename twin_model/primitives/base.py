"""Base primitive class for SimPy-based building blocks.

This module defines the foundational primitive that all other primitives
extend. It provides core functionality for observable emission and
configuration management.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import simpy
from datetime import datetime


@dataclass
class PrimitiveConfig:
    """Configuration for a primitive instance.

    This dataclass holds all configuration values loaded from manifests,
    providing a clean separation between structure (ontology) and
    values (manifests).

    Attributes:
        id: Unique identifier for this primitive instance
        type: Type of primitive (Equipment, Buffer, Source, etc.)
        properties: Type-checked properties from manifest
        relationships: Dict of relationship type to related primitive IDs
        metadata: Additional context for debugging and analysis
    """

    id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value with optional default.

        Args:
            key: Property name to retrieve
            default: Value to return if property not found

        Returns:
            Property value or default
        """
        return self.properties.get(key, default)

    def validate(self) -> None:
        """Validate configuration against expected schema.

        Raises:
            ValueError: If required properties are missing or invalid
        """
        if not self.id:
            raise ValueError("Primitive ID is required")
        if not self.type:
            raise ValueError("Primitive type is required")


class BasePrimitive(ABC):
    """Base class for all SimPy primitives.

    All primitives must emit observables for discovery-based learning.
    This base class provides core functionality for:
    - Observable emission and storage
    - Configuration management
    - SimPy environment integration
    - Common event patterns

    The observable stream is the primary mechanism through which the
    LLM discovers relationships and patterns without prescriptive rules.
    """

    def __init__(self, env: simpy.Environment, config: PrimitiveConfig) -> None:
        """Initialize primitive with configuration.

        Args:
            env: SimPy environment for discrete event simulation
            config: Primitive configuration from manifest
        """
        self.env = env
        self.config = config
        self.config.validate()

        # Observable storage - this is what the LLM learns from
        self.observables: List[Dict[str, Any]] = []

        # Process handle for the main process if any
        self.process: Optional[simpy.Process] = None

        # Track primitive state for debugging
        self.is_initialized: bool = False
        self.is_running: bool = False

    @abstractmethod
    def start(self) -> None:
        """Start the primitive's processes.

        This method should be called after all primitives are created
        and wired together. It typically starts one or more SimPy
        processes that represent the primitive's behavior.
        """
        pass

    def emit_observable(
        self, event_type: str, details: Dict[str, Any], severity: str = "INFO"
    ) -> None:
        """Emit an observable event for learning.

        This is the primary mechanism for primitives to communicate
        their state and behavior. The richer the observables, the
        more patterns the LLM can discover.

        Args:
            event_type: Type of event (state_change, production, failure, etc.)
            details: Event-specific details with rich context
            severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        observable = {
            "timestamp": self.env.now,
            "datetime": datetime.fromtimestamp(
                self.env.now * 60
            ),  # Convert minutes to datetime
            "primitive_id": self.config.id,
            "primitive_type": self.config.type,
            "event_type": event_type,
            "severity": severity,
            **details,
        }
        self.observables.append(observable)

        # Also emit to global event bus if configured
        if hasattr(self.env, "global_observables"):
            self.env.global_observables.append(observable)

    def get_observables(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve observables with optional filtering.

        Args:
            event_type: Filter by specific event type
            start_time: Filter events after this simulation time
            end_time: Filter events before this simulation time

        Returns:
            Filtered list of observable events
        """
        result = self.observables

        if event_type:
            result = [o for o in result if o["event_type"] == event_type]

        if start_time is not None:
            result = [o for o in result if o["timestamp"] >= start_time]

        if end_time is not None:
            result = [o for o in result if o["timestamp"] <= end_time]

        return result

    def connect_to(
        self, other: "BasePrimitive", relationship_type: str = "feeds_into"
    ) -> None:
        """Connect this primitive to another via relationship.

        Args:
            other: Target primitive to connect to
            relationship_type: Type of relationship (feeds_into, controls, monitors)
        """
        if relationship_type not in self.config.relationships:
            self.config.relationships[relationship_type] = []

        if other.config.id not in self.config.relationships[relationship_type]:
            self.config.relationships[relationship_type].append(other.config.id)

        self.emit_observable(
            event_type="relationship_established",
            details={
                "relationship_type": relationship_type,
                "target_id": other.config.id,
                "target_type": other.config.type,
            },
        )

    def initialize(self) -> None:
        """Initialize primitive before starting processes.

        Override this method to perform setup that requires all
        primitives to be created first (e.g., wiring relationships).
        """
        self.is_initialized = True
        self.emit_observable(
            event_type="primitive_initialized",
            details={
                "properties": self.config.properties,
                "relationships": self.config.relationships,
            },
        )

    def shutdown(self) -> None:
        """Gracefully shutdown the primitive.

        Override this method to perform cleanup when simulation ends.
        """
        self.is_running = False
        self.emit_observable(
            event_type="primitive_shutdown", details={"final_state": self.get_state()}
        )

    def get_state(self) -> Dict[str, Any]:
        """Get current primitive state for debugging/analysis.

        Returns:
            Dictionary describing current primitive state
        """
        return {
            "id": self.config.id,
            "type": self.config.type,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "observable_count": len(self.observables),
            "relationships": self.config.relationships,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"{self.__class__.__name__}(id={self.config.id}, type={self.config.type})"
        )
