#!/usr/bin/env python
"""Comprehensive test of buffer functionality in production line."""

import simpy
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder
from twin_model.primitives import AccumulationBuffer

def test_buffer_comprehensive():
    """Comprehensive test of buffer integration and functionality."""
    
    print("=" * 80)
    print("COMPREHENSIVE BUFFER TEST")
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
    
    print(f"\n✅ Model built with {len(primitives)} primitives")
    
    # Get all buffers
    buffers = {k: v for k, v in primitives.items() if isinstance(v, AccumulationBuffer)}
    print(f"\n📦 Buffers in system: {len(buffers)}")
    for buffer_id in buffers:
        print(f"  - {buffer_id}")
    
    # Run simulation
    test_duration = 120  # 2 hours
    print(f"\n🏭 Running {test_duration} minute simulation...")
    env.run(until=test_duration)
    
    # Analyze buffer performance
    print("\n" + "=" * 80)
    print("BUFFER PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    for buffer_id, buffer in buffers.items():
        metrics = buffer.get_metrics()
        print(f"\n📊 {buffer_id}:")
        print(f"  Configuration:")
        print(f"    - Capacity: {buffer.flow_capacity.internal_capacity} units")
        print(f"    - Mode: {buffer.buffer_params.mode.value}")
        print(f"    - Warning levels: {buffer.buffer_params.warning_level_low*100:.0f}%-{buffer.buffer_params.warning_level_high*100:.0f}%")
        print(f"    - Max dwell time: {buffer.buffer_params.max_dwell_time} minutes")
        
        print(f"  Performance:")
        print(f"    - Current level: {metrics['buffer_level']:.1f} units ({metrics['fill_percentage']*100:.1f}%)")
        print(f"    - Total flow in: {metrics['total_flow_in']:.0f} units")
        print(f"    - Total flow out: {metrics['total_flow_out']:.0f} units")
        print(f"    - Flow efficiency: {metrics['total_flow_out']/metrics['total_flow_in']*100:.1f}%" if metrics['total_flow_in'] > 0 else "N/A")
        
        print(f"  Events:")
        print(f"    - Overflow events: {metrics['overflow_events']}")
        print(f"    - Underflow events: {metrics['underflow_events']}")
        print(f"    - Low warnings: {metrics['warning_events_low']}")
        print(f"    - High warnings: {metrics['warning_events_high']}")
        
        print(f"  Status:")
        print(f"    - State: {metrics['state']}")
        print(f"    - Utilization: {metrics['utilization']:.1f}%")
        print(f"    - Availability: {metrics['availability']:.1f}%")
    
    # Analyze production lines
    print("\n" + "=" * 80)
    print("PRODUCTION LINE ANALYSIS")
    print("=" * 80)
    
    for line_num in [1, 2, 3]:
        line_id = f"LINE{line_num}"
        sink_id = f"{line_id}-SINK"
        
        if sink_id in primitives:
            sink = primitives[sink_id]
            if hasattr(sink, 'total_collected'):
                production = sink.total_collected
                rate = production / test_duration
                print(f"\n📈 {line_id}:")
                print(f"  - Total production: {production:,.0f} units")
                print(f"  - Production rate: {rate:.1f} units/min")
                
                # Check if this line has a buffer
                buffer_id = f"{line_id}-BUF-FIL-PCK"
                if buffer_id in buffers:
                    buffer = buffers[buffer_id]
                    metrics = buffer.get_metrics()
                    print(f"  - Buffer impact:")
                    print(f"    - Flow smoothing: {metrics['total_flow_in']:,.0f} → {metrics['total_flow_out']:,.0f} units")
                    print(f"    - Buffer utilization: {metrics['utilization']:.1f}%")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_buffer_flow_in = sum(b.get_metrics()['total_flow_in'] for b in buffers.values())
    total_buffer_flow_out = sum(b.get_metrics()['total_flow_out'] for b in buffers.values())
    total_production = sum(
        primitives[f"LINE{i}-SINK"].total_collected 
        for i in [1, 2, 3] 
        if f"LINE{i}-SINK" in primitives and hasattr(primitives[f"LINE{i}-SINK"], 'total_collected')
    )
    
    print(f"\n✅ Buffer System Performance:")
    print(f"  - Total buffer throughput: {total_buffer_flow_in:,.0f} units in, {total_buffer_flow_out:,.0f} units out")
    print(f"  - Overall flow efficiency: {total_buffer_flow_out/total_buffer_flow_in*100:.1f}%" if total_buffer_flow_in > 0 else "N/A")
    print(f"  - Total production: {total_production:,.0f} units")
    print(f"  - Average production rate: {total_production/test_duration:.1f} units/min")
    
    return buffers, total_production

if __name__ == "__main__":
    try:
        buffers, production = test_buffer_comprehensive()
        print("\n" + "=" * 80)
        if buffers and production > 0:
            print("✅ BUFFER SYSTEM OPERATIONAL AND EFFECTIVE")
        else:
            print("⚠️ CHECK BUFFER CONFIGURATION")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()