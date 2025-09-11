#!/usr/bin/env python
"""Debug buffer integration with detailed logging."""

import logging
import simpy
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder
from twin_model.primitives import AccumulationBuffer

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('buffer_debug.log'),
        logging.StreamHandler()
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger('twin_model.primitives.buffer_flow').setLevel(logging.DEBUG)
logging.getLogger('twin_model.ontology_model_builder').setLevel(logging.INFO)

def test_buffer_debug():
    """Test buffer integration with detailed logging."""
    
    print("=" * 80)
    print("BUFFER DEBUG TEST")
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
    
    print("\n🔧 Building model...")
    model = builder.build_model()
    primitives = model['primitives']
    
    print(f"\n✅ Model built with {len(primitives)} primitives")
    
    # Check for LINE1 buffer specifically
    if "LINE1-BUF-FIL-PCK" in primitives:
        buffer = primitives["LINE1-BUF-FIL-PCK"]
        print(f"\n📦 LINE1 Buffer found:")
        print(f"  - Type: {type(buffer).__name__}")
        print(f"  - Has downstream: {buffer.downstream is not None}")
        if buffer.downstream:
            print(f"  - Downstream type: {type(buffer.downstream).__name__}")
            print(f"  - Downstream ID: {getattr(buffer.downstream, 'equipment_id', 'unknown')}")
    
    # Run for very short time with detailed logging
    print("\n" + "-" * 80)
    print("RUNNING 5 MINUTE TEST WITH DEBUG LOGGING")
    print("-" * 80)
    
    try:
        env.run(until=5)
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check buffer metrics
    if "LINE1-BUF-FIL-PCK" in primitives:
        buffer = primitives["LINE1-BUF-FIL-PCK"]
        metrics = buffer.get_metrics()
        print(f"\n📊 Buffer Metrics after 5 minutes:")
        print(f"  - Current level: {metrics['buffer_level']:.1f} units")
        print(f"  - Total flow in: {metrics['total_flow_in']:.0f} units")
        print(f"  - Total flow out: {metrics['total_flow_out']:.0f} units")
        
        # Check downstream equipment
        if buffer.downstream:
            print(f"\n🔍 Downstream equipment check:")
            print(f"  - Has input_buffer: {hasattr(buffer.downstream, 'input_buffer')}")
            print(f"  - Has input_container: {hasattr(buffer.downstream, 'input_container')}")
            if hasattr(buffer.downstream, 'input_buffer'):
                input_buf = buffer.downstream.input_buffer
                print(f"  - Input buffer type: {type(input_buf).__name__}")
                print(f"  - Is same as buffer.buffer: {input_buf is buffer.buffer}")
    
    print("\n" + "=" * 80)
    print("Check buffer_debug.log for detailed logging")
    print("=" * 80)

if __name__ == "__main__":
    test_buffer_debug()