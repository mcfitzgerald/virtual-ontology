"""
Line Coupling Model
Explicit cascade model with buffers and stochastic variation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from enum import Enum


class EquipmentStatus(Enum):
    """Equipment operational status"""
    RUNNING = "Running"
    STOPPED = "Stopped"
    STARVED = "Starved"  # No input material
    BLOCKED = "Blocked"  # Output blocked


@dataclass
class Buffer:
    """Material buffer between equipment"""
    capacity: int = 100  # units
    current_level: int = 50  # units
    min_operating_level: int = 10  # Minimum to avoid starvation
    max_operating_level: int = 90  # Maximum before blocking
    
    def is_empty(self) -> bool:
        """Check if buffer is effectively empty"""
        return self.current_level <= self.min_operating_level
    
    def is_full(self) -> bool:
        """Check if buffer is effectively full"""
        return self.current_level >= self.max_operating_level
    
    def add(self, units: int) -> int:
        """
        Add units to buffer
        Returns actual units added (may be less if buffer fills)
        """
        space_available = self.capacity - self.current_level
        units_added = min(units, space_available)
        self.current_level += units_added
        return units_added
    
    def remove(self, units: int) -> int:
        """
        Remove units from buffer
        Returns actual units removed (may be less if buffer empties)
        """
        units_removed = min(units, self.current_level)
        self.current_level -= units_removed
        return units_removed


@dataclass
class LineCoupling:
    """
    Explicit cascade model with buffers and stochastic variation
    Models how upstream stops affect downstream equipment
    """
    # Buffer parameters
    buffer_capacity: int = 100  # units
    initial_buffer_level: int = 50  # units
    
    # Flow rates
    depletion_rate: float = 10.0  # units/min when upstream stopped
    refill_rate: float = 20.0  # units/min when upstream running
    
    # Stochastic parameters
    depletion_noise_std: float = 2.0  # Standard deviation for depletion variation
    refill_noise_std: float = 3.0  # Standard deviation for refill variation
    use_probabilistic: bool = True  # Enable/disable stochastic behavior
    
    # Cascade parameters
    cascade_sensitivity: float = 0.5  # 0=no cascade, 1=immediate cascade
    cascade_delay_minutes: int = 10  # Time before cascade starts
    
    def __init__(self):
        """Initialize line coupling model"""
        self.buffers: Dict[str, Buffer] = {}
        self.equipment_status: Dict[str, EquipmentStatus] = {}
        self.cascade_timers: Dict[str, int] = {}  # Minutes since upstream stop
        
    def initialize_line(self, equipment_ids: List[str]) -> None:
        """
        Initialize a production line with equipment and buffers
        
        Args:
            equipment_ids: List of equipment IDs in order (upstream to downstream)
        """
        # Create buffers between each pair of equipment
        for i in range(len(equipment_ids) - 1):
            buffer_id = f"{equipment_ids[i]}_to_{equipment_ids[i+1]}"
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
        """
        Calculate if downstream equipment starves due to upstream stop
        
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
        """
        Calculate if upstream equipment blocks due to downstream stop
        
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
        """
        Simulate cascade effects over time
        
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


def demonstrate_line_coupling():
    """Demonstrate line coupling and cascade effects"""
    
    print("LINE COUPLING MODEL DEMONSTRATION")
    print("=" * 60)
    
    # Create coupling model with different sensitivities
    scenarios = [
        ("Low Coupling (Good Buffers)", 0.2),
        ("Medium Coupling (Normal Buffers)", 0.5),
        ("High Coupling (Small Buffers)", 0.8)
    ]
    
    equipment_sequence = ["LINE1-FIL", "LINE1-PCK", "LINE1-PAL"]
    
    for scenario_name, sensitivity in scenarios:
        print(f"\n{scenario_name} (Sensitivity: {sensitivity})")
        print("-" * 40)
        
        model = LineCoupling()
        model.cascade_sensitivity = sensitivity
        model.use_probabilistic = False  # Deterministic for demo
        
        # Simulate cascade from filler failure
        history = model.simulate_cascade(
            equipment_sequence,
            initial_failure="LINE1-FIL",
            time_steps=12  # 1 hour
        )
        
        # Show results
        for eq_id in equipment_sequence:
            statuses = history[eq_id]
            status_counts = {}
            for status in statuses:
                status_counts[status.value] = status_counts.get(status.value, 0) + 1
            
            print(f"{eq_id}:")
            for status, count in status_counts.items():
                percentage = (count / len(statuses)) * 100
                print(f"  {status}: {count}/12 intervals ({percentage:.0f}%)")
        
        # Show buffer status at end
        print("\nFinal Buffer Status:")
        buffer_status = model.get_buffer_status()
        for buffer_id, status in buffer_status.items():
            print(f"  {buffer_id}: {status['fill_percentage']:.0f}% full")
    
    # Demonstrate probabilistic behavior
    print("\n" + "=" * 60)
    print("PROBABILISTIC CASCADE SIMULATION")
    print("-" * 40)
    
    model = LineCoupling()
    model.cascade_sensitivity = 0.6
    model.use_probabilistic = True
    
    # Run multiple simulations to show variation
    cascade_counts = {eq: 0 for eq in equipment_sequence}
    n_simulations = 100
    
    for _ in range(n_simulations):
        model.initialize_line(equipment_sequence)
        model.equipment_status["LINE1-FIL"] = EquipmentStatus.STOPPED
        
        # Check cascade after 30 minutes (6 intervals)
        for _ in range(6):
            for i, eq_id in enumerate(equipment_sequence[1:], 1):
                upstream_id = equipment_sequence[i-1]
                upstream_status = model.equipment_status[upstream_id]
                is_starved, _ = model.calculate_starvation(
                    eq_id, upstream_id, upstream_status
                )
                if is_starved:
                    model.equipment_status[eq_id] = EquipmentStatus.STARVED
        
        # Count cascades
        for eq_id in equipment_sequence:
            if model.equipment_status[eq_id] != EquipmentStatus.RUNNING:
                cascade_counts[eq_id] += 1
    
    print(f"Cascade probability after 30 minutes ({n_simulations} simulations):")
    for eq_id in equipment_sequence:
        prob = cascade_counts[eq_id] / n_simulations
        print(f"  {eq_id}: {prob:.2%} probability of being affected")


if __name__ == "__main__":
    demonstrate_line_coupling()