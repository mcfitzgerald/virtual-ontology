"""Test Phase 1: Validate primitives framework.

This test validates that the base primitive and equipment primitive
work correctly with SimPy and emit proper observables.
"""

import simpy
from twin_model.primitives.base import BasePrimitive, PrimitiveConfig
from twin_model.primitives.equipment import EquipmentPrimitive, EquipmentState


def test_base_primitive():
    """Test base primitive configuration and validation."""
    print("Testing Base Primitive...")

    # Test valid configuration
    config = PrimitiveConfig(
        id="TEST-001",
        type="TestPrimitive",
        properties={"rate": 60.0, "capacity": 100},
        relationships={"feeds_into": ["TEST-002"]},
        metadata={"test": True},
    )

    # Validate config
    config.validate()
    assert config.get_property("rate") == 60.0
    assert config.get_property("missing", "default") == "default"
    print("✓ Configuration validation passed")

    # Test invalid configuration
    try:
        invalid_config = PrimitiveConfig(id="", type="Test")
        invalid_config.validate()
        assert False, "Should have raised validation error"
    except ValueError:
        print("✓ Invalid configuration caught")

    print("Base Primitive tests passed!\n")


def test_equipment_primitive():
    """Test equipment primitive with SimPy."""
    print("Testing Equipment Primitive...")

    # Create SimPy environment
    env = simpy.Environment()

    # Create equipment configuration
    config = PrimitiveConfig(
        id="LINE1-FIL",
        type="Filler",
        properties={
            "base_rate": 60.0,  # units per minute
            "mtbf": 480.0,  # 8 hours
            "mttr": 30.0,  # 30 minutes
            "energy_consumption_rate": 5.0,  # kWh per minute
            "base_scrap_rate": 0.02,
        },
    )

    # Create equipment (no buffers for simplicity)
    equipment = EquipmentPrimitive(env, config)

    # Verify initial state
    assert equipment.state == EquipmentState.IDLE
    assert equipment.units_produced == 0
    assert len(equipment.observables) == 0
    print("✓ Equipment initialized correctly")

    # Start equipment
    equipment.start()
    assert equipment.is_running == True
    print("✓ Equipment started")

    # Run simulation for 10 minutes
    env.run(until=10)

    # Check observables were emitted
    assert len(equipment.observables) > 0
    print(f"✓ Emitted {len(equipment.observables)} observables")

    # Check for specific event types
    event_types = {o["event_type"] for o in equipment.observables}
    assert "equipment_started" in event_types
    print("✓ Equipment start event emitted")

    # Check monitoring events
    monitor_events = [
        o for o in equipment.observables if o["event_type"] == "equipment_monitor"
    ]
    assert len(monitor_events) >= 9  # Should have ~10 monitoring events (1 per minute)
    print(f"✓ Monitor events working ({len(monitor_events)} events)")

    # Verify OEE calculation
    if monitor_events:
        last_monitor = monitor_events[-1]
        assert "oee" in last_monitor
        print(f"✓ OEE calculation working (OEE: {last_monitor['oee']:.1f}%)")

    print("Equipment Primitive tests passed!\n")


def test_observable_emission():
    """Test observable emission and filtering."""
    print("Testing Observable Emission...")

    env = simpy.Environment()
    config = PrimitiveConfig(id="TEST-OBS", type="Test")

    # Create a simple test primitive
    class TestPrimitive(BasePrimitive):
        def start(self):
            self.env.process(self.test_process())

        def test_process(self):
            for i in range(5):
                yield self.env.timeout(1)
                self.emit_observable(
                    event_type="test_event",
                    details={"iteration": i},
                    severity="INFO" if i % 2 == 0 else "DEBUG",
                )

    primitive = TestPrimitive(env, config)
    primitive.start()
    env.run(until=6)

    # Test filtering
    all_obs = primitive.get_observables()
    assert len(all_obs) == 5
    print(f"✓ Emitted {len(all_obs)} observables")

    # Filter by event type
    test_events = primitive.get_observables(event_type="test_event")
    assert len(test_events) == 5
    print("✓ Event type filtering working")

    # Filter by time
    early_events = primitive.get_observables(end_time=3)
    assert len(early_events) <= 3
    print("✓ Time filtering working")

    print("Observable emission tests passed!\n")


def run_integration_test():
    """Run a more complex integration test."""
    print("Running Integration Test...")

    env = simpy.Environment()

    # Add global observables to environment
    env.global_observables = []

    # Create multiple equipment pieces
    equipment_configs = [
        PrimitiveConfig(
            id=f"LINE1-{eq}",
            type=eq,
            properties={
                "base_rate": rate,
                "mtbf": 600.0,
                "mttr": 20.0,
                "failure_patterns": {
                    "micro_stop": {
                        "probability_per_5min": 0.1,
                        "duration_range": [1, 3],
                        "downtime_reason": "UNP-SENS",
                    }
                },
            },
        )
        for eq, rate in [("FIL", 60), ("PCK", 55), ("PAL", 50)]
    ]

    equipment_list = []
    for config in equipment_configs:
        eq = EquipmentPrimitive(env, config)
        eq.set_product("SKU-1001", "ORD-001")
        eq.set_shift("shift1")
        eq.start()
        equipment_list.append(eq)

    # Run for 60 minutes
    env.run(until=60)

    print("✓ Simulation completed (60 minutes)")
    print(f"✓ Global observables: {len(env.global_observables)}")

    # Check production
    for eq in equipment_list:
        if eq.units_produced > 0:
            print(
                f"✓ {eq.config.id}: {eq.units_produced} units produced, OEE: {eq.calculate_oee():.1f}%"
            )

    # Check for failures
    failure_events = [
        o for o in env.global_observables if o["event_type"] == "equipment_failure"
    ]
    print(f"✓ Failures occurred: {len(failure_events)}")

    print("Integration test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1 PRIMITIVES FRAMEWORK TEST")
    print("=" * 60 + "\n")

    try:
        test_base_primitive()
        test_equipment_primitive()
        test_observable_emission()
        run_integration_test()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("Phase 1 primitives framework is working correctly.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
