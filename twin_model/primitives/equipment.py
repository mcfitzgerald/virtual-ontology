"""Equipment primitive with internal queues only.

This module provides equipment primitives that use internal queues
for material handling. NO EXTERNAL BUFFERS - direct equipment connections only.
"""

from typing import Optional, Generator, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import math
import random
import numpy as np
import simpy
import logging

from .base import BasePrimitive, PrimitiveConfig, SamplingConfig

logger = logging.getLogger(__name__)


class EquipmentState(str, Enum):
    """Equipment operational states."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPED_FAILURE = "STOPPED_FAILURE"
    STOPPED_MAINTENANCE = "STOPPED_MAINTENANCE"
    STARVED = "STARVED"
    BLOCKED = "BLOCKED"
    CHANGEOVER = "CHANGEOVER"
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"


class FailureType(str, Enum):
    """Types of equipment failures."""

    MICRO_STOP = "micro_stop"
    MINOR_FAILURE = "minor_failure"
    MAJOR_FAILURE = "major_failure"


@dataclass
class ProductionUnit:
    """Represents a unit of production."""

    product_id: str
    order_id: Optional[str] = None
    quality: float = 1.0
    timestamp: float = 0.0

    @property
    def is_good(self) -> bool:
        """Check if unit meets quality threshold."""
        return self.quality >= 0.95  # 95% quality threshold


class EquipmentPrimitive(BasePrimitive):
    """Equipment with internal queues only - no external buffers.

    Key features:
    - Internal input and output queues (SimPy Stores)
    - Direct equipment-to-equipment connections
    - Realistic failure modeling
    - Product-specific performance
    - State-based operation
    """

    def __init__(
        self, env: simpy.Environment, config: PrimitiveConfig, sampling_config: Optional[SamplingConfig] = None
    ) -> None:
        """Initialize equipment with internal queues.

        Args:
            env: SimPy environment
            config: Equipment configuration
            sampling_config: Optional sampling configuration

        """
        super().__init__(env, config, sampling_config)

        # Internal queues (the ONLY queues we use!)
        queue_size = config.get_property("internal_queue_size", 20)
        self.input_queue: simpy.Store = simpy.Store(env, capacity=queue_size)
        self.output_queue: simpy.Store = simpy.Store(env, capacity=queue_size)

        # Direct equipment connections (no buffers!)
        self.upstream_equipment: Optional["EquipmentPrimitive"] = None
        self.downstream_equipment: Optional["EquipmentPrimitive"] = None

        # Equipment parameters
        self.equipment_type = config.get_property("equipment_type", "Generic")
        self.line_id = config.get_property("line_id", "LINE1")
        self.position = config.get_property("position", 1)
        self.base_rate = config.get_property("base_rate", 60.0)
        self.mtbf = config.get_property("mtbf", 480.0)
        self.mttr = config.get_property("mttr", 30.0)

        # State management
        self.state = EquipmentState.IDLE
        self.previous_state = EquipmentState.IDLE
        self.state_start_time = 0.0
        self.state_durations: Dict[EquipmentState, float] = {state: 0.0 for state in EquipmentState}

        # Production tracking
        self.units_produced = 0
        self.units_scrapped = 0
        self.current_product = config.get_property("default_product", "SKU-1001")
        self.current_order = config.get_property("default_order", None)

        # Performance factors
        self.performance_factor = config.get_property("performance_factor", 0.85)
        self.scrap_rate = config.get_property("scrap_rate", 0.05)

        # Failure parameters (from control system)
        self.micro_stop_probability = config.get_property("micro_stop_probability", 0.3)
        self.micro_stop_duration_mean = config.get_property("micro_stop_duration_mean", 0.0)
        self.micro_stop_duration_sigma = config.get_property("micro_stop_duration_sigma", 0.5)

        # Failure tracking
        self.failure_count: int = 0
        self.micro_stop_count: int = 0
        self.minor_failure_count: int = 0
        self.major_failure_count: int = 0

        # Warmup period
        self.warmup_period = config.get_property("warmup_period", 5.0)
        self.warmup_complete = False

        # Process reference
        self.process: Optional[simpy.Process] = None
        self.failure_process: Optional[simpy.Process] = None

        logger.info(f"Equipment {self.config.id} initialized with internal queues (size={queue_size})")

    def connect_to(self, other: BasePrimitive, relationship_type: str = "feeds_into") -> None:
        """Connect this equipment to downstream equipment.

        Args:
            other: Next equipment in line
            relationship_type: Type of relationship (default: feeds_into)

        """
        # Call parent implementation
        super().connect_to(other, relationship_type)

        # Equipment-specific connection logic
        if isinstance(other, EquipmentPrimitive) and relationship_type == "feeds_into":
            self.downstream_equipment = other
            other.upstream_equipment = self
            logger.debug(f"Connected {self.config.id} → {other.config.id}")

    def run(self) -> Generator:
        """Run main equipment process."""
        # Start failure process
        self.failure_process = self.env.process(self._failure_process())

        # Warmup period
        if self.warmup_period > 0:
            yield self.env.timeout(self.warmup_period)
        self.warmup_complete = True
        logger.debug(f"{self.config.id}: Warmup complete at {self.env.now}")

        # Main processing loop
        while True:
            try:
                # Check for material in input queue
                if len(self.input_queue.items) == 0:
                    # No material - go to STARVED
                    yield from self._handle_starved()
                    continue

                # Check if downstream is blocked
                if self._is_blocked():
                    # Output blocked - go to BLOCKED
                    yield from self._handle_blocked()
                    continue

                # Process a unit
                yield from self._process_unit()

            except simpy.Interrupt as interrupt:
                # Handle interruptions (failures, maintenance)
                yield from self._handle_interrupt(interrupt)

            except Exception as e:
                logger.error(f"{self.config.id}: Error in run process: {e}")
                yield self.env.timeout(1)  # Brief pause before retry

    def _process_unit(self) -> Generator:
        """Process a single unit of production."""
        # Change state to RUNNING
        self._change_state(EquipmentState.RUNNING)

        # Get unit from input queue
        unit = yield self.input_queue.get()

        # Calculate processing time
        base_time = 1.0 / self.base_rate  # Minutes per unit
        
        # Apply performance factors (lower performance = slower processing)
        # Performance factor of 0.5 means running at 50% speed, so takes 2x longer
        combined_performance = self.performance_factor
        
        # Apply product-specific performance if available
        product_performance = self.config.get_property(f"performance_by_product.{self.current_product}", 1.0)
        combined_performance *= product_performance
        
        # Calculate actual time (slower performance = longer time)
        actual_time = base_time / combined_performance if combined_performance > 0 else base_time

        # Process the unit (interruptible for failures)
        try:
            yield self.env.timeout(actual_time)
        except simpy.Interrupt as interrupt:
            # Re-raise to be handled by outer try-except
            raise interrupt

        # Quality check
        if random.random() < self.scrap_rate:
            # Unit is scrapped
            self.units_scrapped += 1
            self.emit_observable(
                "unit_scrapped",
                {"equipment_id": self.config.id, "product_id": self.current_product, "reason": "quality_failure"},
            )
        else:
            # Good unit - send to output queue
            if isinstance(unit, ProductionUnit):
                unit.quality = 1.0 - self.scrap_rate
            else:
                unit = ProductionUnit(
                    product_id=self.current_product,
                    order_id=self.current_order,
                    quality=1.0 - self.scrap_rate,
                    timestamp=self.env.now,
                )

            # Transfer directly to downstream or output queue
            if self.downstream_equipment and hasattr(self.downstream_equipment, "input_queue"):
                # Direct transfer to downstream equipment (no double queuing)
                yield self.downstream_equipment.input_queue.put(unit)
            else:
                # No downstream equipment or it's a sink - put in output queue
                yield self.output_queue.put(unit)

            self.units_produced += 1

            self.emit_observable(
                "unit_produced",
                {"equipment_id": self.config.id, "product_id": self.current_product, "order_id": self.current_order},
            )

    def _is_blocked(self) -> bool:
        """Check if equipment is blocked by downstream.

        Returns:
            True if blocked, False otherwise

        """
        if self.downstream_equipment and hasattr(self.downstream_equipment, "input_queue"):
            # Check if downstream input queue is full
            downstream_queue = self.downstream_equipment.input_queue
            return len(downstream_queue.items) >= downstream_queue.capacity
        else:
            # No downstream equipment, check our output queue
            return len(self.output_queue.items) >= self.output_queue.capacity

    def _handle_starved(self) -> Generator:
        """Handle starved state (no input material)."""
        if self.state != EquipmentState.STARVED:
            self._change_state(EquipmentState.STARVED)
            self.emit_observable("equipment_starved", {"equipment_id": self.config.id})

        # Wait for material to arrive
        yield self.env.timeout(0.1)  # Check every 0.1 minutes

    def _handle_blocked(self) -> Generator:
        """Handle blocked state (output queue full)."""
        if self.state != EquipmentState.BLOCKED:
            self._change_state(EquipmentState.BLOCKED)
            self.emit_observable("equipment_blocked", {"equipment_id": self.config.id})

        # Wait for output space
        yield self.env.timeout(0.1)  # Check every 0.1 minutes

    def _handle_interrupt(self, interrupt: simpy.Interrupt) -> Generator:
        """Handle process interruption.

        Args:
            interrupt: Interruption cause

        """
        cause = interrupt.cause if hasattr(interrupt, "cause") else None

        if isinstance(cause, dict):
            failure_type = cause.get("type")
            duration = cause.get("duration", 10)

            if failure_type == FailureType.MICRO_STOP:
                self._change_state(EquipmentState.STOPPED_FAILURE)
                yield self.env.timeout(duration)

            elif failure_type == FailureType.MINOR_FAILURE:
                self._change_state(EquipmentState.STOPPED_FAILURE)
                yield self.env.timeout(duration)

            elif failure_type == FailureType.MAJOR_FAILURE:
                self._change_state(EquipmentState.STOPPED_FAILURE)
                yield self.env.timeout(duration)

            else:
                # Generic failure
                self._change_state(EquipmentState.STOPPED_FAILURE)
                yield self.env.timeout(self.mttr)
        else:
            # Unknown interruption
            yield self.env.timeout(1)

    def _failure_process(self) -> Generator:
        """Generate equipment failures based on realistic patterns."""
        while True:
            # Wait until warmup is complete
            if not self.warmup_complete:
                yield self.env.timeout(1)
                continue

            # Only fail when running
            if self.state != EquipmentState.RUNNING:
                yield self.env.timeout(1)
                continue

            # Determine next failure
            failure_type, time_to_failure = self._get_next_failure()

            # Wait for failure to occur
            yield self.env.timeout(time_to_failure)

            # Generate failure
            if self.state == EquipmentState.RUNNING and self.process:
                # Track failure counts
                self.failure_count += 1
                if failure_type == FailureType.MICRO_STOP:
                    self.micro_stop_count += 1
                elif failure_type == FailureType.MINOR_FAILURE:
                    self.minor_failure_count += 1
                elif failure_type == FailureType.MAJOR_FAILURE:
                    self.major_failure_count += 1

                duration = self._get_repair_duration(failure_type)

                logger.info(
                    f"{self.config.id}: {failure_type.value} occurred at {self.env.now:.1f}, repair: {duration:.1f} min"
                )

                self.emit_observable(
                    "equipment_failure",
                    {"equipment_id": self.config.id, "failure_type": failure_type.value, "duration": duration},
                )

                # Interrupt main process
                self.process.interrupt({"type": failure_type, "duration": duration})

    def _get_next_failure(self) -> Tuple[FailureType, float]:
        """Determine next failure using competing risks model.

        Based on research findings:
        - 80% of stops are micro-stops (jams, sensor trips, adjustments)
        - 15% are minor failures (component issues, calibration)
        - 5% are major failures (equipment breakdown)

        Returns:
            Tuple of (failure_type, time_to_failure)

        """
        # Get failure probabilities from configuration
        micro_stop_prob = self.get_failure_config("micro_stops", "percentage", 0.80)
        minor_failure_prob = self.get_failure_config("minor_failures", "percentage", 0.15)
        major_failure_prob = self.get_failure_config("major_failures", "percentage", 0.05)

        # Adjust based on equipment age/wear if available
        equipment_wear = self.config.get_property("equipment_wear_rate", 1.0)

        # Sample time for each failure type using realistic distributions
        # Micro-stops: Frequent, short intervals (Poisson process)
        if micro_stop_prob > 0:
            # Get base rate from configuration
            base_rate = self.get_failure_config("micro_stops", "occurrence.base_rate", 20.0)
            # Convert to rate per minute: 1 stop per base_rate minutes
            micro_stop_rate = (1.0 / base_rate) * equipment_wear
            micro_stop_time = random.expovariate(micro_stop_rate) if micro_stop_rate > 0 else float("inf")
        else:
            micro_stop_time = float("inf")

        # Minor failures: Less frequent (Weibull distribution for wear-out)
        if minor_failure_prob > 0:
            # Shape parameter > 1 indicates increasing failure rate
            minor_shape = self.get_failure_config("minor_failures", "weibull_shape", 2.0)
            base_interval = self.get_failure_config("minor_failures", "base_interval", 480.0)
            minor_scale = base_interval / (minor_failure_prob * equipment_wear)
            minor_failure_time = random.weibullvariate(minor_scale, minor_shape)
        else:
            minor_failure_time = float("inf")

        # Major failures: Rare events (Log-normal for complex failures)
        if major_failure_prob > 0:
            # Use log-normal as major failures often result from cascading issues
            base_interval = self.get_failure_config("major_failures", "base_interval", 2880.0)
            major_mean = np.log(base_interval / (major_failure_prob * equipment_wear))
            major_sigma = self.get_failure_config("major_failures", "lognormal_sigma", 1.0)
            major_failure_time = np.random.lognormal(major_mean, major_sigma)
        else:
            major_failure_time = float("inf")

        # First to occur wins (competing risks)
        times = [
            (FailureType.MICRO_STOP, micro_stop_time),
            (FailureType.MINOR_FAILURE, minor_failure_time),
            (FailureType.MAJOR_FAILURE, major_failure_time),
        ]

        return min(times, key=lambda x: x[1])

    def _get_repair_duration(self, failure_type: FailureType) -> float:
        """Get repair duration based on failure type and root causes.

        Based on research:
        - Micro-stops (80%): 0.5-3 minutes (jams, sensor trips)
        - Minor failures (15%): 5-30 minutes (component adjust, calibration)
        - Major failures (5%): 30+ minutes (breakdown, part replacement)

        Args:
            failure_type: Type of failure

        Returns:
            Repair duration in minutes

        """
        # Get control-affected recovery parameters
        operator_skill = self.config.get_property("operator_skill_factor", 1.0)
        maintenance_effectiveness = self.config.get_property("maintenance_effectiveness", 1.0)

        if failure_type == FailureType.MICRO_STOP:
            # Get micro-stop causes from configuration
            causes_config = self.get_system_config("failure_distributions.micro_stops.causes", {})
            
            if causes_config:
                # Extract weights and durations from config
                cause_weights = {}
                base_durations = {}
                for cause_name, cause_data in causes_config.items():
                    cause_weights[cause_name] = cause_data.get("weight", 0.25)
                    base_durations[cause_name] = cause_data.get("duration_mean", 1.0)
            else:
                # Fallback to defaults
                cause_weights = {
                    "jam_at_handoff": 0.40,
                    "sensor_trip": 0.25,
                    "minor_adjustment": 0.15,
                    "material_issue": 0.20,
                }
                base_durations = {
                    "jam_at_handoff": 1.0,
                    "sensor_trip": 0.5,
                    "minor_adjustment": 2.0,
                    "material_issue": 1.5,
                }

            # Select cause based on weights
            cause = random.choices(list(cause_weights.keys()), weights=list(cause_weights.values()))[0]
            base_duration = base_durations[cause]
            
            # Get sigma from config for the selected cause
            sigma = self.get_system_config(f"failure_distributions.micro_stops.causes.{cause}.duration_sigma", 0.3)
            
            # Add variability and apply operator skill factor
            duration = base_duration * np.random.lognormal(0, sigma) / operator_skill
            return min(max(0.5, duration), 5.0)  # Bounded 0.5-5 minutes

        elif failure_type == FailureType.MINOR_FAILURE:
            # Minor failures require more intervention
            # Get parameters from configuration
            mean_duration = self.get_failure_config("minor_failures", "duration_mean", 15.0)
            sigma_duration = self.get_failure_config("minor_failures", "duration_sigma", 5.0)
            
            # Gamma distribution for time to diagnose and fix
            shape = 2.0  # Shape parameter
            scale = (mean_duration / shape) / maintenance_effectiveness
            duration = np.random.gamma(shape, scale)
            return min(max(5.0, duration), 30.0)  # Bounded 5-30 minutes

        elif failure_type == FailureType.MAJOR_FAILURE:
            # Major failures may require parts, specialized repair
            # Get parameters from configuration
            mean_duration = self.get_failure_config("major_failures", "duration_mean", self.mttr)
            shape = self.get_failure_config("major_failures", "weibull_shape", 1.5)
            
            # Use Weibull for complex repair scenarios
            # Scale based on configured mean and maintenance effectiveness
            scale = mean_duration / maintenance_effectiveness
            duration = random.weibullvariate(scale, shape)
            return min(max(30.0, duration), 480.0)  # Bounded 30-480 minutes

        else:
            return self.mttr

    def _change_state(self, new_state: EquipmentState) -> None:
        """Change equipment state and track duration.

        Args:
            new_state: New equipment state

        """
        if self.state != new_state:
            # Update duration for previous state
            duration = self.env.now - self.state_start_time
            self.state_durations[self.state] += duration

            # Change state
            self.previous_state = self.state
            self.state = new_state
            self.state_start_time = self.env.now

            # Emit state change event
            self.emit_observable(
                "state_change",
                {"equipment_id": self.config.id, "from_state": self.previous_state.value, "to_state": new_state.value},
            )

            logger.debug(f"{self.config.id}: {self.previous_state.value} → {new_state.value} at {self.env.now:.1f}")

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status.

        Returns:
            Queue status dictionary

        """
        return {
            "input_queue_level": len(self.input_queue.items),
            "input_queue_capacity": self.input_queue.capacity,
            "output_queue_level": len(self.output_queue.items),
            "output_queue_capacity": self.output_queue.capacity,
            "input_utilization": len(self.input_queue.items) / self.input_queue.capacity,
            "output_utilization": len(self.output_queue.items) / self.output_queue.capacity,
        }

    def get_kpis(self) -> Dict[str, float]:
        """Calculate equipment KPIs.

        Returns:
            KPI dictionary

        """
        total_time = self.env.now
        if total_time == 0:
            return {}

        # Availability
        running_time = self.state_durations[EquipmentState.RUNNING]
        self.state_durations[EquipmentState.STOPPED_FAILURE]
        scheduled_time = total_time - self.state_durations[EquipmentState.IDLE]
        availability = running_time / scheduled_time if scheduled_time > 0 else 0

        # Performance
        theoretical_output = running_time * self.base_rate
        actual_output = self.units_produced + self.units_scrapped
        performance = actual_output / theoretical_output if theoretical_output > 0 else 0

        # Quality
        quality = self.units_produced / actual_output if actual_output > 0 else 0

        # OEE
        oee = availability * performance * quality

        return {
            "availability": availability,
            "performance": performance,
            "quality": quality,
            "oee": oee,
            "units_produced": self.units_produced,
            "units_scrapped": self.units_scrapped,
            "uptime_percentage": running_time / total_time if total_time > 0 else 0,
        }

    def start(self) -> None:
        """Start the equipment processes.

        Implements the abstract start method from BasePrimitive.
        """
        self.process = self.env.process(self.run())
        self.failure_process = self.env.process(self._failure_process())
