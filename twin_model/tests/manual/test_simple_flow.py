"""Simple test to debug flow issues."""

import simpy

from twin_model.primitives import (
    EquipmentFlow,
    FailureParameters,
    FlowCapacity,
    ProcessingParameters,
    SinkFlow,
    SourceFlow,
)


def test_simple_flow():
    """Test a simple source -> equipment -> sink flow."""
    env = simpy.Environment()

    # Create source
    source_capacity = FlowCapacity(100, 60, 1000, 0)
    source_config = {"name": "SOURCE", "continuous_mode": True, "default_product": "TEST"}
    source = SourceFlow(env, source_config, source_capacity, 60.0, 0.1)
    source.output_buffer = simpy.Container(env, 1000, init=0)

    # Create equipment
    eq_capacity = FlowCapacity(60, 50, 500, 0)
    eq_config = {"name": "EQUIPMENT"}
    processing = ProcessingParameters(50.0, 0.95, 1.0, 10.0, 0.1)
    failures = FailureParameters(1000.0, 10.0, 0, 0)  # No failures for test
    equipment = EquipmentFlow(env, eq_config, eq_capacity, processing, failures)

    # Wire: share buffer between source and equipment
    equipment.input_buffer = source.output_buffer  # Share the buffer!
    equipment.output_buffer = simpy.Container(env, 500, init=0)

    # Create sink
    sink_capacity = FlowCapacity(60, 60, 10000, 0)
    sink_config = {"name": "SINK", "nominal_rate": 50.0}
    sink = SinkFlow(env, sink_config, sink_capacity, 50.0, 0.1)

    # Wire: share buffer between equipment and sink
    sink.input_buffer = equipment.output_buffer  # Share the buffer!

    # Start processes
    source.start()
    equipment.start()
    sink.start()

    print("Initial state:")
    print(f"  Source output buffer: {source.output_buffer.level:.1f}/{source.output_buffer.capacity}")
    print(f"  Equipment input buffer: {equipment.input_buffer.level:.1f}/{equipment.input_buffer.capacity}")
    print(f"  Equipment internal buffer: {equipment.internal_buffer.level:.1f}/{equipment.internal_buffer.capacity}")
    print(f"  Equipment output buffer: {equipment.output_buffer.level:.1f}/{equipment.output_buffer.capacity}")
    print(f"  Sink input buffer: {sink.input_buffer.level:.1f}/{sink.input_buffer.capacity}")

    # Run for a short time
    for i in range(5):
        env.run(until=(i + 1) * 0.2)
        print(f"\nAfter {(i+1)*0.2:.1f} minutes:")
        print(f"  Source state: {source.current_state}")
        print(f"    Output buffer: {source.output_buffer.level:.1f}")
        print(f"    Total generated: {source.flow_metrics.total_output:.1f}")
        print(f"  Equipment state: {equipment.current_state}")
        print(f"    Input buffer: {equipment.input_buffer.level:.1f}")
        print(f"    Internal buffer: {equipment.internal_buffer.level:.1f}")
        print(f"    Output buffer: {equipment.output_buffer.level:.1f}")
        print(f"    Total processed: {equipment.flow_metrics.total_output:.1f}")
        print(f"  Sink state: {sink.current_state}")
        print(f"    Input buffer: {sink.input_buffer.level:.1f}")
        print(f"    Total collected: {sink.total_collected:.1f}")

    # Final check
    if sink.total_collected > 0:
        print(f"\n✅ SUCCESS: Flow working! Collected {sink.total_collected:.1f} units")
    else:
        print("\n❌ FAILURE: No flow detected")

        # Debug
        print("\nDebug info:")
        print(f"  Batch size: {equipment.processing.batch_size}")
        print(f"  Input buffer has material: {equipment.input_buffer.level}")
        print(f"  Input >= batch_size: {equipment.input_buffer.level >= equipment.processing.batch_size}")
        print(f"  Input buffer exists: {equipment.input_buffer is not None}")
        print(f"  Input buffer truthy: {bool(equipment.input_buffer)}")
        print(f"  Processing interval: {equipment.processing.processing_interval}")
        print(f"  Is failed: {equipment.is_failed}")


if __name__ == "__main__":
    test_simple_flow()
