"""Unit tests for AccumulationBuffer primitive."""

from __future__ import annotations

import pytest
import simpy

from twin_model.primitives import (
    AccumulationBuffer,
    BufferMode,
    BufferParameters,
    FlowCapacity,
    FlowState,
)


class TestAccumulationBuffer:
    """Test AccumulationBuffer functionality."""

    def test_buffer_creation(self) -> None:
        """Test buffer creation with valid parameters."""
        env = simpy.Environment()

        flow_capacity = FlowCapacity(
            max_input_rate=100.0,
            max_output_rate=100.0,
            internal_capacity=500.0,
            initial_level=0.0,
        )

        buffer_params = BufferParameters(
            mode=BufferMode.FIFO,
            warning_level_low=0.2,
            warning_level_high=0.8,
            max_dwell_time=180.0,
            update_interval=0.01,
        )

        config = {"id": "TEST-BUFFER-1"}

        buffer = AccumulationBuffer(env, config, flow_capacity, buffer_params)

        assert buffer is not None
        assert buffer.buffer.capacity == 500.0
        assert buffer.buffer.level == 0.0
        assert buffer.buffer_params.mode == BufferMode.FIFO

    def test_buffer_parameter_validation(self) -> None:
        """Test buffer parameter validation."""
        # Test invalid warning levels
        with pytest.raises(ValueError, match="warning_level_low must be between"):
            BufferParameters(
                mode=BufferMode.FIFO,
                warning_level_low=-0.1,
                warning_level_high=0.8,
                max_dwell_time=180.0,
            )

        with pytest.raises(ValueError, match="warning_level_high must be between"):
            BufferParameters(
                mode=BufferMode.FIFO,
                warning_level_low=0.2,
                warning_level_high=1.5,
                max_dwell_time=180.0,
            )

        # Test invalid warning level relationship
        with pytest.raises(ValueError, match="warning_level_low must be less than"):
            BufferParameters(
                mode=BufferMode.FIFO,
                warning_level_low=0.8,
                warning_level_high=0.2,
                max_dwell_time=180.0,
            )

        # Test invalid dwell time
        with pytest.raises(ValueError, match="max_dwell_time must be positive"):
            BufferParameters(
                mode=BufferMode.FIFO,
                warning_level_low=0.2,
                warning_level_high=0.8,
                max_dwell_time=-1.0,
            )

    def test_buffer_overflow_detection(self) -> None:
        """Test buffer overflow detection."""
        env = simpy.Environment()

        flow_capacity = FlowCapacity(
            max_input_rate=100.0,
            max_output_rate=100.0,
            internal_capacity=100.0,  # Small capacity for testing
            initial_level=100.0,  # Start full
        )

        buffer_params = BufferParameters(
            mode=BufferMode.FIFO,
            warning_level_low=0.2,
            warning_level_high=0.8,
            max_dwell_time=180.0,
            update_interval=0.01,
        )

        config = {"id": "TEST-BUFFER-OVERFLOW"}

        buffer = AccumulationBuffer(env, config, flow_capacity, buffer_params)

        # Check overflow detection
        buffer._check_overflow_underflow(100.0, 100.0)
        assert buffer.is_overflow is True
        assert buffer.overflow_events == 1

    def test_buffer_underflow_detection(self) -> None:
        """Test buffer underflow detection."""
        env = simpy.Environment()

        flow_capacity = FlowCapacity(
            max_input_rate=100.0,
            max_output_rate=100.0,
            internal_capacity=100.0,
            initial_level=0.0,  # Start empty
        )

        buffer_params = BufferParameters(
            mode=BufferMode.FIFO,
            warning_level_low=0.2,
            warning_level_high=0.8,
            max_dwell_time=180.0,
            update_interval=0.01,
        )

        config = {"id": "TEST-BUFFER-UNDERFLOW"}

        buffer = AccumulationBuffer(env, config, flow_capacity, buffer_params)

        # Check underflow detection
        buffer._check_overflow_underflow(0.0, 100.0)
        assert buffer.is_underflow is True
        assert buffer.underflow_events == 1

    def test_buffer_warning_levels(self) -> None:
        """Test buffer warning level detection."""
        env = simpy.Environment()

        flow_capacity = FlowCapacity(
            max_input_rate=100.0,
            max_output_rate=100.0,
            internal_capacity=100.0,
            initial_level=50.0,
        )

        buffer_params = BufferParameters(
            mode=BufferMode.FIFO,
            warning_level_low=0.2,  # 20 units
            warning_level_high=0.8,  # 80 units
            max_dwell_time=180.0,
            update_interval=0.01,
        )

        config = {"id": "TEST-BUFFER-WARNINGS"}

        buffer = AccumulationBuffer(env, config, flow_capacity, buffer_params)

        # Test low warning
        buffer._check_warning_levels(0.15)  # 15% fill
        assert buffer.is_warning_low is True
        assert buffer.warning_events["low"] == 1

        # Reset and test high warning
        buffer.is_warning_low = False
        buffer._check_warning_levels(0.85)  # 85% fill
        assert buffer.is_warning_high is True
        assert buffer.warning_events["high"] == 1

    def test_buffer_metrics(self) -> None:
        """Test buffer metrics collection."""
        env = simpy.Environment()

        flow_capacity = FlowCapacity(
            max_input_rate=100.0,
            max_output_rate=100.0,
            internal_capacity=500.0,
            initial_level=250.0,  # 50% full
        )

        buffer_params = BufferParameters(
            mode=BufferMode.FIFO,
            warning_level_low=0.2,
            warning_level_high=0.8,
            max_dwell_time=180.0,
            update_interval=0.01,
        )

        config = {"id": "TEST-BUFFER-METRICS"}

        buffer = AccumulationBuffer(env, config, flow_capacity, buffer_params)

        # Set some test values
        buffer.overflow_events = 2
        buffer.underflow_events = 3
        buffer.warning_events["low"] = 4
        buffer.warning_events["high"] = 5

        metrics = buffer.get_metrics()

        assert metrics["buffer_level"] == 250.0
        assert metrics["fill_percentage"] == 0.5
        assert metrics["overflow_events"] == 2
        assert metrics["underflow_events"] == 3
        assert metrics["warning_events_low"] == 4
        assert metrics["warning_events_high"] == 5
        assert metrics["mode"] == "fifo"

    def test_buffer_state_transitions(self) -> None:
        """Test buffer state transitions based on conditions."""
        env = simpy.Environment()

        flow_capacity = FlowCapacity(
            max_input_rate=100.0,
            max_output_rate=100.0,
            internal_capacity=100.0,
            initial_level=0.0,
        )

        buffer_params = BufferParameters(
            mode=BufferMode.FIFO,
            warning_level_low=0.2,
            warning_level_high=0.8,
            max_dwell_time=180.0,
            update_interval=0.01,
        )

        config = {"id": "TEST-BUFFER-STATES"}

        buffer = AccumulationBuffer(env, config, flow_capacity, buffer_params)

        # Initially should be IDLE
        assert buffer.current_state == FlowState.IDLE

        # Test state change
        buffer.change_state(FlowState.FLOWING, "Material flowing")
        assert buffer.current_state == FlowState.FLOWING

        buffer.change_state(FlowState.STARVED_UPSTREAM, "No input available")
        assert buffer.current_state == FlowState.STARVED_UPSTREAM

        buffer.change_state(FlowState.BLOCKED_DOWNSTREAM, "Downstream blocked")
        assert buffer.current_state == FlowState.BLOCKED_DOWNSTREAM
