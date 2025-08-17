"""
Configuration classes for the SimPy twin model.

Defines configuration structures for equipment, production lines, and simulations.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
from enum import Enum


class EquipmentType(Enum):
    """Types of equipment in production lines."""

    FILLER = "FILLER"
    PACKER = "PACKER"
    PALLETIZER = "PALLETIZER"


@dataclass
class EquipmentConfig:
    """Configuration for a single piece of equipment.

    Attributes:
        equipment_id: Unique identifier for the equipment
        equipment_type: Type of equipment (FILLER, PACKER, PALLETIZER)
        base_rate: Base production rate in units per minute
        mtbf: Mean time between failures in minutes
        mttr: Mean time to repair in minutes
        base_scrap_rate: Base probability of producing scrap (0-1)
        upstream_buffer_capacity: Capacity of upstream buffer
        downstream_buffer_capacity: Capacity of downstream buffer
    """

    equipment_id: str
    equipment_type: EquipmentType
    base_rate: float  # units per minute
    mtbf: float  # minutes
    mttr: float  # minutes
    base_scrap_rate: float = 0.01  # 1% default scrap rate
    upstream_buffer_capacity: int = 100
    downstream_buffer_capacity: int = 100


@dataclass
class LineConfig:
    """Configuration for a production line.

    Attributes:
        line_id: Unique identifier for the line (LINE1, LINE2, LINE3)
        equipment_configs: List of equipment configurations in sequence
        source_arrival_rate: Raw material arrival rate (units per minute)
    """

    line_id: str
    equipment_configs: List[EquipmentConfig]
    source_arrival_rate: float = 100.0  # units per minute


@dataclass
class ActionableParameters:
    """The 5 actionable parameters that can be adjusted.

    Attributes:
        micro_stop_probability: Scales MTBF (higher = more frequent stops)
        performance_factor: Scales production rate (1.0 = normal speed)
        scrap_multiplier: Scales scrap probability (1.0 = normal quality)
        material_reliability: Controls material availability (1.0 = normal)
        cascade_sensitivity: Controls buffer sizes (higher = smaller buffers = tighter coupling)
    """

    micro_stop_probability: float = 1.0
    performance_factor: float = 1.0
    scrap_multiplier: float = 1.0
    material_reliability: float = 1.0
    cascade_sensitivity: float = 1.0


@dataclass
class SimulationConfig:
    """Overall simulation configuration.

    Attributes:
        duration_days: Simulation duration in days
        mes_logging_interval: MES data logging interval in minutes
        line_configs: Configuration for each production line
        parameters: Actionable parameters
        random_seed: Random seed for reproducibility
    """

    duration_days: Union[int, float] = 7
    mes_logging_interval: float = 5.0  # minutes
    line_configs: List[LineConfig] = field(default_factory=list)
    parameters: ActionableParameters = field(default_factory=ActionableParameters)
    random_seed: Optional[int] = None

    @staticmethod
    def create_default_config() -> "SimulationConfig":
        """Create a default configuration with 3 production lines."""
        # LINE1: Base configuration
        line1_equipment = [
            EquipmentConfig(
                equipment_id="LINE1_FILLER",
                equipment_type=EquipmentType.FILLER,
                base_rate=60.0,  # 60 units/min
                mtbf=480.0,  # 8 hours
                mttr=30.0,  # 30 minutes
                downstream_buffer_capacity=200,
            ),
            EquipmentConfig(
                equipment_id="LINE1_PACKER",
                equipment_type=EquipmentType.PACKER,
                base_rate=55.0,  # slightly slower
                mtbf=600.0,  # 10 hours
                mttr=20.0,  # 20 minutes
                upstream_buffer_capacity=200,
                downstream_buffer_capacity=150,
            ),
            EquipmentConfig(
                equipment_id="LINE1_PALLETIZER",
                equipment_type=EquipmentType.PALLETIZER,
                base_rate=50.0,  # slowest (potential bottleneck)
                mtbf=720.0,  # 12 hours
                mttr=15.0,  # 15 minutes
                upstream_buffer_capacity=150,
            ),
        ]

        # LINE2: Faster but less reliable
        line2_equipment = [
            EquipmentConfig(
                equipment_id="LINE2_FILLER",
                equipment_type=EquipmentType.FILLER,
                base_rate=80.0,  # faster
                mtbf=360.0,  # less reliable
                mttr=40.0,
                downstream_buffer_capacity=250,
            ),
            EquipmentConfig(
                equipment_id="LINE2_PACKER",
                equipment_type=EquipmentType.PACKER,
                base_rate=75.0,
                mtbf=420.0,
                mttr=35.0,
                upstream_buffer_capacity=250,
                downstream_buffer_capacity=200,
            ),
            EquipmentConfig(
                equipment_id="LINE2_PALLETIZER",
                equipment_type=EquipmentType.PALLETIZER,
                base_rate=70.0,
                mtbf=500.0,
                mttr=25.0,
                upstream_buffer_capacity=200,
            ),
        ]

        # LINE3: Slower but more reliable
        line3_equipment = [
            EquipmentConfig(
                equipment_id="LINE3_FILLER",
                equipment_type=EquipmentType.FILLER,
                base_rate=45.0,  # slower
                mtbf=960.0,  # very reliable
                mttr=10.0,  # quick repairs
                downstream_buffer_capacity=150,
            ),
            EquipmentConfig(
                equipment_id="LINE3_PACKER",
                equipment_type=EquipmentType.PACKER,
                base_rate=42.0,
                mtbf=1200.0,
                mttr=8.0,
                upstream_buffer_capacity=150,
                downstream_buffer_capacity=120,
            ),
            EquipmentConfig(
                equipment_id="LINE3_PALLETIZER",
                equipment_type=EquipmentType.PALLETIZER,
                base_rate=40.0,
                mtbf=1440.0,  # 24 hours
                mttr=5.0,
                upstream_buffer_capacity=120,
            ),
        ]

        return SimulationConfig(
            line_configs=[
                LineConfig("LINE1", line1_equipment),
                LineConfig("LINE2", line2_equipment),
                LineConfig("LINE3", line3_equipment),
            ]
        )
