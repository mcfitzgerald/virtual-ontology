"""
Production line implementation combining equipment and buffers.

Models a complete production line with material flow from source to sink.
"""

import simpy
import random
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

from .equipment import Equipment
from .buffer import Buffer
from .config import LineConfig, ActionableParameters


@dataclass
class LineStats:
    """Statistics for the entire production line.

    Attributes:
        total_input: Total units entered the line
        total_output: Total units completed
        total_scrap: Total units scrapped
        bottleneck_equipment: ID of bottleneck equipment
        line_efficiency: Overall line efficiency
    """

    total_input: int = 0
    total_output: int = 0
    total_scrap: int = 0
    bottleneck_equipment: Optional[str] = None
    line_efficiency: float = 0.0


class MaterialSource:
    """Source of raw materials for the production line."""

    def __init__(
        self,
        env: simpy.Environment,
        line_id: str,
        arrival_rate: float,
        parameters: ActionableParameters,
        first_buffer: Buffer,
    ):
        """Initialize material source.

        Args:
            env: SimPy environment
            line_id: Line identifier
            arrival_rate: Base arrival rate (units per minute)
            parameters: Actionable parameters
            first_buffer: Buffer to put materials into
        """
        self.env = env
        self.line_id = line_id
        self.base_arrival_rate = arrival_rate
        self.parameters = parameters
        self.first_buffer = first_buffer
        self.units_generated = 0

        # Start material generation process
        self.process = env.process(self._generate_materials())

    def _generate_materials(self) -> Generator[simpy.Event, None, None]:
        """Generate materials based on arrival rate and reliability."""
        while True:
            # Adjust arrival rate based on material_reliability
            # Lower reliability = less frequent arrivals
            adjusted_rate = (
                self.base_arrival_rate * self.parameters.material_reliability
            )

            if adjusted_rate > 0:
                # Time between arrivals (exponential distribution)
                # Rate is in units per minute, so interarrival time is 1/rate minutes
                interarrival_time = random.expovariate(adjusted_rate)
                yield self.env.timeout(interarrival_time)

                # Random material shortages
                if (
                    random.random()
                    < (1.0 - self.parameters.material_reliability) * 0.05
                ):
                    # Material shortage event (5% chance when reliability < 1.0)
                    shortage_duration = random.uniform(5, 30)  # 5-30 minutes
                    yield self.env.timeout(shortage_duration)
                else:
                    # Put material into first buffer (wait if full)
                    yield self.first_buffer.put(1)
                    self.units_generated += 1
            else:
                # No material flow
                yield self.env.timeout(60)  # Check again in 1 minute


class ProductSink:
    """Sink for finished products."""

    def __init__(self, env: simpy.Environment, line_id: str, last_buffer: Buffer):
        """Initialize product sink.

        Args:
            env: SimPy environment
            line_id: Line identifier
            last_buffer: Buffer to get products from
        """
        self.env = env
        self.line_id = line_id
        self.last_buffer = last_buffer
        self.units_collected = 0

        # Start collection process
        self.process = env.process(self._collect_products())

    def _collect_products(self) -> Generator[simpy.Event, None, None]:
        """Collect finished products from last buffer."""
        while True:
            if not self.last_buffer.is_empty():
                yield self.last_buffer.get(1)
                self.units_collected += 1
            else:
                # Wait a bit before checking again
                yield self.env.timeout(0.1)


class ProductionLine:
    """Complete production line with equipment, buffers, source, and sink."""

    def __init__(
        self,
        env: simpy.Environment,
        config: LineConfig,
        parameters: ActionableParameters,
    ):
        """Initialize production line.

        Args:
            env: SimPy environment
            config: Line configuration
            parameters: Actionable parameters
        """
        self.env = env
        self.config = config
        self.parameters = parameters
        self.line_id = config.line_id

        # Create buffers based on cascade_sensitivity
        self.buffers: List[Buffer] = []
        self.equipment: List[Equipment] = []

        # Build the production line
        self._build_line()

        # Statistics
        self.stats = LineStats()

        # MES logging
        self.mes_data: List[Dict[str, Any]] = []

    def _calculate_buffer_capacity(self, base_capacity: int) -> int:
        """Calculate adjusted buffer capacity based on cascade_sensitivity.

        Args:
            base_capacity: Base buffer capacity from config

        Returns:
            Adjusted capacity
        """
        # Higher cascade_sensitivity = smaller buffers = tighter coupling
        # cascade_sensitivity = 2.0 → buffers are half size
        # cascade_sensitivity = 0.5 → buffers are double size
        adjusted = int(base_capacity / self.parameters.cascade_sensitivity)
        return max(adjusted, 10)  # Minimum buffer size of 10

    def _build_line(self) -> None:
        """Build the production line from configuration."""
        # Create buffers between equipment
        for i in range(len(self.config.equipment_configs) + 1):
            if i == 0:
                # First buffer (before first equipment)
                buffer_id = f"{self.line_id}_BUFFER_IN"
                capacity = self._calculate_buffer_capacity(
                    self.config.equipment_configs[0].upstream_buffer_capacity
                )
            elif i == len(self.config.equipment_configs):
                # Last buffer (after last equipment)
                buffer_id = f"{self.line_id}_BUFFER_OUT"
                capacity = self._calculate_buffer_capacity(
                    self.config.equipment_configs[-1].downstream_buffer_capacity
                )
            else:
                # Intermediate buffer
                buffer_id = f"{self.line_id}_BUFFER_{i}"
                # Use downstream capacity of previous equipment
                capacity = self._calculate_buffer_capacity(
                    self.config.equipment_configs[i - 1].downstream_buffer_capacity
                )

            buffer = Buffer(self.env, buffer_id, capacity)
            self.buffers.append(buffer)

        # Create equipment
        for i, eq_config in enumerate(self.config.equipment_configs):
            upstream_buffer = self.buffers[i]
            downstream_buffer = self.buffers[i + 1]

            equipment = Equipment(
                env=self.env,
                config=eq_config,
                parameters=self.parameters,
                upstream_buffer=upstream_buffer,
                downstream_buffer=downstream_buffer,
            )
            self.equipment.append(equipment)

        # Create source and sink
        self.source = MaterialSource(
            env=self.env,
            line_id=self.line_id,
            arrival_rate=self.config.source_arrival_rate,
            parameters=self.parameters,
            first_buffer=self.buffers[0],
        )

        self.sink = ProductSink(
            env=self.env, line_id=self.line_id, last_buffer=self.buffers[-1]
        )

    def identify_bottleneck(self) -> Optional[str]:
        """Identify the bottleneck equipment.

        Returns:
            Equipment ID of the bottleneck, or None
        """
        min_oee = 100.0
        bottleneck_id = None

        for eq in self.equipment:
            oee_metrics = eq.get_oee_metrics()
            if oee_metrics["oee"] < min_oee:
                min_oee = oee_metrics["oee"]
                bottleneck_id = eq.config.equipment_id

        return bottleneck_id

    def get_line_oee(self) -> Dict[str, float]:
        """Calculate overall line OEE.

        Returns:
            Dictionary with line-level OEE metrics
        """
        if not self.equipment:
            return {"availability": 0.0, "performance": 0.0, "quality": 0.0, "oee": 0.0}

        # Line OEE is typically the minimum of equipment OEEs
        # (weakest link determines line performance)
        min_oee = 100.0
        min_availability = 100.0
        min_performance = 100.0
        avg_quality = 0.0

        for eq in self.equipment:
            metrics = eq.get_oee_metrics()
            min_oee = min(min_oee, metrics["oee"])
            min_availability = min(min_availability, metrics["availability"])
            min_performance = min(min_performance, metrics["performance"])
            avg_quality += metrics["quality"]

        avg_quality /= len(self.equipment)

        return {
            "availability": min_availability,
            "performance": min_performance,
            "quality": avg_quality,
            "oee": min_oee,
        }

    def capture_mes_snapshot(self) -> Dict[str, Any]:
        """Capture current state for MES logging.

        Returns:
            Dictionary with line state snapshot
        """
        snapshot: Dict[str, Any] = {
            "timestamp": self.env.now,
            "line_id": self.line_id,
            "line_oee": self.get_line_oee(),
            "bottleneck": self.identify_bottleneck(),
            "source_units": self.source.units_generated,
            "sink_units": self.sink.units_collected,
            "equipment_states": {},
            "buffer_levels": {},
        }

        # Add equipment states
        for eq in self.equipment:
            snapshot["equipment_states"][eq.config.equipment_id] = {
                "state": eq.state.value,
                "units_produced": eq.stats.units_produced,
                "units_scrapped": eq.stats.units_scrapped,
                "oee": eq.get_oee_metrics()["oee"],
            }

        # Add buffer levels
        for buffer in self.buffers:
            snapshot["buffer_levels"][buffer.buffer_id] = {
                "level": buffer.level,
                "capacity": buffer.capacity,
                "utilization": buffer.utilization,
            }

        return snapshot

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get comprehensive line statistics.

        Returns:
            Dictionary with all line statistics
        """
        self.stats.total_input = self.source.units_generated
        self.stats.total_output = self.sink.units_collected
        self.stats.total_scrap = sum(eq.stats.units_scrapped for eq in self.equipment)
        self.stats.bottleneck_equipment = self.identify_bottleneck()

        if self.stats.total_input > 0:
            self.stats.line_efficiency = (
                self.stats.total_output / self.stats.total_input
            ) * 100

        return {
            "line_id": self.line_id,
            "total_input": self.stats.total_input,
            "total_output": self.stats.total_output,
            "total_scrap": self.stats.total_scrap,
            "line_efficiency": self.stats.line_efficiency,
            "bottleneck": self.stats.bottleneck_equipment,
            "line_oee": self.get_line_oee(),
            "equipment_stats": [eq.get_stats_summary() for eq in self.equipment],
            "buffer_stats": [buffer.get_stats_summary() for buffer in self.buffers],
        }
