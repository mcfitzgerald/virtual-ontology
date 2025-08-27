"""Test material flow through the system.

This module tests end-to-end material flow from source through equipment
to sink, validating queue operations and state transitions.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any

import simpy

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twin_model.primitives.source import SourcePrimitiveV2
from twin_model.primitives.equipment import EquipmentPrimitiveV2, EquipmentState
from twin_model.primitives.sink import SinkPrimitiveV2
from twin_model.primitives.base import PrimitiveConfig


def create_test_line(env: simpy.Environment) -> Dict[str, Any]:
    """Create a simple test production line.
    
    Args:
        env: SimPy environment
    
    Returns:
        Dictionary with line components
    """
    # Create configurations
    source_config = PrimitiveConfig(
        id="TEST-SOURCE",
        type="SourcePrimitiveV2",
        properties={
            "order_mode": False,  # Continuous generation
            "arrival_rate": 10.0,  # 10 units/minute
            "default_product": "TEST-PRODUCT",
            "warmup_period": 0.0  # No warmup for testing
        }
    )
    
    equipment1_config = PrimitiveConfig(
        id="TEST-EQUIP-1",
        type="EquipmentPrimitiveV2",
        properties={
            "equipment_type": "Filler",
            "base_rate": 12.0,  # Slightly faster than source
            "internal_queue_size": 10,
            "performance_factor": 0.9,
            "scrap_rate": 0.05,
            "micro_stop_probability": 0.1,  # Low for testing
            "warmup_period": 0.0
        }
    )
    
    equipment2_config = PrimitiveConfig(
        id="TEST-EQUIP-2",
        type="EquipmentPrimitiveV2",
        properties={
            "equipment_type": "Packer",
            "base_rate": 8.0,  # Bottleneck
            "internal_queue_size": 10,
            "performance_factor": 0.85,
            "scrap_rate": 0.03,
            "micro_stop_probability": 0.1,
            "warmup_period": 0.0
        }
    )
    
    sink_config = PrimitiveConfig(
        id="TEST-SINK",
        type="SinkPrimitiveV2",
        properties={
            "collection_mode": "continuous",
            "track_throughput": True,
            "track_orders": True
        }
    )
    
    # Create primitives
    source = SourcePrimitiveV2(env, source_config)
    equipment1 = EquipmentPrimitiveV2(env, equipment1_config)
    equipment2 = EquipmentPrimitiveV2(env, equipment2_config)
    sink = SinkPrimitiveV2(env, sink_config)
    
    # Wire connections (direct equipment-to-equipment)
    source.set_downstream(equipment1.input_queue)
    equipment1.connect_to(equipment2)
    equipment2.downstream_equipment = sink  # Connect to sink
    sink.set_upstream(equipment2.output_queue)
    
    # Start processes
    source.process = env.process(source.run())
    equipment1.process = env.process(equipment1.run())
    equipment2.process = env.process(equipment2.run())
    sink.process = env.process(sink.run())
    
    return {
        "source": source,
        "equipment1": equipment1,
        "equipment2": equipment2,
        "sink": sink,
        "env": env
    }


def test_basic_material_flow():
    """Test basic material flow through the line."""
    print("\n" + "="*60)
    print("Testing Basic Material Flow")
    print("="*60)
    
    env = simpy.Environment()
    line = create_test_line(env)
    
    # Run for 10 minutes
    env.run(until=10)
    
    # Check source generation
    source_generated = line["source"].units_generated
    print(f"\nSource generated: {source_generated} units")
    assert source_generated > 0, "Source should generate units"
    
    # Check equipment processing
    equip1_produced = line["equipment1"].units_produced
    equip1_scrapped = line["equipment1"].units_scrapped
    print(f"Equipment 1 produced: {equip1_produced}, scrapped: {equip1_scrapped}")
    assert equip1_produced > 0, "Equipment 1 should produce units"
    
    equip2_produced = line["equipment2"].units_produced
    equip2_scrapped = line["equipment2"].units_scrapped
    print(f"Equipment 2 produced: {equip2_produced}, scrapped: {equip2_scrapped}")
    assert equip2_produced > 0, "Equipment 2 should produce units"
    
    # Check sink collection
    sink_collected = line["sink"].total_units_collected
    print(f"Sink collected: {sink_collected} units")
    assert sink_collected > 0, "Sink should collect units"
    
    # Verify material conservation (approximately)
    # Generated should roughly equal produced + scrapped
    total_processed = equip1_produced + equip1_scrapped
    print(f"\nMaterial conservation check:")
    print(f"  Generated: {source_generated}")
    print(f"  Processed by Equip1: {total_processed}")
    print(f"  Difference: {abs(source_generated - total_processed)}")
    
    # The difference should be small (units in queues)
    assert abs(source_generated - total_processed) <= 20, "Material conservation violated"
    
    print("\n✓ Basic material flow test passed")
    return True


def test_queue_dynamics():
    """Test queue filling and emptying dynamics."""
    print("\n" + "="*60)
    print("Testing Queue Dynamics")
    print("="*60)
    
    env = simpy.Environment()
    
    # Create line with specific rates to test queuing
    source_config = PrimitiveConfig(
        id="QUEUE-SOURCE",
        type="SourcePrimitiveV2",
        properties={
            "order_mode": False,  # Continuous generation
            "arrival_rate": 20.0,  # Fast source
            "warmup_period": 0.0
        }
    )
    
    equipment_config = PrimitiveConfig(
        id="QUEUE-EQUIP",
        type="EquipmentPrimitiveV2",
        properties={
            "base_rate": 10.0,  # Slow equipment (bottleneck)
            "internal_queue_size": 5,  # Small queue
            "performance_factor": 1.0,  # Perfect performance
            "scrap_rate": 0.0,  # No scrap
            "micro_stop_probability": 0.0,  # No failures
            "warmup_period": 0.0
        }
    )
    
    sink_config = PrimitiveConfig(
        id="QUEUE-SINK",
        type="SinkPrimitiveV2",
        properties={}
    )
    
    source = SourcePrimitiveV2(env, source_config)
    equipment = EquipmentPrimitiveV2(env, equipment_config)
    sink = SinkPrimitiveV2(env, sink_config)
    
    source.set_downstream(equipment.input_queue)
    equipment.downstream_equipment = sink
    sink.set_upstream(equipment.output_queue)
    
    # Track queue levels over time
    queue_levels = []
    
    def monitor_queues(env, equipment, queue_levels):
        """Monitor queue levels periodically."""
        while True:
            queue_levels.append({
                "time": env.now,
                "input_queue": len(equipment.input_queue.items),
                "output_queue": len(equipment.output_queue.items)
            })
            yield env.timeout(0.5)  # Check every 0.5 minutes
    
    # Start processes
    source.process = env.process(source.run())
    equipment.process = env.process(equipment.run())
    sink.process = env.process(sink.run())
    env.process(monitor_queues(env, equipment, queue_levels))
    
    # Run simulation
    env.run(until=5)
    
    # Analyze queue behavior
    print(f"\nQueue level samples: {len(queue_levels)}")
    
    # Check that input queue fills up (source faster than equipment)
    max_input_queue = max(ql["input_queue"] for ql in queue_levels)
    print(f"Max input queue level: {max_input_queue}/{equipment.input_queue.capacity}")
    assert max_input_queue >= 3, "Input queue should fill due to bottleneck"
    
    # Check queue utilization
    avg_input_queue = sum(ql["input_queue"] for ql in queue_levels) / len(queue_levels)
    print(f"Average input queue level: {avg_input_queue:.2f}")
    
    # Check for blocking (input queue full)
    blocking_samples = sum(1 for ql in queue_levels 
                          if ql["input_queue"] >= equipment.input_queue.capacity)
    print(f"Blocking occurrences: {blocking_samples}/{len(queue_levels)}")
    
    print("\n✓ Queue dynamics test passed")
    return True


def test_state_transitions():
    """Test equipment state transitions."""
    print("\n" + "="*60)
    print("Testing State Transitions")
    print("="*60)
    
    env = simpy.Environment()
    
    # Create equipment with various conditions to trigger states
    equipment_config = PrimitiveConfig(
        id="STATE-EQUIP",
        type="EquipmentPrimitiveV2",
        properties={
            "base_rate": 10.0,
            "internal_queue_size": 5,
            "performance_factor": 0.9,
            "scrap_rate": 0.05,
            "micro_stop_probability": 0.5,  # High failure rate
            "micro_stop_frequency": 0.1,
            "warmup_period": 1.0  # Include warmup
        }
    )
    
    equipment = EquipmentPrimitiveV2(env, equipment_config)
    
    # Create intermittent source to cause starvation
    source = SourcePrimitiveV2(env, PrimitiveConfig(
        id="STATE-SOURCE",
        type="SourcePrimitiveV2",
        properties={
            "order_mode": False,  # Continuous generation
            "arrival_rate": 2.5,  # Batch equivalent
            "batch_size": 5,
            "warmup_period": 0.0
        }
    ))
    
    # Create sink
    sink = SinkPrimitiveV2(env, PrimitiveConfig(
        id="STATE-SINK",
        type="SinkPrimitiveV2",
        properties={}
    ))
    
    # Wire connections
    source.set_downstream(equipment.input_queue)
    equipment.downstream_equipment = sink
    sink.set_upstream(equipment.output_queue)
    
    # Start processes
    source.process = env.process(source.run())
    equipment.process = env.process(equipment.run())
    sink.process = env.process(sink.run())
    
    # Run simulation
    env.run(until=20)
    
    # Check state durations
    print("\nState durations:")
    total_time = sum(equipment.state_durations.values())
    
    for state, duration in equipment.state_durations.items():
        percentage = (duration / total_time * 100) if total_time > 0 else 0
        print(f"  {state.value}: {duration:.2f} min ({percentage:.1f}%)")
    
    # Verify multiple states were visited
    states_visited = sum(1 for duration in equipment.state_durations.values() if duration > 0)
    print(f"\nStates visited: {states_visited}")
    assert states_visited >= 3, "Equipment should visit multiple states"
    
    # Check for expected states
    from twin_model.primitives.equipment import EquipmentState
    
    assert equipment.state_durations[EquipmentState.RUNNING] > 0, "Should have running time"
    assert equipment.state_durations[EquipmentState.STARVED] > 0, "Should experience starvation"
    
    print("\n✓ State transitions test passed")
    return True


def test_no_immediate_starvation():
    """Test that equipment doesn't immediately starve at startup."""
    print("\n" + "="*60)
    print("Testing No Immediate Starvation")
    print("="*60)
    
    env = simpy.Environment()
    
    # Create line with initial WIP
    source_config = PrimitiveConfig(
        id="WIP-SOURCE",
        type="SourcePrimitiveV2",
        properties={
            "order_mode": False,  # Continuous generation
            "arrival_rate": 10.0,
            "initial_wip": True,  # Start with WIP
            "initial_wip_amount": 5,
            "warmup_period": 0.0
        }
    )
    
    equipment_config = PrimitiveConfig(
        id="WIP-EQUIP",
        type="EquipmentPrimitiveV2",
        properties={
            "base_rate": 10.0,
            "internal_queue_size": 10,
            "performance_factor": 1.0,
            "scrap_rate": 0.0,
            "micro_stop_probability": 0.0,
            "warmup_period": 0.0
        }
    )
    
    source = SourcePrimitiveV2(env, source_config)
    equipment = EquipmentPrimitiveV2(env, equipment_config)
    sink = SinkPrimitiveV2(env, PrimitiveConfig(
        id="WIP-SINK",
        type="SinkPrimitiveV2",
        properties={}
    ))
    
    source.set_downstream(equipment.input_queue)
    equipment.downstream_equipment = sink
    sink.set_upstream(equipment.output_queue)
    
    # Track early state
    early_states = []
    
    def monitor_early_state(env, equipment, early_states):
        """Monitor state in first minute."""
        while env.now < 1.0:
            early_states.append({
                "time": env.now,
                "state": equipment.state.value,
                "input_queue": len(equipment.input_queue.items)
            })
            yield env.timeout(0.1)
    
    # Start processes
    source.process = env.process(source.run())
    equipment.process = env.process(equipment.run())
    sink.process = env.process(sink.run())
    env.process(monitor_early_state(env, equipment, early_states))
    
    # Run for short time
    env.run(until=1)
    
    # Check early states
    print(f"\nEarly state samples: {len(early_states)}")
    
    # Count starvation in first minute
    starved_count = sum(1 for s in early_states if s["state"] == "STARVED")
    starved_percentage = (starved_count / len(early_states) * 100) if early_states else 0
    
    print(f"Starvation in first minute: {starved_percentage:.1f}%")
    print(f"Initial queue levels: {[s['input_queue'] for s in early_states[:5]]}")
    
    # Should have minimal starvation with initial WIP
    assert starved_percentage < 50, "Too much early starvation despite initial WIP"
    
    print("\n✓ No immediate starvation test passed")
    return True


def test_bottleneck_identification():
    """Test identification of bottleneck equipment."""
    print("\n" + "="*60)
    print("Testing Bottleneck Identification")
    print("="*60)
    
    env = simpy.Environment()
    
    # Create line with clear bottleneck
    equipment_configs = [
        PrimitiveConfig(
            id="FAST-EQUIP-1",
            type="EquipmentPrimitiveV2",
            properties={
                "base_rate": 20.0,  # Fast
                "internal_queue_size": 10,
                "performance_factor": 0.95,
                "scrap_rate": 0.02,
                "micro_stop_probability": 0.05,
                "warmup_period": 0.0
            }
        ),
        PrimitiveConfig(
            id="BOTTLENECK-EQUIP",
            type="EquipmentPrimitiveV2",
            properties={
                "base_rate": 8.0,  # Slow - bottleneck
                "internal_queue_size": 10,
                "performance_factor": 0.90,
                "scrap_rate": 0.03,
                "micro_stop_probability": 0.1,
                "warmup_period": 0.0
            }
        ),
        PrimitiveConfig(
            id="FAST-EQUIP-2",
            type="EquipmentPrimitiveV2",
            properties={
                "base_rate": 15.0,  # Fast
                "internal_queue_size": 10,
                "performance_factor": 0.92,
                "scrap_rate": 0.02,
                "micro_stop_probability": 0.05,
                "warmup_period": 0.0
            }
        )
    ]
    
    # Create equipment
    equipment_list = []
    for config in equipment_configs:
        equipment_list.append(EquipmentPrimitiveV2(env, config))
    
    # Create source and sink
    source = SourcePrimitiveV2(env, PrimitiveConfig(
        id="BOTTLE-SOURCE",
        type="SourcePrimitiveV2",
        properties={
            "order_mode": False,  # Continuous generation
            "arrival_rate": 25.0,  # Faster than line
            "warmup_period": 0.0
        }
    ))
    
    sink = SinkPrimitiveV2(env, PrimitiveConfig(
        id="BOTTLE-SINK",
        type="SinkPrimitiveV2",
        properties={}
    ))
    
    # Wire connections
    source.set_downstream(equipment_list[0].input_queue)
    for i in range(len(equipment_list) - 1):
        equipment_list[i].connect_to(equipment_list[i + 1])
    equipment_list[-1].downstream_equipment = sink
    sink.set_upstream(equipment_list[-1].output_queue)
    
    # Start processes
    source.process = env.process(source.run())
    for eq in equipment_list:
        eq.process = env.process(eq.run())
    sink.process = env.process(sink.run())
    
    # Run simulation
    env.run(until=30)
    
    # Analyze bottleneck indicators
    print("\nBottleneck Analysis:")
    
    for eq in equipment_list:
        # Calculate utilization
        running_time = eq.state_durations.get(
            EquipmentState.RUNNING, 0
        )
        total_time = env.now
        utilization = (running_time / total_time * 100) if total_time > 0 else 0
        
        # Calculate queue statistics
        queue_status = eq.get_queue_status()
        
        print(f"\n{eq.id}:")
        print(f"  Base rate: {eq.base_rate} units/min")
        print(f"  Utilization: {utilization:.1f}%")
        print(f"  Input queue avg: {queue_status['input_utilization']:.2f}")
        print(f"  Output queue avg: {queue_status['output_utilization']:.2f}")
        print(f"  Units produced: {eq.units_produced}")
        
        # Bottleneck should have high utilization and full input queue
        if eq.id == "BOTTLENECK-EQUIP":
            assert utilization > 70, "Bottleneck should have high utilization"
            assert queue_status['input_utilization'] > 0.5, "Bottleneck should have full input queue"
    
    print("\n✓ Bottleneck identification test passed")
    return True


def main():
    """Run all material flow tests."""
    print("\n" + "="*60)
    print("MATERIAL FLOW INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Basic Material Flow", test_basic_material_flow),
        ("Queue Dynamics", test_queue_dynamics),
        ("State Transitions", test_state_transitions),
        ("No Immediate Starvation", test_no_immediate_starvation),
        ("Bottleneck Identification", test_bottleneck_identification)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"MATERIAL FLOW TEST SUMMARY")
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("✓ ALL MATERIAL FLOW TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)