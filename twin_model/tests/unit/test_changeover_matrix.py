"""Unit tests for ChangeoverMatrix functionality in EquipmentFlow."""

from __future__ import annotations

import pytest
import simpy

from twin_model.primitives import (
    ChangeoverMatrix,
    EquipmentFlow,
    FailureParameters,
    FlowCapacity,
    FlowState,
    ProcessingParameters,
)


class TestChangeoverMatrix:
    """Test ChangeoverMatrix class."""

    def test_valid_matrix_creation(self) -> None:
        """Test creation of valid changeover matrix."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 15.0, "product_c": 30.0},
                "product_b": {"product_a": 15.0, "product_c": 20.0},
            },
            default_time=25.0,
            min_changeover_time=5.0,
        )

        assert matrix.default_time == 25.0
        assert matrix.min_changeover_time == 5.0
        assert matrix.track_patterns is True

    def test_negative_time_validation(self) -> None:
        """Test that negative times are rejected."""
        with pytest.raises(ValueError, match="default_time cannot be negative"):
            ChangeoverMatrix(
                matrix={},
                default_time=-10.0,
            )

        with pytest.raises(ValueError, match="min_changeover_time cannot be negative"):
            ChangeoverMatrix(
                matrix={},
                default_time=20.0,
                min_changeover_time=-5.0,
            )

        with pytest.raises(ValueError, match="Changeover time cannot be negative"):
            ChangeoverMatrix(
                matrix={
                    "product_a": {"product_b": -15.0},
                },
                default_time=20.0,
            )

    def test_get_changeover_time_same_product(self) -> None:
        """Test that same product returns zero changeover time."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 15.0},
            },
            default_time=25.0,
        )

        assert matrix.get_changeover_time("product_a", "product_a") == 0.0
        assert matrix.get_changeover_time("product_b", "product_b") == 0.0

    def test_get_changeover_time_defined(self) -> None:
        """Test getting defined changeover times."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 15.0, "product_c": 30.0},
                "product_b": {"product_a": 20.0},
            },
            default_time=25.0,
            min_changeover_time=5.0,
        )

        # Defined times
        assert matrix.get_changeover_time("product_a", "product_b") == 15.0
        assert matrix.get_changeover_time("product_a", "product_c") == 30.0
        assert matrix.get_changeover_time("product_b", "product_a") == 20.0

    def test_get_changeover_time_default(self) -> None:
        """Test getting default time for undefined pairs."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 15.0},
            },
            default_time=25.0,
            min_changeover_time=5.0,
        )

        # Undefined pairs use default
        assert matrix.get_changeover_time("product_a", "product_c") == 25.0
        assert matrix.get_changeover_time("product_c", "product_d") == 25.0

    def test_minimum_time_constraint(self) -> None:
        """Test that minimum time constraint is applied."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 3.0},  # Below minimum
            },
            default_time=2.0,  # Also below minimum
            min_changeover_time=10.0,
        )

        # Should return minimum time
        assert matrix.get_changeover_time("product_a", "product_b") == 10.0
        assert matrix.get_changeover_time("product_c", "product_d") == 10.0


class TestEquipmentFlowChangeover:
    """Test EquipmentFlow changeover functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.env = simpy.Environment()
        self.config = {
            "name": "TEST-EQUIP",
            "default_product": "product_a",
        }
        self.flow_capacity = FlowCapacity(
            max_input_rate=200.0,
            max_output_rate=200.0,
            internal_capacity=100.0,
        )
        self.processing = ProcessingParameters(
            nominal_rate=100.0,
            quality_rate=0.95,
            performance_factor=0.9,
            processing_interval=1.0,
        )
        self.failures = FailureParameters(
            mtbf=1000.0,
            mttr=10.0,
            micro_stop_rate=0.0,
            micro_stop_duration=0.0,
        )

    def test_equipment_with_changeover_matrix(self) -> None:
        """Test equipment creation with changeover matrix."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 15.0},
            },
            default_time=20.0,
        )

        equipment = EquipmentFlow(
            self.env,
            self.config,
            self.flow_capacity,
            self.processing,
            self.failures,
            changeover_matrix=matrix,
        )

        assert equipment.changeover_matrix == matrix
        assert equipment.current_product == "product_a"
        assert equipment.next_product is None
        assert equipment.changeover_count == 0
        assert equipment.total_changeover_time == 0.0

    def test_request_product_change(self) -> None:
        """Test requesting a product change."""
        equipment = EquipmentFlow(
            self.env,
            self.config,
            self.flow_capacity,
            self.processing,
            self.failures,
        )

        equipment.request_product_change("product_b")

        assert equipment.next_product == "product_b"
        assert equipment.current_product == "product_a"  # Not changed yet

    def test_handle_product_change_with_matrix(self) -> None:
        """Test product change handling with matrix."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 15.0},
            },
            default_time=20.0,
        )

        equipment = EquipmentFlow(
            self.env,
            self.config,
            self.flow_capacity,
            self.processing,
            self.failures,
            changeover_matrix=matrix,
        )

        # Request change
        equipment.request_product_change("product_b")

        # Run the change process
        def test_process():
            yield self.env.process(equipment.handle_product_change("product_b"))

        self.env.process(test_process())
        self.env.run(until=20)

        # Check results
        assert equipment.current_product == "product_b"
        assert equipment.changeover_count == 1
        assert equipment.total_changeover_time == 15.0

    def test_handle_product_change_without_matrix(self) -> None:
        """Test product change uses default time without matrix."""
        equipment = EquipmentFlow(
            self.env,
            self.config,
            self.flow_capacity,
            self.processing,
            self.failures,
            changeover_matrix=None,
        )

        # Run the change process
        def test_process():
            yield self.env.process(equipment.handle_product_change("product_b"))

        self.env.process(test_process())
        self.env.run(until=35)

        # Should use default 30.0 minutes
        assert equipment.current_product == "product_b"
        assert equipment.changeover_count == 1
        assert equipment.total_changeover_time == 30.0

    def test_changeover_state_tracking(self) -> None:
        """Test that changeover state is properly tracked."""
        equipment = EquipmentFlow(
            self.env,
            self.config,
            self.flow_capacity,
            self.processing,
            self.failures,
        )

        # Track state changes
        states = []

        def track_state():
            initial_state = equipment.current_state
            states.append(initial_state)

            # Start changeover
            yield self.env.process(equipment.changeover("product_b", 10.0))

            # State should change back after changeover
            states.append(equipment.current_state)

        self.env.process(track_state())

        # Check initial state
        assert not equipment.is_changing_over

        # Run for a bit to enter changeover
        self.env.run(until=5)
        assert equipment.is_changing_over
        assert equipment.current_state == FlowState.CHANGEOVER

        # Complete changeover
        self.env.run(until=15)
        assert not equipment.is_changing_over
        assert equipment.current_product == "product_b"

    def test_changeover_history_tracking(self) -> None:
        """Test that changeover history is tracked."""
        equipment = EquipmentFlow(
            self.env,
            self.config,
            self.flow_capacity,
            self.processing,
            self.failures,
        )

        # Perform multiple changeovers
        def test_process():
            yield self.env.process(equipment.changeover("product_b", 10.0))
            yield self.env.timeout(5)
            yield self.env.process(equipment.changeover("product_c", 15.0))
            yield self.env.timeout(5)
            yield self.env.process(equipment.changeover("product_a", 20.0))

        self.env.process(test_process())
        self.env.run(until=60)

        # Check history
        assert len(equipment.changeover_history) == 3
        assert equipment.changeover_count == 3
        assert equipment.total_changeover_time == 45.0  # 10 + 15 + 20

        # Check history details
        history = equipment.changeover_history
        assert history[0][1] == "product_a"  # from
        assert history[0][2] == "product_b"  # to
        assert history[0][3] == 10.0  # duration

        assert history[1][1] == "product_b"
        assert history[1][2] == "product_c"
        assert history[1][3] == 15.0

    def test_get_changeover_metrics(self) -> None:
        """Test changeover metrics collection."""
        matrix = ChangeoverMatrix(
            matrix={
                "product_a": {"product_b": 15.0},
            },
            default_time=20.0,
        )

        equipment = EquipmentFlow(
            self.env,
            self.config,
            self.flow_capacity,
            self.processing,
            self.failures,
            changeover_matrix=matrix,
        )

        # Perform some changeovers
        def test_process():
            yield self.env.process(equipment.changeover("product_b", 15.0))
            yield self.env.process(equipment.changeover("product_c", 20.0))

        self.env.process(test_process())
        self.env.run(until=40)

        # Get metrics
        metrics = equipment.get_changeover_metrics()

        assert metrics["changeover_count"] == 2
        assert metrics["total_changeover_time"] == 35.0
        assert metrics["avg_changeover_time"] == 17.5
        assert metrics["current_product"] == "product_c"
        assert metrics["has_changeover_matrix"] is True
        assert metrics["changeover_matrix_default_time"] == 20.0
        assert len(metrics["recent_changeovers"]) == 2
