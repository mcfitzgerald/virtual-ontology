"""Unit tests for container-based flow primitives."""

import pytest
import simpy

from twin_model.primitives import (
    EquipmentFlow,
    FailureParameters,
    FlowCapacity,
    FlowState,
    ProcessingParameters,
    ProductionOrder,
    SinkFlow,
    SourceFlow,
)


class TestFlowCapacity:
    """Test FlowCapacity dataclass validation."""

    def test_valid_capacity(self):
        """Test creating valid flow capacity."""
        capacity = FlowCapacity(max_input_rate=100.0, max_output_rate=95.0, internal_capacity=500.0, initial_level=50.0)
        assert capacity.max_input_rate == 100.0
        assert capacity.max_output_rate == 95.0
        assert capacity.internal_capacity == 500.0
        assert capacity.initial_level == 50.0

    def test_invalid_rates(self):
        """Test invalid rate values."""
        with pytest.raises(ValueError, match="max_input_rate must be positive"):
            FlowCapacity(0, 100, 500)

        with pytest.raises(ValueError, match="max_output_rate must be positive"):
            FlowCapacity(100, -1, 500)

    def test_invalid_capacity(self):
        """Test invalid capacity values."""
        with pytest.raises(ValueError, match="internal_capacity must be positive"):
            FlowCapacity(100, 100, 0)

        with pytest.raises(ValueError, match="initial_level cannot be negative"):
            FlowCapacity(100, 100, 500, -10)

        with pytest.raises(ValueError, match="initial_level .* cannot exceed"):
            FlowCapacity(100, 100, 500, 600)


class TestEquipmentFlow:
    """Test EquipmentFlow continuous processing."""

    def test_continuous_flow(self):
        """Test continuous flow processing."""
        env = simpy.Environment()

        # Create equipment with known parameters
        equipment = EquipmentFlow(
            env=env,
            config={"id": "TEST-01"},
            flow_capacity=FlowCapacity(100, 100, 500),
            processing=ProcessingParameters(100, 0.95, 1.0, 10, 0.1),
            failures=FailureParameters(1000, 10, 0, 0),  # No failures for this test
        )

        # Add material buffers with sufficient input
        equipment.input_buffer = simpy.Container(env, 2000, init=1500)  # More input material
        equipment.output_buffer = simpy.Container(env, 2000, init=0)

        # Start process
        equipment.start()

        # Run simulation
        env.run(until=10)

        # Verify continuous production
        # With 100 units/min * 10 min = 1000 units theoretical
        # With 0.95 quality = 950 good units expected
        assert equipment.flow_metrics.total_output > 900
        assert equipment.flow_metrics.total_output < 1000

        # Verify scrap generation (5% scrap rate)
        assert equipment.flow_metrics.total_scrap > 45
        assert equipment.flow_metrics.total_scrap < 55

        # Verify material conservation
        total_produced = equipment.flow_metrics.total_output + equipment.flow_metrics.total_scrap
        assert abs(equipment.flow_metrics.total_input - total_produced) < 1.0

    def test_starvation_handling(self):
        """Test equipment behavior when starved of input."""
        env = simpy.Environment()

        equipment = EquipmentFlow(
            env=env,
            config={"id": "TEST-02"},
            flow_capacity=FlowCapacity(100, 100, 500),
            processing=ProcessingParameters(100, 0.95, 1.0, 10, 0.1),
            failures=FailureParameters(1000, 10, 0, 0),
        )

        # Empty input buffer
        equipment.input_buffer = simpy.Container(env, 1000, init=0)
        equipment.output_buffer = simpy.Container(env, 1000, init=0)

        equipment.start()
        env.run(until=1)

        # Should be starved
        assert equipment.current_state == FlowState.STARVED_UPSTREAM
        assert equipment.flow_metrics.total_output == 0

    def test_blocking_handling(self):
        """Test equipment behavior when blocked downstream."""
        env = simpy.Environment()

        equipment = EquipmentFlow(
            env=env,
            config={"id": "TEST-03"},
            flow_capacity=FlowCapacity(100, 100, 500),
            processing=ProcessingParameters(100, 0.95, 1.0, 10, 0.1),
            failures=FailureParameters(1000, 10, 0, 0),
        )

        # Setup buffers - output buffer is full
        equipment.input_buffer = simpy.Container(env, 1000, init=100)  # Some input material
        equipment.output_buffer = simpy.Container(env, 100, init=99)  # Nearly full buffer

        equipment.start()
        env.run(until=2)  # Give more time to process and get blocked

        # Should be blocked since output buffer is full
        assert (
            equipment.current_state == FlowState.BLOCKED_DOWNSTREAM
        ), f"Expected BLOCKED_DOWNSTREAM but got {equipment.current_state}"
        # Also verify that blocking was tracked
        assert equipment.flow_metrics.state_durations.get(FlowState.BLOCKED_DOWNSTREAM, 0) > 0


class TestSourceFlow:
    """Test SourceFlow material generation."""

    def test_continuous_generation(self):
        """Test continuous material generation."""
        env = simpy.Environment()

        source = SourceFlow(
            env=env,
            config={"id": "SOURCE-01", "continuous_mode": True},
            flow_capacity=FlowCapacity(1000, 1000, 10000),
            generation_rate=50.0,  # 50 units/minute
            generation_interval=0.1,
        )

        # Add output buffer
        source.output_buffer = simpy.Container(env, 1000, init=0)

        source.start()
        env.run(until=10)

        # Should generate ~500 units (50 units/min * 10 min)
        assert source.flow_metrics.total_output > 450
        assert source.flow_metrics.total_output < 550

    def test_order_based_generation(self):
        """Test order-based material generation."""
        env = simpy.Environment()

        source = SourceFlow(
            env=env,
            config={"id": "SOURCE-02", "continuous_mode": False},
            flow_capacity=FlowCapacity(1000, 1000, 10000),
            generation_rate=100.0,
            generation_interval=0.1,
        )

        source.output_buffer = simpy.Container(env, 1000, init=0)

        # Add production order
        order = ProductionOrder(order_id="ORDER-001", product_id="PRODUCT-A", target_volume=200.0, due_time=15.0)
        source.add_order(order)

        source.start()
        env.run(until=5)

        # Should complete the order
        assert len(source.completed_orders) == 1
        assert source.completed_orders[0].order_id == "ORDER-001"
        assert source.completed_orders[0].completed_volume >= 200.0

    def test_order_priority(self):
        """Test order priority handling."""
        env = simpy.Environment()

        source = SourceFlow(
            env=env,
            config={"id": "SOURCE-03", "continuous_mode": False},
            flow_capacity=FlowCapacity(1000, 1000, 10000),
            generation_rate=100.0,
            generation_interval=0.1,
        )

        # Add multiple orders with different priorities
        order1 = ProductionOrder("ORDER-001", "PRODUCT-A", 100, 10, priority=1)
        order2 = ProductionOrder("ORDER-002", "PRODUCT-B", 100, 10, priority=5)  # Higher priority
        order3 = ProductionOrder("ORDER-003", "PRODUCT-C", 100, 10, priority=3)

        source.add_order(order1)
        source.add_order(order2)
        source.add_order(order3)

        # Higher priority order should be selected first
        next_order = source._get_next_order()
        assert next_order.order_id == "ORDER-002"


class TestSinkFlow:
    """Test SinkFlow collection and OEE calculation."""

    def test_product_collection(self):
        """Test product collection."""
        env = simpy.Environment()

        sink = SinkFlow(
            env=env,
            config={"id": "SINK-01", "nominal_rate": 100.0},
            flow_capacity=FlowCapacity(1000, 1000, 10000),
            collection_rate=100.0,
            collection_interval=0.1,
        )

        # Add input buffer with material
        sink.input_buffer = simpy.Container(env, 1000, init=500)

        sink.start()
        env.run(until=5)

        # Should collect material
        assert sink.total_collected > 0
        assert sink.total_collected <= 500  # Can't collect more than available

    def test_oee_calculation(self):
        """Test OEE calculation."""
        env = simpy.Environment()

        sink = SinkFlow(
            env=env,
            config={"id": "SINK-02", "nominal_rate": 100.0, "window_duration": 1.0},
            flow_capacity=FlowCapacity(1000, 1000, 10000),
            collection_rate=100.0,
            collection_interval=0.1,
        )

        sink.input_buffer = simpy.Container(env, 1000, init=1000)

        sink.start()
        env.run(until=10)

        # Calculate OEE
        oee, availability, performance, quality = sink.calculate_oee(window_minutes=10)

        # Should have reasonable OEE values
        assert 0 <= oee <= 100
        assert 0 <= availability <= 100
        assert 0 <= performance <= 100
        assert 0 <= quality <= 100

        # With continuous flow and no failures, should have high values
        assert availability > 50  # Should be mostly available
        assert quality > 90  # No quality issues in sink


class TestIntegratedFlow:
    """Test integrated flow from source to sink."""

    def test_simple_line(self):
        """Test simple production line."""
        env = simpy.Environment()

        # Create source
        source = SourceFlow(
            env=env,
            config={"id": "SOURCE", "continuous_mode": True},
            flow_capacity=FlowCapacity(1000, 100, 1000),
            generation_rate=100.0,
        )

        # Create equipment with realistic parameters
        equipment = EquipmentFlow(
            env=env,
            config={"id": "EQUIPMENT"},
            flow_capacity=FlowCapacity(100, 100, 500),
            processing=ProcessingParameters(
                nominal_rate=100,
                quality_rate=0.92,  # 92% quality (realistic)
                performance_factor=1.0,  # 100% to ensure processing happens
                batch_size=10,
                processing_interval=0.1,
            ),
            failures=FailureParameters(
                mtbf=30,  # Failure every 30 minutes
                mttr=3,  # 3 minutes to repair
                micro_stop_rate=4,  # 4 micro-stops per hour
                micro_stop_duration=10,  # 10 seconds each
            ),
        )

        # Create sink
        sink = SinkFlow(
            env=env,
            config={"id": "SINK", "nominal_rate": 95.0},
            flow_capacity=FlowCapacity(100, 100, 10000),
            collection_rate=100.0,
        )

        # Wire connections with shared buffers
        buffer1 = simpy.Container(env, 1000, init=0)
        source.output_buffer = buffer1
        equipment.input_buffer = buffer1

        buffer2 = simpy.Container(env, 1000, init=0)
        equipment.output_buffer = buffer2
        sink.input_buffer = buffer2

        # Register upstream equipment with sink for quality tracking
        sink.upstream_equipment = [equipment]

        # Start processes
        source.start()
        equipment.start()
        sink.start()

        # Run simulation
        env.run(until=60)  # 1 hour

        # Verify flow through system
        assert source.flow_metrics.total_output > 0
        assert equipment.flow_metrics.total_input > 0
        assert equipment.flow_metrics.total_output > 0
        assert sink.total_collected > 0

        # Verify material conservation (with quality losses)
        # Source output should roughly equal equipment input (accounting for buffer storage)
        assert abs(source.flow_metrics.total_output - equipment.flow_metrics.total_input) <= buffer1.capacity

        # Equipment good output should roughly equal sink collection
        assert abs(equipment.flow_metrics.total_output - sink.total_collected) < 100

        # Calculate end-to-end OEE
        oee, _, _, _ = sink.calculate_oee(window_minutes=60)

        # Should achieve reasonable OEE (wider range due to stochastic failures)
        assert 30 <= oee <= 90  # Allow wider margin for test conditions
