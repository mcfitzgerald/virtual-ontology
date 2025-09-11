#!/usr/bin/env python
"""Integration test for changeover matrix with production line."""

import logging
import simpy
import yaml
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder
from twin_model.primitives import ChangeoverMatrix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_changeover_integration():
    """Test changeover matrix integration with production system."""
    
    print("=" * 80)
    print("CHANGEOVER MATRIX INTEGRATION TEST")
    print("=" * 80)
    
    # Load changeover matrix configuration
    with open("config/changeover_matrix.yaml", "r") as f:
        changeover_config = yaml.safe_load(f)
    
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
    
    # Add changeover matrices to equipment
    filler_matrix_config = changeover_config['changeover_matrices']['filler_matrix']
    filler_matrix = ChangeoverMatrix(
        matrix=filler_matrix_config['matrix'],
        default_time=filler_matrix_config['default_time'],
        min_changeover_time=filler_matrix_config['min_changeover_time'],
        track_patterns=filler_matrix_config['track_patterns']
    )
    
    packer_matrix_config = changeover_config['changeover_matrices']['packer_matrix']
    packer_matrix = ChangeoverMatrix(
        matrix=packer_matrix_config['matrix'],
        default_time=packer_matrix_config['default_time'],
        min_changeover_time=packer_matrix_config['min_changeover_time'],
        track_patterns=packer_matrix_config['track_patterns']
    )
    
    # Apply matrices to LINE1 equipment
    for equip_id, primitive in primitives.items():
        if "LINE1-FIL" in equip_id:
            primitive.changeover_matrix = filler_matrix
            print(f"  - Added filler matrix to {equip_id}")
        elif "LINE1-PCK" in equip_id:
            primitive.changeover_matrix = packer_matrix
            print(f"  - Added packer matrix to {equip_id}")
    
    # Simulate production schedule with changeovers
    schedule = changeover_config['example_schedule']
    
    def production_scheduler():
        """Execute production schedule with product changes."""
        for i, batch in enumerate(schedule):
            product = batch['product']
            duration = batch['duration']
            
            print(f"\n📦 Starting batch {i+1}: {product} for {duration} minutes")
            
            # Request product change on all LINE1 equipment
            for equip_id, primitive in primitives.items():
                if "LINE1" in equip_id and hasattr(primitive, 'request_product_change'):
                    primitive.request_product_change(product)
            
            # Run production for specified duration
            yield env.timeout(duration)
            
            # Collect changeover metrics
            print(f"\n📊 Changeover metrics after batch {i+1}:")
            for equip_id, primitive in primitives.items():
                if "LINE1" in equip_id and hasattr(primitive, 'get_changeover_metrics'):
                    metrics = primitive.get_changeover_metrics()
                    if metrics['changeover_count'] > 0:
                        print(f"  {equip_id}:")
                        print(f"    - Changeovers: {metrics['changeover_count']}")
                        print(f"    - Total time: {metrics['total_changeover_time']:.1f} min")
                        print(f"    - Average time: {metrics['avg_changeover_time']:.1f} min")
    
    # Start scheduler
    env.process(production_scheduler())
    
    # Run simulation
    total_time = sum(batch['duration'] for batch in schedule)
    print(f"\n⏱️ Running simulation for {total_time} minutes...")
    env.run(until=total_time)
    
    # Final results
    print("\n" + "=" * 80)
    print("FINAL CHANGEOVER SUMMARY")
    print("=" * 80)
    
    total_changeover_time = 0
    total_changeover_count = 0
    
    for equip_id, primitive in primitives.items():
        if hasattr(primitive, 'get_changeover_metrics'):
            metrics = primitive.get_changeover_metrics()
            if metrics['changeover_count'] > 0:
                total_changeover_time += metrics['total_changeover_time']
                total_changeover_count += metrics['changeover_count']
                
                print(f"\n{equip_id}:")
                print(f"  - Total changeovers: {metrics['changeover_count']}")
                print(f"  - Total changeover time: {metrics['total_changeover_time']:.1f} min")
                print(f"  - Average changeover time: {metrics['avg_changeover_time']:.1f} min")
                print(f"  - Current product: {metrics['current_product']}")
                
                if metrics['recent_changeovers']:
                    print(f"  - Recent changeovers:")
                    for change in metrics['recent_changeovers'][-3:]:  # Last 3
                        print(f"    * {change['from_product']} -> {change['to_product']}: {change['duration']:.1f} min")
    
    # Calculate changeover efficiency
    if total_changeover_count > 0:
        print(f"\n📈 Overall Statistics:")
        print(f"  - Total changeover time: {total_changeover_time:.1f} minutes")
        print(f"  - Total production time: {total_time:.1f} minutes")
        print(f"  - Changeover percentage: {(total_changeover_time/total_time)*100:.1f}%")
        
        # Check sink output
        for line_num in [1]:
            sink_id = f"LINE{line_num}-SINK"
            if sink_id in primitives and hasattr(primitives[sink_id], 'total_collected'):
                production = primitives[sink_id].total_collected
                print(f"  - LINE{line_num} production: {production:,.0f} units")
    
    return total_changeover_time, total_changeover_count

if __name__ == "__main__":
    try:
        changeover_time, changeover_count = test_changeover_integration()
        print("\n" + "=" * 80)
        if changeover_count > 0:
            print("✅ CHANGEOVER MATRIX INTEGRATION SUCCESSFUL")
            print(f"   Completed {changeover_count} changeovers")
        else:
            print("⚠️ NO CHANGEOVERS DETECTED")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()