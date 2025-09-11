#!/usr/bin/env python
"""Test buffer integration with production line."""

import simpy
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder
from twin_model.primitives import AccumulationBuffer

def test_buffer_integration():
    """Test that buffers are properly integrated in the production line."""
    
    print("=" * 80)
    print("BUFFER INTEGRATION TEST")
    print("=" * 80)
    
    # Create environment
    env = simpy.Environment()
    
    # Build model
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=Path("ontology/filling_line_ontology.yaml"),
        manifest_path=Path("manifests/equipment_manifest.yaml"),
        config_path=Path("config/calibrated_parameters.yaml")
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    connections = builder.connections
    
    print(f"\n✅ Model built with {len(primitives)} primitives")
    print(f"\n🔗 Connections: {len(connections)}")
    for conn in connections:
        print(f"  - {conn['from']} -> {conn['to']}")
    
    # Check for buffers
    buffers = {k: v for k, v in primitives.items() if isinstance(v, AccumulationBuffer)}
    print(f"\n📦 Found {len(buffers)} buffer(s):")
    for buffer_id, buffer in buffers.items():
        print(f"  - {buffer_id}: capacity={buffer.buffer.capacity}, mode={buffer.buffer_params.mode.value}")
    
    # Check LINE1 buffer specifically
    if "LINE1-BUF-FIL-PCK" in buffers:
        line1_buffer = buffers["LINE1-BUF-FIL-PCK"]
        print(f"\n✅ LINE1 buffer found:")
        print(f"  - Capacity: {line1_buffer.buffer.capacity} units")
        print(f"  - Warning levels: {line1_buffer.buffer_params.warning_level_low*100:.0f}% - {line1_buffer.buffer_params.warning_level_high*100:.0f}%")
        print(f"  - Max dwell time: {line1_buffer.buffer_params.max_dwell_time} minutes")
    else:
        print("\n⚠️ LINE1-BUF-FIL-PCK not found in primitives")
    
    # Run for short time
    print("\n" + "-" * 80)
    print("RUNNING 60 MINUTE TEST WITH BUFFER")
    print("-" * 80)
    
    env.run(until=60)
    
    # Check buffer metrics
    if "LINE1-BUF-FIL-PCK" in buffers:
        metrics = line1_buffer.get_metrics()
        print(f"\n📊 Buffer Metrics after 60 minutes:")
        print(f"  - Current level: {metrics['buffer_level']:.1f} units")
        print(f"  - Fill percentage: {metrics['fill_percentage']*100:.1f}%")
        print(f"  - Total flow in: {metrics['total_flow_in']:.0f} units")
        print(f"  - Total flow out: {metrics['total_flow_out']:.0f} units")
        print(f"  - Overflow events: {metrics['overflow_events']}")
        print(f"  - Underflow events: {metrics['underflow_events']}")
        print(f"  - Low warnings: {metrics['warning_events_low']}")
        print(f"  - High warnings: {metrics['warning_events_high']}")
    
    # Check production through LINE1
    line1_sink = primitives.get("LINE1-SINK")
    if line1_sink and hasattr(line1_sink, 'total_collected'):
        print(f"\n📈 LINE1 Production: {line1_sink.total_collected:,.0f} units")
    
    return buffers

if __name__ == "__main__":
    try:
        buffers = test_buffer_integration()
        print("\n" + "=" * 80)
        if buffers:
            print("✅ Buffer integration successful!")
        else:
            print("⚠️ No buffers found - check configuration")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()