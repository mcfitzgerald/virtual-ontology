"""Test Phase 1.3: Validate Buffer, Source, and Sink primitives.

This test validates that the Buffer, Source, and Sink primitives
work correctly with SimPy and can be connected together.
"""

import simpy
from twin_model.primitives import (
    PrimitiveConfig,
    BufferPrimitive,
    SourcePrimitive,
    SinkPrimitive,
    EquipmentPrimitive,
)


def test_buffer_primitive():
    """Test buffer primitive functionality."""
    print("Testing Buffer Primitive...")

    env = simpy.Environment()

    # Create buffer configuration
    config = PrimitiveConfig(
        id="BUF-001",
        type="Buffer",
        properties={
            "capacity": 50,
            "initial_level": 10,
            "buffer_type": "FIFO",
            "min_level": 5,
            "max_dwell_time": 30.0,
        },
    )

    # Create buffer
    buffer = BufferPrimitive(env, config)
    buffer.start()

    # Check initial state
    assert buffer.level == 10
    assert buffer.capacity == 50
    print("✓ Buffer initialized with correct parameters")

    # Test put/get operations
    def test_operations():
        # Put items
        yield from buffer.put(5, product_id="SKU-001")
        assert buffer.level == 15
        print("✓ Put operation working")

        # Get items
        items = yield from buffer.get(3)
        assert buffer.level == 12
        assert len(items) == 3
        print("✓ Get operation working")

        # Check statistics
        stats = buffer.get_statistics()
        assert stats["total_throughput"] == 3
        print("✓ Statistics tracking working")

    env.process(test_operations())
    env.run(until=5)

    # Check monitoring observables
    monitor_events = [
        o for o in buffer.observables if o["event_type"] == "buffer_monitor"
    ]
    assert len(monitor_events) >= 4  # Should have ~5 monitoring events
    print(f"✓ Buffer monitoring active ({len(monitor_events)} events)")

    print("Buffer Primitive tests passed!\n")


def test_source_primitive():
    """Test source primitive functionality."""
    print("Testing Source Primitive...")

    env = simpy.Environment()

    # Create source configuration
    config = PrimitiveConfig(
        id="SRC-001",
        type="Source",
        properties={
            "arrival_pattern": "EXPONENTIAL",
            "arrival_rate": 120.0,  # 2 per minute
            "batch_size": 1,
            "product_mix": {"SKU-A": 0.6, "SKU-B": 0.4},
            "quality_rate": 0.95,
            "disruption_probability": 0.0,  # No disruptions for test
        },
    )

    # Create a dummy buffer for source to send to
    dummy_buffer = BufferPrimitive(
        env,
        PrimitiveConfig(id="DUMMY-BUF", type="Buffer", properties={"capacity": 1000}),
    )
    dummy_buffer.start()

    # Create source with downstream
    source = SourcePrimitive(env, config, downstream=dummy_buffer)
    source.start()

    # Run for 10 minutes
    env.run(until=10)

    # Check generation
    assert source.total_generated > 0
    print(f"✓ Source generated {source.total_generated} units")

    # Check product mix
    generation_events = [
        o for o in source.observables if o["event_type"] == "material_generated"
    ]
    products = [e["product"] for e in generation_events]
    sku_a_count = products.count("SKU-A")
    sku_b_count = products.count("SKU-B")

    if len(products) > 10:  # Only check mix if we have enough samples
        ratio = sku_a_count / (sku_a_count + sku_b_count)
        assert 0.4 < ratio < 0.8  # Should be roughly 60/40
        print(f"✓ Product mix working (A:{sku_a_count}, B:{sku_b_count})")

    # Check statistics
    stats = source.get_statistics()
    assert stats["total_generated"] > 0
    assert stats["efficiency"] > 0
    print(f"✓ Source efficiency: {stats['efficiency']:.1%}")

    print("Source Primitive tests passed!\n")


def test_sink_primitive():
    """Test sink primitive functionality."""
    print("Testing Sink Primitive...")

    env = simpy.Environment()

    # Create sink configuration
    config = PrimitiveConfig(
        id="SINK-001",
        type="Sink",
        properties={
            "collection_rate": 100.0,
            "quality_threshold": 0.5,
            "target_throughput": 50.0,
            "order_tracking": True,
        },
    )

    # Create sink
    sink = SinkPrimitive(env, config)

    # Simulate collection process
    def simulate_collection():
        sink.start()

        # Simulate collecting products
        for i in range(10):
            yield env.timeout(0.5)
            yield from sink._process_product(
                {
                    "product_id": f"SKU-{i % 3}",
                    "order_id": f"ORD-{i // 3}",
                    "quality_score": 0.9 if i % 5 != 0 else 0.3,  # Some low quality
                }
            )

    env.process(simulate_collection())
    env.run(until=10)

    # Check collection
    assert sink.total_collected > 0
    assert sink.total_rejected > 0  # Should have some rejections
    print(f"✓ Sink collected {sink.total_collected}, rejected {sink.total_rejected}")

    # Check order tracking
    assert len(sink.completed_orders) > 0 or len(sink.pending_orders) > 0
    print(
        f"✓ Order tracking: {len(sink.completed_orders)} completed, {len(sink.pending_orders)} pending"
    )

    # Check statistics
    stats = sink.get_statistics()
    assert "acceptance_rate" in stats
    assert "current_throughput" in stats
    print(f"✓ Acceptance rate: {stats['acceptance_rate']:.1%}")

    print("Sink Primitive tests passed!\n")


def test_source_buffer_sink_integration():
    """Test integration of Source -> Buffer -> Sink."""
    print("Testing Source -> Buffer -> Sink Integration...")

    env = simpy.Environment()
    env.global_observables = []

    # Create buffer
    buffer_config = PrimitiveConfig(
        id="BUF-INT", type="Buffer", properties={"capacity": 20, "initial_level": 0}
    )
    buffer = BufferPrimitive(env, buffer_config)

    # Create source feeding into buffer
    source_config = PrimitiveConfig(
        id="SRC-INT",
        type="Source",
        properties={
            "arrival_pattern": "CONSTANT",
            "arrival_rate": 60.0,  # 1 per minute
            "product_mix": {"PROD-1": 1.0},
            "quality_rate": 1.0,  # All good quality
        },
    )
    source = SourcePrimitive(env, source_config, downstream=buffer)

    # Create sink pulling from buffer
    sink_config = PrimitiveConfig(
        id="SINK-INT",
        type="Sink",
        properties={
            "collection_rate": 50.0,  # Slightly slower than source
            "target_throughput": 45.0,
        },
    )
    sink = SinkPrimitive(env, sink_config, upstream=buffer)

    # Start all primitives
    buffer.start()
    source.start()
    sink.start()

    # Run simulation
    env.run(until=30)

    print(f"✓ Source generated: {source.total_generated}")
    print(f"✓ Buffer level: {buffer.level}/{buffer.capacity}")
    print(f"✓ Sink collected: {sink.total_collected}")

    # Buffer should have accumulated some inventory
    assert buffer.level > 0
    print("✓ Buffer is accumulating inventory (source faster than sink)")

    # Check flow consistency
    assert source.total_generated == sink.total_collected + buffer.level
    print("✓ Material flow is conserved")

    # Check observables
    total_observables = (
        len(source.observables) + len(buffer.observables) + len(sink.observables)
    )
    print(f"✓ Total observables emitted: {total_observables}")

    print("Integration test passed!\n")


def test_complete_production_line():
    """Test complete production line: Source -> Buffer -> Equipment -> Buffer -> Sink."""
    print("Testing Complete Production Line...")

    env = simpy.Environment()

    # Create input buffer
    input_buffer = BufferPrimitive(
        env,
        PrimitiveConfig(
            id="BUF-IN", type="Buffer", properties={"capacity": 30, "initial_level": 15}
        ),
    )

    # Create output buffer
    output_buffer = BufferPrimitive(
        env,
        PrimitiveConfig(
            id="BUF-OUT", type="Buffer", properties={"capacity": 30, "initial_level": 0}
        ),
    )

    # Create source
    source = SourcePrimitive(
        env,
        PrimitiveConfig(
            id="SRC-LINE",
            type="Source",
            properties={
                "arrival_pattern": "NORMAL",
                "arrival_rate": 65.0,
                "product_mix": {"SKU-1": 0.5, "SKU-2": 0.5},
                "supply_variability": 0.2,
            },
        ),
        downstream=input_buffer,
    )

    # Create equipment
    equipment = EquipmentPrimitive(
        env,
        PrimitiveConfig(
            id="EQ-LINE",
            type="Equipment",
            properties={
                "base_rate": 60.0,
                "mtbf": 1000.0,
                "mttr": 10.0,
                "base_scrap_rate": 0.05,
            },
        ),
        upstream=input_buffer,
        downstream=output_buffer,
    )

    # Create sink
    sink = SinkPrimitive(
        env,
        PrimitiveConfig(
            id="SINK-LINE",
            type="Sink",
            properties={"collection_rate": 55.0, "target_throughput": 50.0},
        ),
        upstream=output_buffer,
    )

    # Start all components
    input_buffer.start()
    output_buffer.start()
    source.start()
    equipment.start()
    equipment.set_product("SKU-1", "ORD-001")
    sink.start()

    # Run for 60 minutes
    env.run(until=60)

    # Print results
    print(f"✓ Source generated: {source.total_generated}")
    print(f"✓ Input buffer: {input_buffer.level}/{input_buffer.capacity}")
    print(
        f"✓ Equipment produced: {equipment.units_produced}, scrapped: {equipment.units_scrapped}"
    )
    print(f"✓ Output buffer: {output_buffer.level}/{output_buffer.capacity}")
    print(f"✓ Sink collected: {sink.total_collected}")
    print(f"✓ Equipment OEE: {equipment.calculate_oee():.1f}%")

    # Check that material is flowing through the system
    assert source.total_generated > 0
    assert equipment.units_produced > 0
    assert sink.total_collected > 0

    # Check buffer utilization
    input_util = input_buffer.get_utilization()
    output_util = output_buffer.get_utilization()
    print(
        f"✓ Buffer utilization - Input: {input_util:.1f}%, Output: {output_util:.1f}%"
    )

    print("Complete production line test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1.3 BUFFER, SOURCE, SINK PRIMITIVES TEST")
    print("=" * 60 + "\n")

    try:
        test_buffer_primitive()
        test_source_primitive()
        test_sink_primitive()
        test_source_buffer_sink_integration()
        test_complete_production_line()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("Phase 1.3 Buffer, Source, and Sink primitives are working correctly.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
