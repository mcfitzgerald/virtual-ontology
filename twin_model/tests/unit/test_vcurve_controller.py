"""Unit tests for V-Curve Controller."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import simpy

from twin_model.control import VCurveController, VCurveMode, VCurveParameters
from twin_model.primitives import FlowState


class TestVCurveParameters:
    """Test VCurveParameters validation."""

    def test_valid_parameters(self) -> None:
        """Test creation with valid parameters."""
        params = VCurveParameters(
            mode=VCurveMode.FIXED_CONSTRAINT,
            constraint_equipment="LINE1-FIL",
            upstream_differential=0.2,
            downstream_differential=0.15,
            update_interval=5.0,
        )
        assert params.mode == VCurveMode.FIXED_CONSTRAINT
        assert params.constraint_equipment == "LINE1-FIL"
        assert params.upstream_differential == 0.2
        assert params.downstream_differential == 0.15

    def test_invalid_differentials(self) -> None:
        """Test validation of differential values."""
        with pytest.raises(ValueError, match="upstream_differential must be 0-1"):
            VCurveParameters(
                mode=VCurveMode.FIXED_CONSTRAINT,
                constraint_equipment="LINE1-FIL",
                upstream_differential=1.5,  # Invalid
                downstream_differential=0.15,
                update_interval=5.0,
            )

        with pytest.raises(ValueError, match="downstream_differential must be 0-1"):
            VCurveParameters(
                mode=VCurveMode.FIXED_CONSTRAINT,
                constraint_equipment="LINE1-FIL",
                upstream_differential=0.2,
                downstream_differential=-0.1,  # Invalid
                update_interval=5.0,
            )

    def test_invalid_update_interval(self) -> None:
        """Test validation of update interval."""
        with pytest.raises(ValueError, match="update_interval must be positive"):
            VCurveParameters(
                mode=VCurveMode.FIXED_CONSTRAINT,
                constraint_equipment="LINE1-FIL",
                upstream_differential=0.2,
                downstream_differential=0.15,
                update_interval=0,  # Invalid
            )

    def test_fixed_mode_requires_constraint(self) -> None:
        """Test that fixed mode requires constraint equipment."""
        with pytest.raises(ValueError, match="constraint_equipment must be specified"):
            VCurveParameters(
                mode=VCurveMode.FIXED_CONSTRAINT,
                constraint_equipment=None,  # Invalid for fixed mode
                upstream_differential=0.2,
                downstream_differential=0.15,
                update_interval=5.0,
            )


class TestVCurveController:
    """Test VCurveController functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.env = simpy.Environment()

        # Create mock equipment
        self.equipment = {}
        for line in [1, 2]:
            for station in ["FIL", "PCK", "PAL"]:
                equip_id = f"LINE{line}-{station}"
                equipment = Mock()
                equipment.processing = Mock()
                equipment.processing.nominal_rate = 100.0 if station == "FIL" else 110.0
                equipment.current_state = FlowState.FLOWING
                equipment.get_utilization = Mock(return_value=85.0)
                self.equipment[equip_id] = equipment

    def test_controller_creation(self) -> None:
        """Test controller creation with valid parameters."""
        params = VCurveParameters(
            mode=VCurveMode.FIXED_CONSTRAINT,
            constraint_equipment="LINE1-FIL",
            upstream_differential=0.2,
            downstream_differential=0.15,
            update_interval=5.0,
        )

        controller = VCurveController(self.env, self.equipment, params)

        assert controller.constraint_id == "LINE1-FIL"
        assert controller.params.mode == VCurveMode.FIXED_CONSTRAINT
        assert len(controller.original_rates) == 6  # 2 lines × 3 stations

    def test_identify_constraint_lowest_rate(self) -> None:
        """Test constraint identification by lowest rate."""
        # Set LINE1-FIL to have lowest rate
        self.equipment["LINE1-FIL"].processing.nominal_rate = 90.0

        params = VCurveParameters(
            mode=VCurveMode.DYNAMIC_CONSTRAINT,
            constraint_equipment=None,
            upstream_differential=0.2,
            downstream_differential=0.15,
            update_interval=5.0,
        )

        controller = VCurveController(self.env, self.equipment, params)
        controller.identify_constraint()

        assert controller.constraint_id == "LINE1-FIL"

    def test_adjust_speeds_vcurve_pattern(self) -> None:
        """Test that speeds follow V-curve pattern."""
        params = VCurveParameters(
            mode=VCurveMode.FIXED_CONSTRAINT,
            constraint_equipment="LINE1-PCK",  # Middle equipment as constraint
            upstream_differential=0.2,
            downstream_differential=0.1,
            update_interval=5.0,
        )

        controller = VCurveController(self.env, self.equipment, params)
        controller.adjust_speeds()

        # Check V-curve pattern for LINE1
        # FIL (upstream): should be faster
        assert controller.speed_adjustments.get("LINE1-FIL", 1.0) > 1.0
        # PCK (constraint): should be nominal
        assert controller.speed_adjustments.get("LINE1-PCK", 1.0) == 1.0
        # PAL (downstream): should be faster
        assert controller.speed_adjustments.get("LINE1-PAL", 1.0) > 1.0

    def test_speed_adjustment_caps(self) -> None:
        """Test that speed adjustments respect min/max caps."""
        params = VCurveParameters(
            mode=VCurveMode.FIXED_CONSTRAINT,
            constraint_equipment="LINE1-PAL",  # Last equipment as constraint
            upstream_differential=0.5,  # High differential
            downstream_differential=0.3,
            update_interval=5.0,
            max_speed_multiplier=1.3,  # Cap at 1.3x
            min_speed_multiplier=0.9,
        )

        controller = VCurveController(self.env, self.equipment, params)
        controller.adjust_speeds()

        # Check that all adjustments respect caps
        for _equip_id, multiplier in controller.speed_adjustments.items():
            assert 0.9 <= multiplier <= 1.3

    def test_monitor_constraint_health(self) -> None:
        """Test constraint health monitoring."""
        params = VCurveParameters(
            mode=VCurveMode.FIXED_CONSTRAINT,
            constraint_equipment="LINE1-FIL",
            upstream_differential=0.2,
            downstream_differential=0.15,
            update_interval=5.0,
        )

        controller = VCurveController(self.env, self.equipment, params)

        # Simulate constraint starvation
        self.equipment["LINE1-FIL"].current_state = FlowState.STARVED_UPSTREAM
        controller.monitor_constraint_health()

        # Advance time
        self.env.run(until=10)
        controller.last_check_time = 0  # Reset for calculation
        controller.monitor_constraint_health()

        assert controller.constraint_starvation_time > 0

    def test_get_metrics(self) -> None:
        """Test metrics collection."""
        params = VCurveParameters(
            mode=VCurveMode.FIXED_CONSTRAINT,
            constraint_equipment="LINE1-FIL",
            upstream_differential=0.2,
            downstream_differential=0.15,
            update_interval=5.0,
        )

        controller = VCurveController(self.env, self.equipment, params)
        controller.adjust_speeds()

        metrics = controller.get_metrics()

        assert metrics["mode"] == "fixed_constraint"
        assert metrics["constraint_id"] == "LINE1-FIL"
        assert metrics["upstream_differential"] == 0.2
        assert metrics["downstream_differential"] == 0.15
        assert "speed_adjustments" in metrics
        assert "constraint_utilization" in metrics

    def test_reset_speeds(self) -> None:
        """Test resetting speeds to original values."""
        params = VCurveParameters(
            mode=VCurveMode.FIXED_CONSTRAINT,
            constraint_equipment="LINE1-FIL",
            upstream_differential=0.2,
            downstream_differential=0.15,
            update_interval=5.0,
        )

        controller = VCurveController(self.env, self.equipment, params)

        # Store original rates
        original_rates = {}
        for equip_id, equipment in self.equipment.items():
            original_rates[equip_id] = equipment.processing.nominal_rate

        # Adjust speeds
        controller.adjust_speeds()

        # Verify speeds changed
        for equip_id in ["LINE1-FIL", "LINE1-PCK", "LINE1-PAL"]:
            if equip_id != "LINE1-FIL":  # Constraint stays at nominal
                assert self.equipment[equip_id].processing.nominal_rate != original_rates[equip_id]

        # Reset speeds
        controller.reset_speeds()

        # Verify speeds restored
        for equip_id, equipment in self.equipment.items():
            assert equipment.processing.nominal_rate == original_rates[equip_id]

    def test_disabled_mode(self) -> None:
        """Test that disabled mode doesn't start control loop."""
        params = VCurveParameters(
            mode=VCurveMode.DISABLED,
            constraint_equipment=None,
            upstream_differential=0.2,
            downstream_differential=0.15,
            update_interval=5.0,
        )

        controller = VCurveController(self.env, self.equipment, params)
        controller.start()

        assert controller.process is None  # No process started
