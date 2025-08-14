"""Line Coupling Model
Explicit cascade model with buffers and stochastic variation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from enum import Enum
from .config_loader import ConfigLoader


class EquipmentStatus(Enum):
    """Equipment operational status"""

    RUNNING = "Running"
    STOPPED = "Stopped"
    STARVED = "Starved"  # No input material
    BLOCKED = "Blocked"  # Output blocked


@dataclass
class Buffer:
    """Material buffer between equipment"""

    capacity: int = 100  # TODO: HARDCODED - buffer capacity units
    current_level: int = 50  # TODO: HARDCODED - initial buffer level
    min_operating_level: int = 10  # TODO: HARDCODED - minimum operating level
    max_operating_level: int = 90  # TODO: HARDCODED - maximum operating level
    
    def is_empty(self) -> bool:
        """Check if buffer is effectively empty"""
        return self.current_level <= self.min_operating_level
    
    def is_full(self) -> bool:
        """Check if buffer is effectively full"""
        return self.current_level >= self.max_operating_level
    
    def add(self, units: int) -> int:
        """Add units to buffer
        Returns actual units added (may be less if buffer fills)
        """
        space_available: int = self.capacity - self.current_level
        units_added: int = min(units, space_available)
        self.current_level += units_added
        return units_added
    
    def remove(self, units: int) -> int:
        """Remove units from buffer
        Returns actual units removed (may be less if buffer empties)
        """
        units_removed: int = min(units, self.current_level)
        self.current_level -= units_removed
        return units_removed


@dataclass
class LineCoupling:
    """Explicit cascade model with buffers and stochastic variation
    Models how upstream stops affect downstream equipment
    """

    # Buffer parameters
    buffer_capacity: int = 100  # TODO: HARDCODED - buffer capacity units
    initial_buffer_level: int = 50  # TODO: HARDCODED - initial buffer level
    
    # Flow rates
    depletion_rate: float = 10.0  # TODO: HARDCODED - units/min when upstream stopped
    refill_rate: float = 20.0  # TODO: HARDCODED - units/min when upstream running
    
    # Stochastic parameters
    depletion_noise_std: float = 2.0  # TODO: HARDCODED - depletion variation std dev
    refill_noise_std: float = 3.0  # TODO: HARDCODED - refill variation std dev
    use_probabilistic: bool = True  # TODO: HARDCODED - enable/disable stochastic
    
    # Cascade parameters
    cascade_sensitivity: float = 0.5  # TODO: HARDCODED - 0=no cascade, 1=immediate
    cascade_delay_minutes: int = 10  # TODO: HARDCODED - time before cascade starts
    
    def __init__(self) -> None:
        """Initialize line coupling model"""
        self.loader = ConfigLoader()
        self.config = self.loader.config
        
        # Set parameters from configuration
        self.cascade_sensitivity = self.config["parameters"]["cascade_sensitivity"]["default"]
        self.cascade_delay_minutes = self.config["material_cascade"]["cascade_delay_base"]
        
        self.buffers: Dict[str, Buffer] = {}
        self.equipment_status: Dict[str, EquipmentStatus] = {}
        self.cascade_timers: Dict[str, int] = {}  # Minutes since upstream stop
        
    def initialize_line(self, equipment_ids: List[str]) -> None:
        """Initialize a production line with equipment and buffers
        
        Args:
            equipment_ids: List of equipment IDs in order (upstream to downstream)

        """
        # Create buffers between each pair of equipment
        for i in range(len(equipment_ids) - 1):
            buffer_id: str = f"{equipment_ids[i]}_to_{equipment_ids[i+1]}"
            self.buffers[buffer_id] = Buffer(
                capacity=self.buffer_capacity,
                current_level=self.initial_buffer_level
            )
        
        # Initialize all equipment as running
        for eq_id in equipment_ids:
            self.equipment_status[eq_id] = EquipmentStatus.RUNNING
            self.cascade_timers[eq_id] = 0
    
    def calculate_starvation(
        self,
        downstream_id: str,
        upstream_id: str,
        upstream_status: EquipmentStatus,
        time_interval_minutes: int = 5
    ) -> Tuple[bool, float]:
        """Calculate if downstream equipment starves due to upstream stop
        
        Args:
            downstream_id: ID of downstream equipment
            upstream_id: ID of upstream equipment
            upstream_status: Current status of upstream equipment
            time_interval_minutes: Time interval for calculation
            
        Returns:
            Tuple of (is_starved, probability_of_starvation)

        """
        buffer_id = f"{upstream_id}_to_{downstream_id}"
        
        if buffer_id not in self.buffers:
            # No buffer defined, use direct coupling
            if upstream_status in [EquipmentStatus.STOPPED, EquipmentStatus.STARVED]:
                return (True, self.cascade_sensitivity)
            return (False, 0.0)
        
        buffer = self.buffers[buffer_id]
        
        if upstream_status == EquipmentStatus.RUNNING:
            # Upstream running, refill buffer
            if self.use_probabilistic:
                actual_refill = np.random.normal(
                    self.refill_rate * time_interval_minutes,
                    self.refill_noise_std * np.sqrt(time_interval_minutes)
                )
            else:
                actual_refill = self.refill_rate * time_interval_minutes
            
            buffer.add(int(max(0, actual_refill)))
            self.cascade_timers[downstream_id] = 0  # Reset cascade timer
            return (False, 0.0)
        
        else:  # Upstream stopped or starved
            # Increment cascade timer
            self.cascade_timers[downstream_id] += time_interval_minutes
            
            # Check if cascade delay has passed
            if self.cascade_timers[downstream_id] < self.cascade_delay_minutes:
                # Still within delay period, use buffer
                if self.use_probabilistic:
                    actual_depletion = np.random.normal(
                        self.depletion_rate * time_interval_minutes,
                        self.depletion_noise_std * np.sqrt(time_interval_minutes)
                    )
                else:
                    actual_depletion = self.depletion_rate * time_interval_minutes
                
                buffer.remove(int(max(0, actual_depletion)))
                
                if buffer.is_empty():
                    # Buffer depleted, downstream starves
                    return (True, 1.0)
                else:
                    # Buffer still has material
                    depletion_prob = 1.0 - (buffer.current_level / buffer.capacity)
                    return (False, depletion_prob * self.cascade_sensitivity)
            
            else:
                # Cascade delay passed, apply sensitivity
                if self.use_probabilistic:
                    # Probabilistic cascade based on sensitivity
                    cascade_prob = self.cascade_sensitivity
                    if np.random.random() < cascade_prob:
                        return (True, cascade_prob)
                    else:
                        # Lucky - cascade didn't happen this interval
                        return (False, cascade_prob)
                else:
                    # Deterministic cascade
                    if self.cascade_sensitivity > 0.5:
                        return (True, self.cascade_sensitivity)
                    else:
                        return (False, self.cascade_sensitivity)
    
    def calculate_blockage(
        self,
        upstream_id: str,
        downstream_id: str,
        downstream_status: EquipmentStatus,
        time_interval_minutes: int = 5
    ) -> Tuple[bool, float]:
        """Calculate if upstream equipment blocks due to downstream stop
        
        Args:
            upstream_id: ID of upstream equipment
            downstream_id: ID of downstream equipment
            downstream_status: Current status of downstream equipment
            time_interval_minutes: Time interval for calculation
            
        Returns:
            Tuple of (is_blocked, probability_of_blockage)

        """
        buffer_id = f"{upstream_id}_to_{downstream_id}"
        
        if buffer_id not in self.buffers:
            # No buffer, direct blockage
            if downstream_status in [EquipmentStatus.STOPPED, EquipmentStatus.BLOCKED]:
                return (True, self.cascade_sensitivity)
            return (False, 0.0)
        
        buffer = self.buffers[buffer_id]
        
        if downstream_status == EquipmentStatus.RUNNING:
            # Downstream running, can accept material
            return (False, 0.0)
        
        else:  # Downstream stopped or blocked
            # Material accumulates in buffer
            if self.use_probabilistic:
                accumulation = np.random.normal(
                    self.refill_rate * time_interval_minutes,
                    self.refill_noise_std * np.sqrt(time_interval_minutes)
                )
            else:
                accumulation = self.refill_rate * time_interval_minutes
            
            buffer.add(int(max(0, accumulation)))
            
            if buffer.is_full():
                # Buffer full, upstream blocks
                return (True, 1.0)
            else:
                # Buffer filling but not full yet
                fill_prob = buffer.current_level / buffer.capacity
                return (False, fill_prob * self.cascade_sensitivity)
    
    def simulate_cascade(
        self,
        equipment_sequence: List[str],
        initial_failure: str,
        time_steps: int = 12  # 12 * 5min = 1 hour
    ) -> Dict[str, List[EquipmentStatus]]:
        """Simulate cascade effects over time
        
        Args:
            equipment_sequence: Ordered list of equipment IDs
            initial_failure: Equipment ID that initially fails
            time_steps: Number of 5-minute intervals to simulate
            
        Returns:
            Dictionary of equipment ID to list of statuses over time

        """
        # Initialize
        self.initialize_line(equipment_sequence)
        
        # Set initial failure
        self.equipment_status[initial_failure] = EquipmentStatus.STOPPED
        
        # Track status history
        status_history = {eq_id: [] for eq_id in equipment_sequence}
        
        for step in range(time_steps):
            # Record current status
            for eq_id in equipment_sequence:
                status_history[eq_id].append(self.equipment_status[eq_id])
            
            # Calculate cascade effects
            for i, eq_id in enumerate(equipment_sequence):
                if eq_id == initial_failure:
                    continue  # Keep failed equipment stopped
                
                # Check for starvation (from upstream)
                if i > 0:
                    upstream_id = equipment_sequence[i-1]
                    upstream_status = self.equipment_status[upstream_id]
                    is_starved, _ = self.calculate_starvation(
                        eq_id, upstream_id, upstream_status
                    )
                    if is_starved:
                        self.equipment_status[eq_id] = EquipmentStatus.STARVED
                
                # Check for blockage (from downstream)
                if i < len(equipment_sequence) - 1:
                    downstream_id = equipment_sequence[i+1]
                    downstream_status = self.equipment_status[downstream_id]
                    is_blocked, _ = self.calculate_blockage(
                        eq_id, downstream_id, downstream_status
                    )
                    if is_blocked:
                        self.equipment_status[eq_id] = EquipmentStatus.BLOCKED
        
        return status_history
    
    def get_buffer_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current status of all buffers"""
        status = {}
        for buffer_id, buffer in self.buffers.items():
            status[buffer_id] = {
                "current_level": buffer.current_level,
                "capacity": buffer.capacity,
                "fill_percentage": (buffer.current_level / buffer.capacity) * 100,
                "is_empty": buffer.is_empty(),
                "is_full": buffer.is_full()
            }
        return status
