"""Fixed equipment primitive with proper material flow control."""

import logging
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generator, Optional, Tuple

import simpy

from twin_model.primitives.base import PrimitiveConfig, BasePrimitive
from twin_model.types import ArrivalPattern, ProductionUnit

logger = logging.getLogger(__name__)


class EquipmentState(Enum):
    """Equipment operational states."""
    
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STARVED = "STARVED"
    BLOCKED = "BLOCKED"
    CHANGEOVER = "CHANGEOVER"
    STOPPED_FAILURE = "STOPPED_FAILURE"
    STOPPED_MAINTENANCE = "STOPPED_MAINTENANCE"
    STOPPED_BREAK = "STOPPED_BREAK"


class FailureType(Enum):
    """Types of equipment failures."""
    
    MICRO_STOP = "micro_stop"
    MINOR_FAILURE = "minor_failure"
    MAJOR_FAILURE = "major_failure"


@dataclass
class EquipmentPrimitiveV2(BasePrimitive):
    """Fixed equipment with proper material flow.
    
    Key improvements:
    - Direct transfer to downstream equipment without double queuing
    - Proper blocking detection and handling
    - Non-blocking checks for queue status
    
    Attributes:
        input_queue: Queue for incoming material
        output_queue: Queue for outgoing material (only used if no downstream)
        upstream_equipment: Previous equipment in line
        downstream_equipment: Next equipment in line
    """
    
    config: PrimitiveConfig
    
    # Core processing parameters
    base_rate: float = 80.0  # Units per minute
    performance_factor: float = 0.85
    scrap_rate: float = 0.05
    
    # Queue configuration
    internal_queue_size: int = 20
    
    # Failure parameters
    micro_stop_probability: float = 0.15  # Per 5-minute interval
    micro_stop_duration: float = 0.5  # Minutes
    minor_failure_probability: float = 0.02
    major_failure_probability: float = 0.01
    mtbf: float = 240  # Mean time between failures
    mttr: float = 15  # Mean time to repair
    equipment_wear: float = 1.0
    
    # State tracking
    state: EquipmentState = field(default=EquipmentState.IDLE, init=False)
    state_durations: Dict[EquipmentState, float] = field(default_factory=dict, init=False)
    state_start_time: float = field(default=0.0, init=False)
    
    # Production tracking
    units_produced: int = field(default=0, init=False)
    units_scrapped: int = field(default=0, init=False)
    current_product: Optional[str] = field(default=None, init=False)
    current_order: Optional[str] = field(default=None, init=False)
    
    # Failure tracking
    failure_count: int = field(default=0, init=False)
    micro_stop_count: int = field(default=0, init=False)
    minor_failure_count: int = field(default=0, init=False)
    major_failure_count: int = field(default=0, init=False)
    
    # Internal queues
    input_queue: Optional[simpy.Store] = field(default=None, init=False)
    output_queue: Optional[simpy.Store] = field(default=None, init=False)
    
    # Connections
    upstream_equipment: Optional['EquipmentPrimitiveV2'] = field(default=None, init=False)
    downstream_equipment: Optional['EquipmentPrimitiveV2'] = field(default=None, init=False)
    
    # Process handles
    process: Optional[simpy.Process] = field(default=None, init=False)
    failure_process: Optional[simpy.Process] = field(default=None, init=False)
    
    # Control flags
    warmup_complete: bool = field(default=True, init=False)
    running: bool = field(default=False, init=False)
    
    def __post_init__(self) -> None:
        """Initialize equipment after dataclass init."""
        super().__post_init__()
        
        # Validate config
        if self.config.type != "EQUIPMENT":
            raise ValueError(f"Equipment requires EQUIPMENT type, got {self.config.type}")
        
        # Initialize state durations
        for state in EquipmentState:
            self.state_durations[state] = 0.0
        
        # Create queues
        self.input_queue = simpy.Store(self.env, capacity=self.internal_queue_size)
        self.output_queue = simpy.Store(self.env, capacity=self.internal_queue_size)
        
        # Extract parameters from config properties
        props = self.config.properties
        self.base_rate = props.get('base_rate', self.base_rate)
        self.performance_factor = props.get('performance_factor', self.performance_factor)
        self.scrap_rate = props.get('scrap_rate', self.scrap_rate)
        self.internal_queue_size = props.get('internal_queue_size', self.internal_queue_size)
        self.micro_stop_probability = props.get('micro_stop_probability', self.micro_stop_probability)
        self.mtbf = props.get('mtbf', self.mtbf)
        self.mttr = props.get('mttr', self.mttr)
        
        logger.debug(f"Initialized {self.config.id}: rate={self.base_rate}, perf={self.performance_factor}")
    
    def connect_to(self, downstream_equipment: 'EquipmentPrimitiveV2') -> None:
        """Connect this equipment to downstream equipment.
        
        Args:
            downstream_equipment: Next equipment in line
        """
        self.downstream_equipment = downstream_equipment
        downstream_equipment.upstream_equipment = self
        logger.debug(f"Connected {self.config.id} → {downstream_equipment.config.id}")
    
    def start(self) -> None:
        """Start the equipment processes."""
        if not self.running:
            self.running = True
            self.process = self.env.process(self.run())
            self.failure_process = self.env.process(self._failure_process())
            logger.info(f"{self.config.id}: Started")
    
    def stop(self) -> None:
        """Stop the equipment processes."""
        if self.running:
            self.running = False
            if self.process and self.process.is_alive:
                self.process.interrupt()
            if self.failure_process and self.failure_process.is_alive:
                self.failure_process.interrupt()
            logger.info(f"{self.config.id}: Stopped")
    
    def run(self) -> Generator:
        """Main equipment process loop with proper flow control."""
        logger.info(f"{self.config.id}: Starting main process")
        
        while self.running:
            try:
                # Check if we have input material
                if len(self.input_queue.items) == 0:
                    # No input material - we're starved
                    yield self.env.process(self._handle_starved())
                    continue
                
                # Check if downstream can accept output
                if self._is_blocked():
                    # Downstream is full - we're blocked
                    yield self.env.process(self._handle_blocked())
                    continue
                
                # We can process - change to RUNNING
                if self.state != EquipmentState.RUNNING:
                    self._change_state(EquipmentState.RUNNING)
                
                # Get input material
                unit = yield self.input_queue.get()
                
                # Process the unit
                yield self.env.process(self._process_unit(unit))
                
            except simpy.Interrupt as interrupt:
                # Handle failures
                yield self.env.process(self._handle_interrupt(interrupt))
            except Exception as e:
                logger.error(f"{self.config.id}: Error in main process: {e}")
                yield self.env.timeout(1)
    
    def _is_blocked(self) -> bool:
        """Check if equipment is blocked by downstream.
        
        Returns:
            True if blocked, False otherwise
        """
        if self.downstream_equipment:
            # Check if downstream input queue is full
            if hasattr(self.downstream_equipment, 'input_queue'):
                downstream_queue = self.downstream_equipment.input_queue
                return len(downstream_queue.items) >= downstream_queue.capacity
        else:
            # No downstream, check our output queue
            return len(self.output_queue.items) >= self.output_queue.capacity
        return False
    
    def _process_unit(self, unit: Any) -> Generator:
        """Process a single unit with proper output handling.
        
        Args:
            unit: The unit to process
        """
        # Extract product info
        if isinstance(unit, ProductionUnit):
            self.current_product = unit.product_id
            self.current_order = unit.order_id
        
        # Calculate processing time
        product_rate = self.config.properties.get(
            f'rate_{self.current_product}',
            self.base_rate
        )
        theoretical_time = 1.0 / (product_rate / 60.0)
        
        # Apply performance factor
        product_performance = self.config.properties.get(
            f'performance_{self.current_product}',
            self.performance_factor
        )
        actual_time = theoretical_time / product_performance
        
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
            self.emit_observable("unit_scrapped", {
                "equipment_id": self.config.id,
                "product_id": self.current_product,
                "reason": "quality_failure"
            })
        else:
            # Good unit - prepare for output
            if not isinstance(unit, ProductionUnit):
                unit = ProductionUnit(
                    product_id=self.current_product,
                    order_id=self.current_order,
                    quality=1.0 - self.scrap_rate,
                    timestamp=self.env.now
                )
            else:
                unit.quality = 1.0 - self.scrap_rate
            
            # Transfer directly to downstream or output queue
            if self.downstream_equipment and hasattr(self.downstream_equipment, 'input_queue'):
                # Direct transfer to downstream equipment
                yield self.downstream_equipment.input_queue.put(unit)
            else:
                # No downstream equipment, put in output queue
                yield self.output_queue.put(unit)
            
            self.units_produced += 1
            
            self.emit_observable("unit_produced", {
                "equipment_id": self.config.id,
                "product_id": self.current_product,
                "order_id": self.current_order
            })
    
    def _handle_starved(self) -> Generator:
        """Handle starved state (no input material)."""
        if self.state != EquipmentState.STARVED:
            self._change_state(EquipmentState.STARVED)
            self.emit_observable("equipment_starved", {"equipment_id": self.config.id})
        
        # Wait briefly before checking again
        yield self.env.timeout(0.1)
    
    def _handle_blocked(self) -> Generator:
        """Handle blocked state (output queue full)."""
        if self.state != EquipmentState.BLOCKED:
            self._change_state(EquipmentState.BLOCKED)
            self.emit_observable("equipment_blocked", {"equipment_id": self.config.id})
        
        # Wait briefly before checking again
        yield self.env.timeout(0.1)
    
    def _handle_interrupt(self, interrupt: simpy.Interrupt) -> Generator:
        """Handle process interruption.
        
        Args:
            interrupt: Interruption cause
        """
        cause = interrupt.cause if hasattr(interrupt, 'cause') else None
        
        if isinstance(cause, dict):
            failure_type = cause.get('type')
            duration = cause.get('duration', 10)
            
            if failure_type in [FailureType.MICRO_STOP, FailureType.MINOR_FAILURE, FailureType.MAJOR_FAILURE]:
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
                
                logger.info(f"{self.config.id}: {failure_type.value} at {self.env.now:.1f}, repair: {duration:.1f} min")
                
                self.emit_observable("equipment_failure", {
                    "equipment_id": self.config.id,
                    "failure_type": failure_type.value,
                    "duration": duration
                })
                
                # Interrupt main process
                self.process.interrupt({
                    'type': failure_type,
                    'duration': duration
                })
    
    def _get_next_failure(self) -> Tuple[FailureType, float]:
        """Determine next failure using competing risks model.
        
        Returns:
            Tuple of (failure_type, time_to_failure in minutes)
        """
        # Get current parameters
        micro_stop_prob = self.micro_stop_probability
        minor_prob = self.config.properties.get('minor_failure_probability', 0.02)
        major_prob = self.config.properties.get('major_failure_probability', 0.01)
        equipment_wear = self.equipment_wear
        
        # Convert probabilities to rates
        # Probability per 5 minutes to rate per minute
        micro_stop_rate = -math.log(1 - micro_stop_prob) / 5.0 * equipment_wear if micro_stop_prob > 0 else 0
        minor_rate = -math.log(1 - minor_prob) / 60.0 * equipment_wear if minor_prob > 0 else 0
        major_rate = -math.log(1 - major_prob) / 480.0 * equipment_wear if major_prob > 0 else 0
        
        # Generate time to each failure type
        times = {}
        if micro_stop_rate > 0:
            times[FailureType.MICRO_STOP] = random.expovariate(micro_stop_rate)
        if minor_rate > 0:
            times[FailureType.MINOR_FAILURE] = random.expovariate(minor_rate)
        if major_rate > 0:
            times[FailureType.MAJOR_FAILURE] = random.expovariate(major_rate)
        
        # Find earliest failure
        if times:
            failure_type = min(times, key=times.get)
            time_to_failure = times[failure_type]
        else:
            # No failures configured
            failure_type = FailureType.MICRO_STOP
            time_to_failure = 1000000  # Very long time
        
        return failure_type, time_to_failure
    
    def _get_repair_duration(self, failure_type: FailureType) -> float:
        """Get repair duration for failure type.
        
        Args:
            failure_type: Type of failure
            
        Returns:
            Repair duration in minutes
        """
        if failure_type == FailureType.MICRO_STOP:
            return self.micro_stop_duration * random.uniform(0.8, 1.2)
        elif failure_type == FailureType.MINOR_FAILURE:
            return 10 * random.uniform(0.8, 1.2)  # 8-12 minutes
        elif failure_type == FailureType.MAJOR_FAILURE:
            return self.mttr * random.uniform(0.8, 1.2)
        else:
            return self.mttr
    
    def _change_state(self, new_state: EquipmentState) -> None:
        """Change equipment state and track duration.
        
        Args:
            new_state: New equipment state
        """
        if hasattr(self, 'state'):
            # Update duration for previous state
            if hasattr(self, 'state_start_time'):
                duration = self.env.now - self.state_start_time
                self.state_durations[self.state] += duration
        
        # Change state
        self.state = new_state
        self.state_start_time = self.env.now
        
        logger.debug(f"{self.config.id}: State changed to {new_state.value}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get equipment statistics.
        
        Returns:
            Dictionary of statistics
        """
        total_time = self.env.now
        
        # Calculate availability
        running_time = self.state_durations.get(EquipmentState.RUNNING, 0)
        availability = running_time / total_time if total_time > 0 else 0
        
        # Calculate performance
        theoretical_output = running_time * self.base_rate
        actual_output = self.units_produced
        performance = actual_output / theoretical_output if theoretical_output > 0 else 0
        
        # Calculate quality
        total_units = self.units_produced + self.units_scrapped
        quality = self.units_produced / total_units if total_units > 0 else 0
        
        # Calculate OEE
        oee = availability * performance * quality
        
        return {
            'equipment_id': self.config.id,
            'units_produced': self.units_produced,
            'units_scrapped': self.units_scrapped,
            'availability': availability,
            'performance': performance,
            'quality': quality,
            'oee': oee,
            'state_durations': dict(self.state_durations),
            'failure_count': self.failure_count,
            'micro_stop_count': self.micro_stop_count,
            'minor_failure_count': self.minor_failure_count,
            'major_failure_count': self.major_failure_count
        }