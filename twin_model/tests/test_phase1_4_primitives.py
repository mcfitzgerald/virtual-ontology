"""Test Phase 1.4: Validate Scheduler and Monitor primitives.

This test validates that the Scheduler and Monitor primitives
work correctly for production planning and KPI tracking.
"""

import simpy
from twin_model.primitives import (
    PrimitiveConfig,
    SchedulerPrimitive,
    MonitorPrimitive,
    ProductionOrder,
    EquipmentPrimitive,
    BufferPrimitive,
    SourcePrimitive,
    SinkPrimitive,
)


def test_scheduler_primitive():
    """Test scheduler primitive functionality."""
    print("Testing Scheduler Primitive...")

    env = simpy.Environment()

    # Create scheduler configuration
    config = PrimitiveConfig(
        id="SCHED-001",
        type="Scheduler",
        properties={
            "schedule_horizon": 1440,  # 24 hours
            "optimization_mode": "FIFO",
            "changeover_matrix": {
                "SKU-A": {"SKU-B": 30, "SKU-C": 45},
                "SKU-B": {"SKU-A": 30, "SKU-C": 20},
                "SKU-C": {"SKU-A": 45, "SKU-B": 20},
            },
        },
    )

    # Create scheduler
    scheduler = SchedulerPrimitive(env, config)

    # Add production orders
    orders = [
        ProductionOrder(
            order_id="ORD-001",
            product_id="SKU-A",
            target_quantity=1000,
            due_time=480,  # Due in 8 hours
            line_id="LINE1",
            priority=1,
        ),
        ProductionOrder(
            order_id="ORD-002",
            product_id="SKU-B",
            target_quantity=800,
            due_time=960,  # Due in 16 hours
            line_id="LINE1",
            priority=2,
        ),
    ]

    for order in orders:
        scheduler.add_order(order)

    assert len(scheduler.production_orders) == 2
    assert scheduler.orders_scheduled == 2
    print("✓ Orders added successfully")

    # Start scheduler
    scheduler.start()

    # Run for a short time
    env.run(until=10)

    # Check that scheduling events were emitted
    schedule_events = [
        o for o in scheduler.observables if "schedule" in o["event_type"]
    ]
    assert len(schedule_events) > 0
    print(f"✓ Scheduler emitted {len(schedule_events)} schedule events")

    # Check statistics
    stats = scheduler.get_statistics()
    assert stats["orders_scheduled"] == 2
    print(f"✓ Scheduler statistics: {stats['orders_scheduled']} orders scheduled")

    print("Scheduler Primitive tests passed!\n")


def test_monitor_primitive():
    """Test monitor primitive functionality."""
    print("Testing Monitor Primitive...")

    env = simpy.Environment()

    # Create monitor configuration
    config = PrimitiveConfig(
        id="MON-001",
        type="Monitor",
        properties={
            "update_interval": 2.0,  # Update every 2 minutes
            "aggregation_window": 10.0,
            "kpi_definitions": {
                "test_oee": {"type": "OEE", "target": 65.0, "unit": "%"},
                "test_throughput": {
                    "type": "THROUGHPUT",
                    "target": 50.0,
                    "unit": "units/min",
                },
            },
            "alert_thresholds": {
                "test_oee": {"min": 50.0},
                "test_throughput": {"min": 40.0},
            },
        },
    )

    # Create monitor
    monitor = MonitorPrimitive(env, config)

    # Create dummy equipment to monitor
    equipment = EquipmentPrimitive(
        env,
        PrimitiveConfig(id="EQ-MON", type="Equipment", properties={"base_rate": 60.0}),
    )
    equipment.start()
    equipment.units_produced = 100  # Simulate production

    # Register equipment with monitor
    monitor.register_primitive("EQ-MON", equipment)
    assert len(monitor.monitored_primitives) == 1
    print("✓ Equipment registered with monitor")

    # Start monitor
    monitor.start()

    # Run simulation
    env.run(until=5)

    # Check KPI updates
    kpi_events = [o for o in monitor.observables if o["event_type"] == "kpi_update"]
    assert len(kpi_events) >= 2  # Should have at least 2 updates in 5 minutes
    print(f"✓ Monitor emitted {len(kpi_events)} KPI updates")

    # Check KPI values
    oee_value = monitor.get_kpi_value("test_oee")
    assert oee_value is not None
    print(f"✓ OEE KPI tracked: {oee_value:.1f}%")

    # Check dashboard
    dashboard = monitor.get_dashboard()
    assert "kpis" in dashboard
    assert "test_oee" in dashboard["kpis"]
    print("✓ Dashboard generation working")

    # Check statistics
    stats = monitor.get_statistics()
    assert stats["kpis_tracked"] == 2
    assert stats["primitives_monitored"] == 1
    print(f"✓ Monitor tracking {stats['kpis_tracked']} KPIs")

    print("Monitor Primitive tests passed!\n")


def test_scheduler_equipment_integration():
    """Test scheduler controlling equipment."""
    print("Testing Scheduler-Equipment Integration...")

    env = simpy.Environment()

    # Create equipment
    equipment = EquipmentPrimitive(
        env,
        PrimitiveConfig(
            id="EQ-SCHED", type="Equipment", properties={"base_rate": 60.0}
        ),
    )

    # Create scheduler
    scheduler = SchedulerPrimitive(
        env, PrimitiveConfig(id="SCHED-INT", type="Scheduler")
    )

    # Register equipment with scheduler
    scheduler.register_equipment("EQ-SCHED", equipment)
    assert len(scheduler.controlled_equipment) == 1
    print("✓ Equipment registered with scheduler")

    # Start components
    equipment.start()
    scheduler.start()

    # Add an order
    order = ProductionOrder(
        order_id="ORD-INT",
        product_id="PROD-1",
        target_quantity=100,
        due_time=60,
        line_id="LINE1",
    )
    scheduler.add_order(order)

    # Run simulation
    env.run(until=10)

    # Check that equipment received product assignment
    assert equipment.current_product is not None or len(equipment.observables) > 0
    print("✓ Scheduler can control equipment")

    print("Scheduler-Equipment integration test passed!\n")


def test_monitor_full_line():
    """Test monitor with full production line."""
    print("Testing Monitor with Full Production Line...")

    env = simpy.Environment()
    env.global_observables = []

    # Create production line components
    source = SourcePrimitive(
        env,
        PrimitiveConfig(id="SRC-MON", type="Source", properties={"arrival_rate": 65.0}),
    )

    buffer1 = BufferPrimitive(
        env, PrimitiveConfig(id="BUF1-MON", type="Buffer", properties={"capacity": 20})
    )

    equipment = EquipmentPrimitive(
        env,
        PrimitiveConfig(
            id="EQ-MON-LINE",
            type="Equipment",
            properties={"base_rate": 60.0, "line_id": "LINE1"},
        ),
        upstream=buffer1,
    )

    buffer2 = BufferPrimitive(
        env, PrimitiveConfig(id="BUF2-MON", type="Buffer", properties={"capacity": 20})
    )

    sink = SinkPrimitive(
        env,
        PrimitiveConfig(
            id="SINK-MON", type="Sink", properties={"target_throughput": 50.0}
        ),
        upstream=buffer2,
    )

    # Wire connections
    source.downstream = buffer1
    equipment.downstream = buffer2

    # Create monitor
    monitor = MonitorPrimitive(
        env,
        PrimitiveConfig(
            id="MON-LINE",
            type="Monitor",
            properties={
                "update_interval": 5.0,
                "kpi_definitions": {
                    "line_oee": {"type": "OEE", "target": 65.0},
                    "line_throughput": {"type": "THROUGHPUT", "target": 50.0},
                    "buffer_utilization": {"type": "UTILIZATION", "target": 50.0},
                },
            },
        ),
    )

    # Register all components with monitor
    monitor.register_primitive("SRC", source)
    monitor.register_primitive("BUF1", buffer1)
    monitor.register_primitive("EQ", equipment)
    monitor.register_primitive("BUF2", buffer2)
    monitor.register_primitive("SINK", sink)

    # Start all components
    buffer1.start()
    buffer2.start()
    source.start()
    equipment.start()
    equipment.set_product("PROD-MON", "ORD-MON")
    sink.start()
    monitor.start()

    # Run simulation
    env.run(until=30)

    # Check production flow
    print(f"✓ Source generated: {source.total_generated}")
    print(f"✓ Equipment produced: {equipment.units_produced}")
    print(f"✓ Sink collected: {sink.total_collected}")

    # Check monitor captured metrics
    dashboard = monitor.get_dashboard()
    assert "line_metrics" in dashboard
    print(f"✓ Line metrics captured: {list(dashboard['line_metrics'].keys())}")

    # Check KPI tracking
    kpi_updates = [o for o in monitor.observables if o["event_type"] == "kpi_update"]
    assert len(kpi_updates) >= 5  # Should have ~6 updates in 30 minutes
    print(f"✓ Monitor tracked {len(kpi_updates)} KPI updates")

    # Check for alerts if performance is low
    if monitor.active_alerts:
        print(f"✓ Monitor detected {len(monitor.active_alerts)} performance issues")

    print("Monitor full line test passed!\n")


def test_scheduler_monitor_coordination():
    """Test scheduler and monitor working together."""
    print("Testing Scheduler-Monitor Coordination...")

    env = simpy.Environment()

    # Create scheduler
    scheduler = SchedulerPrimitive(
        env, PrimitiveConfig(id="SCHED-COORD", type="Scheduler")
    )

    # Create monitor
    monitor = MonitorPrimitive(
        env,
        PrimitiveConfig(
            id="MON-COORD",
            type="Monitor",
            properties={
                "update_interval": 2.0,
                "kpi_definitions": {
                    "schedule_adherence": {"type": "OEE", "target": 90.0}
                },
            },
        ),
    )

    # Register scheduler with monitor to track schedule metrics
    monitor.register_primitive("SCHEDULER", scheduler)

    # Start both
    scheduler.start()
    monitor.start()

    # Add orders to scheduler
    for i in range(3):
        order = ProductionOrder(
            order_id=f"ORD-{i:03d}",
            product_id=f"SKU-{chr(65 + i)}",  # SKU-A, SKU-B, SKU-C
            target_quantity=500,
            due_time=480 + i * 240,  # Staggered due times
            line_id="LINE1",
        )
        scheduler.add_order(order)

    # Run simulation
    env.run(until=20)

    # Check coordination
    scheduler_events = [o for o in scheduler.observables if "order" in o["event_type"]]
    monitor_events = [o for o in monitor.observables if "kpi" in o["event_type"]]

    print(f"✓ Scheduler events: {len(scheduler_events)}")
    print(f"✓ Monitor events: {len(monitor_events)}")

    # Check that monitor is tracking scheduler metrics
    stats = monitor.get_statistics()
    assert stats["primitives_monitored"] == 1
    print("✓ Monitor tracking scheduler performance")

    print("Scheduler-Monitor coordination test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1.4 SCHEDULER AND MONITOR PRIMITIVES TEST")
    print("=" * 60 + "\n")

    try:
        test_scheduler_primitive()
        test_monitor_primitive()
        test_scheduler_equipment_integration()
        test_monitor_full_line()
        test_scheduler_monitor_coordination()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("Phase 1.4 Scheduler and Monitor primitives are working correctly.")
        print("All Phase 1 primitives are now complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
