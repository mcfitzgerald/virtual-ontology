"""V-Curve speed controller for Theory of Constraints implementation.

This module implements the V-curve speed control pattern where equipment
speeds increase away from the constraint to protect throughput.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generator, Optional

import simpy

logger = logging.getLogger(__name__)


class VCurveMode(Enum):
    """V-Curve operation modes."""

    FIXED_CONSTRAINT = "fixed_constraint"  # Constraint is manually specified
    DYNAMIC_CONSTRAINT = "dynamic_constraint"  # Constraint is auto-identified
    DISABLED = "disabled"  # V-curve control is disabled


@dataclass
class VCurveParameters:
    """Parameters for V-curve speed control."""

    mode: VCurveMode
    constraint_equipment: Optional[str]  # Equipment ID if fixed mode
    upstream_differential: float  # Speed increase per position upstream (0-1)
    downstream_differential: float  # Speed increase per position downstream (0-1)
    update_interval: float  # How often to adjust speeds (minutes)
    max_speed_multiplier: float = 1.5  # Maximum speed multiplier cap
    min_speed_multiplier: float = 0.8  # Minimum speed multiplier floor

    def __post_init__(self) -> None:
        """Validate V-curve parameters."""
        if self.upstream_differential < 0 or self.upstream_differential > 1:
            raise ValueError(f"upstream_differential must be 0-1, got {self.upstream_differential}")
        if self.downstream_differential < 0 or self.downstream_differential > 1:
            raise ValueError(f"downstream_differential must be 0-1, got {self.downstream_differential}")
        if self.update_interval <= 0:
            raise ValueError(f"update_interval must be positive, got {self.update_interval}")
        if self.max_speed_multiplier < 1:
            raise ValueError(f"max_speed_multiplier must be >= 1, got {self.max_speed_multiplier}")
        if self.min_speed_multiplier > 1:
            raise ValueError(f"min_speed_multiplier must be <= 1, got {self.min_speed_multiplier}")
        if self.mode == VCurveMode.FIXED_CONSTRAINT and not self.constraint_equipment:
            raise ValueError("constraint_equipment must be specified for FIXED_CONSTRAINT mode")


class VCurveController:
    """Controls equipment speeds based on V-curve theory.

    The V-curve pattern sets equipment speeds to increase away from the
    constraint (bottleneck) to ensure the constraint is never starved
    and downstream equipment can absorb variations.
    """

    def __init__(
        self,
        env: simpy.Environment,
        equipment_dict: dict[str, Any],
        vcurve_params: VCurveParameters,
    ) -> None:
        """Initialize V-curve controller.

        Args:
            env: SimPy environment
            equipment_dict: Dictionary of equipment ID -> equipment object
            vcurve_params: V-curve control parameters
        """
        self.env = env
        self.equipment = equipment_dict
        self.params = vcurve_params

        # State tracking
        self.constraint_id: Optional[str] = vcurve_params.constraint_equipment
        self.constraint_changes = 0
        self.last_constraint_id: Optional[str] = None
        self.speed_adjustments: dict[str, float] = {}  # Equipment ID -> speed multiplier
        self.original_rates: dict[str, float] = {}  # Store original nominal rates

        # Metrics
        self.constraint_starvation_time = 0.0
        self.constraint_blocking_time = 0.0
        self.last_check_time = 0.0

        # Process handle
        self.process: Optional[simpy.Process] = None

        # Store original rates
        self._store_original_rates()

        logger.info(
            f"Initialized V-curve controller: mode={vcurve_params.mode.value}, "
            f"constraint={self.constraint_id}, "
            f"differentials={vcurve_params.upstream_differential:.2f}/{vcurve_params.downstream_differential:.2f}"
        )

    def _store_original_rates(self) -> None:
        """Store original equipment nominal rates."""
        for equip_id, equipment in self.equipment.items():
            if hasattr(equipment, "processing") and hasattr(equipment.processing, "nominal_rate"):
                self.original_rates[equip_id] = equipment.processing.nominal_rate
                logger.debug(f"Stored original rate for {equip_id}: {self.original_rates[equip_id]:.1f}")

    def start(self) -> None:
        """Start the V-curve control process."""
        if self.params.mode != VCurveMode.DISABLED and self.process is None:
            self.process = self.env.process(self.control_loop())
            logger.info("V-curve controller started")

    def control_loop(self) -> Generator[simpy.Event, None, None]:
        """Main control loop for V-curve adjustments."""
        logger.info("V-curve control loop starting")

        while True:
            try:
                # Identify constraint if in dynamic mode
                if self.params.mode == VCurveMode.DYNAMIC_CONSTRAINT:
                    self.identify_constraint()

                # Adjust speeds based on V-curve
                if self.constraint_id:
                    self.adjust_speeds()
                    self.monitor_constraint_health()

                # Wait for next update
                yield self.env.timeout(self.params.update_interval)

            except simpy.Interrupt:
                logger.info("V-curve control loop interrupted")
                break
            except Exception as e:
                logger.error(f"V-curve control error: {e}")
                yield self.env.timeout(self.params.update_interval)

    def identify_constraint(self) -> None:
        """Identify the constraint (bottleneck) equipment.

        The constraint is typically the equipment with:
        1. Lowest nominal rate (design constraint)
        2. Highest utilization (actual constraint)
        3. Most downstream starvation impact
        """
        if not self.equipment:
            return

        # Method 1: Find equipment with lowest nominal rate
        min_rate = float("inf")
        constraint_candidate = None

        for equip_id, equipment in self.equipment.items():
            # Skip sources and sinks
            if "SOURCE" in equip_id or "SINK" in equip_id:
                continue

            if hasattr(equipment, "processing") and hasattr(equipment.processing, "nominal_rate"):
                rate = self.original_rates.get(equip_id, equipment.processing.nominal_rate)
                if rate < min_rate:
                    min_rate = rate
                    constraint_candidate = equip_id

        # Method 2: Check utilization (if available)
        if constraint_candidate:
            # Could enhance with utilization-based identification
            max_utilization = 0
            for equip_id, equipment in self.equipment.items():
                if "SOURCE" in equip_id or "SINK" in equip_id:
                    continue
                if hasattr(equipment, "get_utilization"):
                    utilization = equipment.get_utilization()
                    if utilization > max_utilization:
                        max_utilization = utilization
                        # Only override if utilization is significantly higher
                        if utilization > 95 and utilization > max_utilization + 10:
                            constraint_candidate = equip_id

        # Update constraint if changed
        if constraint_candidate != self.constraint_id:
            self.last_constraint_id = self.constraint_id
            self.constraint_id = constraint_candidate
            self.constraint_changes += 1
            logger.info(
                f"Constraint changed: {self.last_constraint_id} -> {self.constraint_id} "
                f"(rate: {min_rate:.1f}, change #{self.constraint_changes})"
            )

    def adjust_speeds(self) -> None:
        """Adjust equipment speeds according to V-curve pattern.

        The constraint runs at nominal speed, equipment upstream runs faster
        to prevent starvation, and equipment downstream runs faster to
        prevent blocking.
        """
        if not self.constraint_id or self.constraint_id not in self.equipment:
            logger.warning(f"Cannot adjust speeds: invalid constraint {self.constraint_id}")
            return

        # Get line topology
        line_equipment = self._get_line_equipment(self.constraint_id)
        if not line_equipment:
            logger.warning(f"Cannot determine line topology for constraint {self.constraint_id}")
            return

        # Find constraint position
        constraint_pos = -1
        for i, equip_id in enumerate(line_equipment):
            if equip_id == self.constraint_id:
                constraint_pos = i
                break

        if constraint_pos < 0:
            return

        logger.debug(f"Adjusting speeds for line with constraint at position {constraint_pos}: {line_equipment}")

        # Apply V-curve speed adjustments
        for i, equip_id in enumerate(line_equipment):
            if equip_id not in self.equipment:
                continue

            equipment = self.equipment[equip_id]

            # Skip if equipment doesn't have processing parameters
            if not hasattr(equipment, "processing"):
                continue

            # Calculate speed multiplier based on position relative to constraint
            if i == constraint_pos:
                # Constraint runs at nominal speed
                multiplier = 1.0
            elif i < constraint_pos:
                # Upstream: increase speed to prevent starvation
                distance = constraint_pos - i
                multiplier = 1.0 + (self.params.upstream_differential * distance)
            else:
                # Downstream: increase speed to prevent blocking
                distance = i - constraint_pos
                multiplier = 1.0 + (self.params.downstream_differential * distance)

            # Apply caps
            multiplier = max(self.params.min_speed_multiplier, min(self.params.max_speed_multiplier, multiplier))

            # Apply speed adjustment
            original_rate = self.original_rates.get(equip_id, equipment.processing.nominal_rate)
            new_rate = original_rate * multiplier

            # Update equipment rate
            if hasattr(equipment.processing, "nominal_rate"):
                old_rate = equipment.processing.nominal_rate
                equipment.processing.nominal_rate = new_rate
                self.speed_adjustments[equip_id] = multiplier

                if abs(old_rate - new_rate) > 0.1:  # Only log significant changes
                    logger.info(
                        f"Adjusted {equip_id} speed: {old_rate:.1f} -> {new_rate:.1f} "
                        f"(multiplier: {multiplier:.2f}, position: {i})"
                    )

    def _get_line_equipment(self, equipment_id: str) -> list[str]:
        """Get ordered list of equipment in the same line.

        Args:
            equipment_id: Equipment ID to find line for

        Returns:
            Ordered list of equipment IDs in the line
        """
        # Extract line ID (e.g., "LINE1" from "LINE1-FIL")
        if "-" in equipment_id:
            line_id = equipment_id.split("-")[0]
        else:
            return []

        # Get all equipment in this line
        line_equipment = []
        for equip_id in self.equipment.keys():
            if equip_id.startswith(line_id):
                line_equipment.append(equip_id)

        # Sort by typical production flow order
        # SOURCE -> FIL -> PCK -> PAL -> SINK
        order_map = {
            "SOURCE": 0,
            "FIL": 1,
            "PCK": 2,
            "PAL": 3,
            "SINK": 4,
        }

        def get_order(equip_id: str) -> int:
            for key, order in order_map.items():
                if key in equip_id:
                    return order
            return 99

        line_equipment.sort(key=get_order)

        # Filter out sources and sinks for speed adjustment
        line_equipment = [eid for eid in line_equipment if "SOURCE" not in eid and "SINK" not in eid]

        return line_equipment

    def monitor_constraint_health(self) -> None:
        """Monitor constraint starvation and blocking."""
        if not self.constraint_id or self.constraint_id not in self.equipment:
            return

        constraint = self.equipment[self.constraint_id]

        # Check for starvation (input buffer empty)
        if hasattr(constraint, "current_state"):
            from ..primitives import FlowState

            time_delta = self.env.now - self.last_check_time

            if constraint.current_state == FlowState.STARVED_UPSTREAM:
                self.constraint_starvation_time += time_delta
                logger.warning(
                    f"Constraint {self.constraint_id} starved! "
                    f"Total starvation: {self.constraint_starvation_time:.1f} min"
                )
            elif constraint.current_state == FlowState.BLOCKED_DOWNSTREAM:
                self.constraint_blocking_time += time_delta
                logger.warning(
                    f"Constraint {self.constraint_id} blocked! "
                    f"Total blocking: {self.constraint_blocking_time:.1f} min"
                )

            self.last_check_time = self.env.now

    def get_metrics(self) -> dict[str, Any]:
        """Get V-curve controller metrics.

        Returns:
            Dictionary of controller metrics
        """
        total_time = self.env.now if self.env.now > 0 else 1.0

        metrics = {
            "mode": self.params.mode.value,
            "constraint_id": self.constraint_id,
            "constraint_changes": self.constraint_changes,
            "upstream_differential": self.params.upstream_differential,
            "downstream_differential": self.params.downstream_differential,
            "constraint_starvation_rate": self.constraint_starvation_time / total_time,
            "constraint_blocking_rate": self.constraint_blocking_time / total_time,
            "speed_adjustments": dict(self.speed_adjustments),
        }

        # Add constraint health status
        if self.constraint_id and self.constraint_id in self.equipment:
            constraint = self.equipment[self.constraint_id]
            if hasattr(constraint, "get_utilization"):
                metrics["constraint_utilization"] = constraint.get_utilization()
            if hasattr(constraint, "current_state"):
                metrics["constraint_state"] = str(constraint.current_state)

        return metrics

    def reset_speeds(self) -> None:
        """Reset all equipment to original speeds."""
        for equip_id, original_rate in self.original_rates.items():
            if equip_id in self.equipment:
                equipment = self.equipment[equip_id]
                if hasattr(equipment, "processing") and hasattr(equipment.processing, "nominal_rate"):
                    equipment.processing.nominal_rate = original_rate
                    logger.info(f"Reset {equip_id} to original rate: {original_rate:.1f}")

        self.speed_adjustments.clear()
        logger.info("All equipment speeds reset to original values")
