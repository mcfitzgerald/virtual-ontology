"""Equipment primitive for processing materials in manufacturing.

This module provides a generic equipment primitive that can represent
any type of processing equipment (Filler, Packer, Palletizer, etc.).
It emits rich observables for pattern discovery including state transitions,
production events, failures, and performance variations.
"""

from typing import Optional, Generator, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import random
import simpy
import logging

from .base import BasePrimitive, PrimitiveConfig, SamplingConfig

# Import centralized logging
try:
    from twin_model.logging_config import SimulationLogger

    logger = SimulationLogger.get_logger(__name__)
except ImportError:
    # Fallback to standard logging if logging_config not available
    logger = logging.getLogger(__name__)


class EquipmentState(str, Enum):
    """Possible equipment states with detailed categorization."""

    RUNNING = "RUNNING"
    STOPPED_FAILURE = "STOPPED_FAILURE"
    STOPPED_MAINTENANCE = "STOPPED_MAINTENANCE"
    STARVED = "STARVED"
    BLOCKED = "BLOCKED"
    IDLE = "IDLE"
    CHANGEOVER = "CHANGEOVER"
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class FailureMode:
    """Definition of a failure mode for equipment.

    Attributes:
        name: Failure mode identifier (micro_stop, major_failure, etc.)
        probability_per_5min: Probability of occurrence per time interval
        duration_range: Min and max duration in minutes
        downtime_code: Associated downtime reason code
        cascade_probability: Probability of causing downstream failures
        recovery_time_factor: Multiplier for recovery time based on context
    """

    name: str
    probability_per_5min: float
    duration_range: Tuple[float, float]
    downtime_code: str
    cascade_probability: float = 0.0
    recovery_time_factor: float = 1.0


class EquipmentPrimitive(BasePrimitive):
    """Generic equipment that processes materials.

    Emits rich observables for pattern discovery including:
    - State transitions with context (buffer levels, runtime, product)
    - Production events with quality metrics
    - Failure events with contributing factors
    - Performance variations by shift/product
    - Energy consumption patterns
    - Cascade failure propagation
    """

    def __init__(
        self,
        env: simpy.Environment,
        config: PrimitiveConfig,
        upstream: Optional[Any] = None,  # Will be BufferPrimitive
        downstream: Optional[Any] = None,
        sampling_config: Optional[SamplingConfig] = None,
    ) -> None:  # Will be BufferPrimitive
        """Initialize equipment with buffers and performance optimization.

        Args:
            env: SimPy environment
            config: Equipment configuration containing:
                - base_rate: Units per minute nominal capacity
                - mtbf: Mean time between failures in minutes
                - mttr: Mean time to repair in minutes
                - energy_consumption_rate: kWh per minute when running
            upstream: Input buffer (None for source equipment)
            downstream: Output buffer (None for sink equipment)
            sampling_config: Optional sampling configuration for performance
        """
        super().__init__(env, config, sampling_config)

        # Buffer connections
        self.upstream = upstream
        self.downstream = downstream

        # Equipment parameters from config
        self.base_rate = config.get_property("base_rate", 60.0)
        self.mtbf = config.get_property("mtbf", 480.0)
        self.mttr = config.get_property("mttr", 30.0)
        self.energy_rate = config.get_property("energy_consumption_rate", 5.0)

        # State tracking
        self.state = EquipmentState.IDLE
        self.previous_state = EquipmentState.IDLE
        self.state_start_time = 0.0
        self.total_runtime = 0.0
        self.cycles_since_maintenance = 0

        # Production tracking
        self.units_produced = 0
        self.units_scrapped = 0
        # Default to first configured product if available
        self.current_product = self.config.get_property("default_product", "SKU-1001")
        self.current_order = self.config.get_property("default_order", "ORD-DEFAULT")
        self.current_shift: Optional[str] = None

        # Performance factors
        self.performance_factor = 1.0
        self.quality_factor = 1.0

        # Failure modes from config or defaults
        self.failure_modes = self._init_failure_modes()

        # Energy tracking
        self.energy_consumed = 0.0

        # Rich context for observables
        self.context_history: List[Dict[str, Any]] = []

    def _init_failure_modes(self) -> List[FailureMode]:
        """Initialize failure modes from config or use defaults.

        Returns:
            List of configured failure modes
        """
        modes = []

        # Check for configured failure patterns
        failure_config = self.config.get_property("failure_patterns", {})

        if failure_config:
            for mode_name, mode_data in failure_config.items():
                modes.append(
                    FailureMode(
                        name=mode_name,
                        probability_per_5min=mode_data.get("probability_per_5min", 0.05),
                        duration_range=tuple(mode_data.get("duration_range", [5, 15])),
                        downtime_code=mode_data.get("downtime_reason", "UNP-UNKNOWN"),
                        cascade_probability=mode_data.get("cascade_probability", 0.0),
                        recovery_time_factor=mode_data.get("recovery_factor", 1.0),
                    )
                )
        else:
            # Default failure modes
            modes = [
                FailureMode(
                    name="micro_stop",
                    probability_per_5min=0.08,
                    duration_range=(1, 3),
                    downtime_code="UNP-SENS",
                    cascade_probability=0.1,
                ),
                FailureMode(
                    name="major_failure",
                    probability_per_5min=0.02,
                    duration_range=(15, 45),
                    downtime_code="UNP-MECH",
                    cascade_probability=0.3,
                ),
                FailureMode(
                    name="quality_issue",
                    probability_per_5min=0.05,
                    duration_range=(2, 5),
                    downtime_code="UNP-QC",
                    cascade_probability=0.05,
                ),
            ]

        return modes

    def start(self) -> None:
        """Start the equipment process and failure process."""
        self.is_running = True
        self.process = self.env.process(self.run())
        self.env.process(self.failure_process())
        self.env.process(self.monitor_process())

        self.emit_observable(
            event_type="equipment_started",
            details={
                "base_rate": self.base_rate,
                "mtbf": self.mtbf,
                "mttr": self.mttr,
                "failure_modes": [m.name for m in self.failure_modes],
            },
        )

    def run(self) -> Generator:
        """Main equipment process for production."""
        while self.is_running:
            try:
                # Check for material availability
                if self.upstream and hasattr(self.upstream, "level") and self.upstream.level == 0:
                    yield from self._handle_starved()
                    continue

                # Check for downstream capacity
                if self.downstream and hasattr(self.downstream, "is_full") and self.downstream.is_full():
                    yield from self._handle_blocked()
                    continue

                # Process one unit
                yield from self._process_unit()

            except simpy.Interrupt as interrupt:
                # Handle interruptions (failures, maintenance, changeover)
                yield from self._handle_interrupt(interrupt)

    def _process_unit(self) -> Generator:
        """Process a single unit of material.

        Yields:
            Timeout for processing duration
        """
        self._change_state(EquipmentState.RUNNING)

        # Calculate actual processing time with performance variations
        cycle_time = self._calculate_cycle_time()

        # Get material from upstream if available
        if self.upstream and hasattr(self.upstream, "get"):
            yield from self.upstream.get(1)

        # Processing time
        yield self.env.timeout(cycle_time)

        # Quality check
        if self._quality_check():
            # Good unit - send downstream
            if self.downstream and hasattr(self.downstream, "put"):
                yield from self.downstream.put(1)
            self.units_produced += 1

            # Log production event
            logger.debug(
                f"Unit produced by {self.config.id}",
                extra={
                    "extra_data": {
                        "equipment_id": self.config.id,
                        "product_id": self.current_product,
                        "cycle_time": cycle_time,
                        "units_produced": self.units_produced,
                        "timestamp": self.env.now,
                    }
                },
            )

            self.emit_observable(
                event_type="unit_produced",
                details={
                    "product_id": self.current_product,
                    "order_id": self.current_order,
                    "cycle_time": cycle_time,
                    "quality": "good",
                    "shift": self.current_shift,
                    "performance_factor": self.performance_factor,
                    "upstream_level": self.upstream.level
                    if self.upstream and hasattr(self.upstream, "level")
                    else None,
                    "downstream_level": self.downstream.level
                    if self.downstream and hasattr(self.downstream, "level")
                    else None,
                },
            )
        else:
            # Scrap unit
            self.units_scrapped += 1

            # Log scrap event
            logger.debug(
                f"Unit scrapped by {self.config.id}",
                extra={
                    "extra_data": {
                        "equipment_id": self.config.id,
                        "product_id": self.current_product,
                        "units_scrapped": self.units_scrapped,
                        "timestamp": self.env.now,
                    }
                },
            )

            self.emit_observable(
                event_type="unit_scrapped",
                details={
                    "product_id": self.current_product,
                    "order_id": self.current_order,
                    "reason": "quality_failure",
                    "shift": self.current_shift,
                    "cycles_since_maintenance": self.cycles_since_maintenance,
                },
            )

        # Update counters
        self.cycles_since_maintenance += 1
        self.total_runtime += cycle_time

        # Energy consumption
        self.energy_consumed += self.energy_rate * (cycle_time / 60.0)

    def _calculate_cycle_time(self) -> float:
        """Calculate actual cycle time with variations.

        Returns:
            Cycle time in minutes
        """
        base_cycle = 1.0 / self.base_rate  # minutes per unit

        # Apply product-specific performance factor if configured
        # Performance factor < 1.0 means SLOWER production (longer cycle time)
        # Performance factor > 1.0 means FASTER production (shorter cycle time)
        if self.current_product:
            product_factor = self._get_product_performance()
            actual_cycle = base_cycle / product_factor  # Divide to apply performance
        else:
            actual_cycle = base_cycle

        # Add random variation (±10%)
        variation = random.uniform(0.9, 1.1)

        # Apply shift performance if configured
        if self.current_shift:
            shift_factor = self._get_shift_factor()
            actual_cycle *= shift_factor

        return actual_cycle * variation  # type: ignore[no-any-return]

    def _quality_check(self) -> bool:
        """Determine if produced unit passes quality check.

        Returns:
            True if unit is good quality, False if scrapped
        """
        # Base scrap rate
        scrap_rate = self.config.get_property("base_scrap_rate", 0.02)

        # Adjust for quality factor
        adjusted_rate = scrap_rate / self.quality_factor

        # Increase scrap rate based on runtime since maintenance
        maintenance_factor = 1.0 + (self.cycles_since_maintenance / 10000.0)
        adjusted_rate *= maintenance_factor

        # Product-specific scrap rate
        if self.current_product:
            product_scrap = self.config.get_property(f"scrap_rate_{self.current_product}", scrap_rate)
            adjusted_rate = product_scrap

        return random.random() > adjusted_rate  # type: ignore[no-any-return]

    def _handle_starved(self) -> Generator:
        """Handle starved state when no input material available."""
        self._change_state(EquipmentState.STARVED)

        # Wait for material to become available
        yield self.env.timeout(0.1)  # Check every 0.1 minutes

        self.emit_observable(
            event_type="equipment_starved",
            details={
                "duration": 0.1,
                "upstream_id": self.upstream.config.id if self.upstream else None,
                "upstream_level": 0,
            },
            severity="WARNING",
        )

    def _handle_blocked(self) -> Generator:
        """Handle blocked state when downstream is full."""
        self._change_state(EquipmentState.BLOCKED)

        # Wait for downstream space
        yield self.env.timeout(0.1)  # Check every 0.1 minutes

        self.emit_observable(
            event_type="equipment_blocked",
            details={
                "duration": 0.1,
                "downstream_id": self.downstream.config.id if self.downstream else None,
                "downstream_level": self.downstream.capacity
                if self.downstream and hasattr(self.downstream, "capacity")
                else None,
            },
            severity="WARNING",
        )

    def _handle_interrupt(self, interrupt: simpy.Interrupt) -> Generator:
        """Handle process interruption.

        Args:
            interrupt: SimPy interrupt with cause information
        """
        cause = interrupt.cause

        if isinstance(cause, dict):
            interrupt_type = cause.get("type", "unknown")

            if interrupt_type == "failure":
                yield from self._handle_failure(cause)
            elif interrupt_type == "maintenance":
                yield from self._handle_maintenance(cause)
            elif interrupt_type == "changeover":
                yield from self._handle_changeover(cause)

    def _handle_failure(self, failure_info: Dict[str, Any]) -> Generator:
        """Handle equipment failure.

        Args:
            failure_info: Information about the failure
        """
        self._change_state(EquipmentState.STOPPED_FAILURE)

        failure_mode = failure_info.get("mode")
        duration = failure_info.get("duration", 10.0)

        self.emit_observable(
            event_type="equipment_failure",
            details={
                "failure_mode": failure_mode.name if failure_mode else "unknown",
                "downtime_code": failure_mode.downtime_code if failure_mode else "UNP-UNKNOWN",
                "expected_duration": duration,
                "cycles_since_maintenance": self.cycles_since_maintenance,
                "total_runtime": self.total_runtime,
                "cascade_probability": failure_mode.cascade_probability if failure_mode else 0.0,
            },
            severity="ERROR",
        )

        # Failure duration
        yield self.env.timeout(duration)

        # Check for cascade failure
        if failure_mode and random.random() < failure_mode.cascade_probability:
            self._trigger_cascade_failure()

        self._change_state(EquipmentState.RUNNING)

    def _handle_maintenance(self, maintenance_info: Dict[str, Any]) -> Generator:
        """Handle planned maintenance."""
        self._change_state(EquipmentState.STOPPED_MAINTENANCE)

        duration = maintenance_info.get("duration", 30.0)

        self.emit_observable(
            event_type="planned_maintenance",
            details={
                "duration": duration,
                "cycles_before": self.cycles_since_maintenance,
            },
        )

        yield self.env.timeout(duration)

        # Reset maintenance counter
        self.cycles_since_maintenance = 0

        self._change_state(EquipmentState.RUNNING)

    def _handle_changeover(self, changeover_info: Dict[str, Any]) -> Generator:
        """Handle product changeover."""
        self._change_state(EquipmentState.CHANGEOVER)

        old_product = self.current_product
        new_product = changeover_info.get("new_product")
        duration = changeover_info.get("duration", 45.0)

        self.emit_observable(
            event_type="changeover",
            details={
                "old_product": old_product,
                "new_product": new_product,
                "duration": duration,
                "downtime_code": "PLN-CO",
            },
        )

        yield self.env.timeout(duration)

        self.current_product = new_product
        self._change_state(EquipmentState.RUNNING)

    def failure_process(self) -> Generator:
        """Background process for random failures."""
        while self.is_running:
            # Wait for next check interval (5 minutes)
            yield self.env.timeout(5.0)

            # Only fail if running
            if self.state == EquipmentState.RUNNING:
                for mode in self.failure_modes:
                    if random.random() < mode.probability_per_5min:
                        # Trigger failure
                        duration = random.uniform(*mode.duration_range)

                        # Apply contextual factors
                        duration *= mode.recovery_time_factor

                        # Interrupt main process
                        if self.process and not self.process.triggered:
                            self.process.interrupt({"type": "failure", "mode": mode, "duration": duration})
                        break  # Only one failure at a time

    def monitor_process(self) -> Generator:
        """Background process for periodic monitoring."""
        while self.is_running:
            # Monitor every minute
            yield self.env.timeout(1.0)

            # Emit monitoring observable
            self.emit_observable(
                event_type="equipment_monitor",
                details={
                    "state": self.state.value,
                    "units_produced": self.units_produced,
                    "units_scrapped": self.units_scrapped,
                    "oee": self.calculate_oee(),
                    "energy_consumed": self.energy_consumed,
                    "upstream_level": self.upstream.level
                    if self.upstream and hasattr(self.upstream, "level")
                    else None,
                    "downstream_level": self.downstream.level
                    if self.downstream and hasattr(self.downstream, "level")
                    else None,
                },
                severity="DEBUG",
            )

    def _change_state(self, new_state: EquipmentState) -> None:
        """Change equipment state and emit observable.

        Args:
            new_state: New equipment state
        """
        if new_state != self.state:
            old_state = self.state
            state_duration = self.env.now - self.state_start_time

            self.previous_state = self.state
            self.state = new_state
            self.state_start_time = self.env.now

            # Log state transition with critical information
            logger.info(
                f"Equipment state changed: {old_state.value} -> {new_state.value}",
                extra={
                    "extra_data": {
                        "equipment_id": self.config.id,
                        "old_state": old_state.value,
                        "new_state": new_state.value,
                        "duration_in_state": state_duration,
                        "timestamp": self.env.now,
                        "product": self.current_product,
                        "shift": self.current_shift,
                    }
                },
            )

            self.emit_observable(
                event_type="state_change",
                details={
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "duration_in_old_state": state_duration,
                    "product": self.current_product,
                    "shift": self.current_shift,
                },
            )

    def _get_shift_factor(self) -> float:
        """Get performance factor for current shift.

        Returns:
            Performance multiplier for shift
        """
        # This would be configured in manifest
        shift_factors = {
            "shift1": random.uniform(0.95, 1.05),
            "shift2": random.uniform(0.90, 1.00),
            "shift3": random.uniform(0.85, 0.95),
        }
        return shift_factors.get(self.current_shift, 1.0) if self.current_shift else 1.0

    def _get_product_factor(self) -> float:
        """Get performance factor for current product.

        Returns:
            Performance multiplier for product
        """
        # Product-specific performance from config
        return self.config.get_property(f"performance_{self.current_product}", 1.0)  # type: ignore[no-any-return]

    def _get_product_performance(self) -> float:
        """Get performance factor for current product from manifest.

        Returns:
            Performance multiplier for product (0-1 range, where 1.0 is nominal)
        """
        # Check for performance_by_product in config
        perf_by_product = self.config.get_property("performance_by_product", {})
        if self.current_product and self.current_product in perf_by_product:
            return perf_by_product[self.current_product]  # type: ignore[no-any-return]
        return 1.0  # Default to nominal performance

    def _trigger_cascade_failure(self) -> None:
        """Trigger cascade failure in downstream equipment."""
        if self.downstream:
            self.emit_observable(
                event_type="cascade_failure_triggered",
                details={
                    "source": self.config.id,
                    "target": self.downstream.config.id if hasattr(self.downstream, "config") else "unknown",
                },
                severity="WARNING",
            )

    def calculate_oee(self) -> float:
        """Calculate Overall Equipment Effectiveness.

        Returns:
            OEE percentage (0-100)
        """
        if self.env.now == 0:
            return 0.0

        # Availability
        running_time = sum(
            o["duration_in_old_state"]
            for o in self.get_observables("state_change")
            if o["old_state"] == EquipmentState.RUNNING.value
        )
        availability = running_time / self.env.now if self.env.now > 0 else 0

        # Performance
        theoretical_output = self.base_rate * running_time
        actual_output = self.units_produced + self.units_scrapped
        performance = actual_output / theoretical_output if theoretical_output > 0 else 0

        # Quality
        quality = self.units_produced / actual_output if actual_output > 0 else 0

        return availability * performance * quality * 100

    def set_product(self, product_id: str, order_id: str) -> None:
        """Set current product being processed.

        Args:
            product_id: Product identifier
            order_id: Production order identifier
        """
        self.current_product = product_id
        self.current_order = order_id

        self.emit_observable(
            event_type="product_assigned",
            details={"product": product_id, "order": order_id},
        )

    def set_shift(self, shift_id: str) -> None:
        """Set current shift.

        Args:
            shift_id: Shift identifier
        """
        self.current_shift = str(shift_id) if shift_id else None

        self.emit_observable(
            event_type="shift_change",
            details={"shift": shift_id, "performance_factor": self._get_shift_factor()},
        )
