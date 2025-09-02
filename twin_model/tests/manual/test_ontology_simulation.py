"""Test script for ontology-driven simulation."""

import logging
import simpy
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder
from twin_model.transduction import FlowTransducer
from twin_model.monitoring import FlowMonitor

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')


def run_ontology_simulation(duration: float = 10.0) -> dict:
    """Run simulation using ontology-driven model builder.
    
    Args:
        duration: Simulation duration in minutes
        
    Returns:
        Dictionary with results
    """
    print("=" * 60)
    print("ONTOLOGY-DRIVEN SIMULATION TEST")
    print("=" * 60)
    
    # Create environment
    env = simpy.Environment()
    
    # Define paths
    project_root = Path(__file__).parent
    ontology_path = project_root / "ontology" / "filling_line_ontology.yaml"
    manifest_path = project_root / "manifests" / "equipment_instances.yaml"
    config_path = project_root / "config" / "tunable_parameters.yaml"
    
    print(f"\nLoading configuration:")
    print(f"  Ontology: {ontology_path.name}")
    print(f"  Manifest: {manifest_path.name}")
    print(f"  Config: {config_path.name}")
    
    # Build model using ontology
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_path=manifest_path,
        config_path=config_path
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    lines = model['lines']
    
    print(f"\nModel built successfully:")
    print(f"  Primitives: {len(primitives)}")
    print(f"  Lines: {len(lines)}")
    
    # Show equipment by line
    for line_id, equipment_ids in lines.items():
        print(f"\n{line_id}:")
        for eq_id in equipment_ids:
            equipment = primitives[eq_id]
            eq_type = getattr(equipment, 'equipment_type', 'Unknown')
            print(f"  - {eq_id}: {eq_type}")
    
    # Create transducer and monitor
    transducer = FlowTransducer()
    monitor = FlowMonitor(env)
    
    # Register primitives with monitor (if needed)
    # Note: FlowMonitor may not need explicit registration
    
    # Run simulation
    print(f"\nRunning simulation for {duration} minutes...")
    print("-" * 40)
    
    # Run for short intervals and show progress
    intervals = 5
    interval_duration = duration / intervals
    
    for i in range(intervals):
        env.run(until=(i + 1) * interval_duration)
        
        # Get metrics
        metrics = builder.get_metrics()
        
        # Show progress for each line
        print(f"\nTime: {env.now:.1f} minutes")
        for line_id in lines:
            line_equipment = [eq for eq in lines[line_id]]
            
            # Get source output
            source_id = f"{line_id}-SOURCE"
            if source_id in metrics:
                source_output = metrics[source_id].get('total_output', 0)
                print(f"  {line_id} Source output: {source_output:.1f} units")
            
            # Get sink input
            sink_id = f"{line_id}-SINK"
            if sink_id in metrics:
                sink_input = metrics[sink_id].get('total_input', 0)
                print(f"  {line_id} Sink collected: {sink_input:.1f} units")
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    # Final metrics
    final_metrics = builder.get_metrics()
    results = {
        'simulation_time': env.now,
        'lines': {},
        'total_production': 0
    }
    
    for line_id in lines:
        source_id = f"{line_id}-SOURCE"
        sink_id = f"{line_id}-SINK"
        
        source_output = 0
        sink_collected = 0
        
        if source_id in final_metrics:
            source_output = final_metrics[source_id].get('total_output', 0)
        
        if sink_id in primitives:
            sink = primitives[sink_id]
            if hasattr(sink, 'total_collected'):
                sink_collected = sink.total_collected
            
            # Calculate OEE
            if hasattr(sink, 'calculate_oee'):
                oee_metrics = sink.calculate_oee(duration)
                if oee_metrics:
                    oee, availability, performance, quality = oee_metrics
                    print(f"\n{line_id} OEE Metrics:")
                    print(f"  Generated: {source_output:.1f} units")
                    print(f"  Collected: {sink_collected:.1f} units")
                    print(f"  OEE: {oee:.1%}")
                    print(f"  Availability: {availability:.1%}")
                    print(f"  Performance: {performance:.1%}")
                    print(f"  Quality: {quality:.1%}")
                    
                    results['lines'][line_id] = {
                        'generated': source_output,
                        'collected': sink_collected,
                        'oee': oee,
                        'availability': availability,
                        'performance': performance,
                        'quality': quality
                    }
        
        results['total_production'] += sink_collected
    
    # Check equipment states
    print("\nEquipment States:")
    for equipment_id, equipment in primitives.items():
        if hasattr(equipment, 'current_state'):
            state = str(equipment.current_state).split('.')[-1]
            print(f"  {equipment_id}: {state}")
    
    # Summary
    print("\n" + "=" * 60)
    if results['total_production'] > 0:
        print(f"✅ SUCCESS: Production working! Total: {results['total_production']:.1f} units")
    else:
        print("❌ FAILURE: No production detected")
        print("\nDebugging Information:")
        
        # Check for common issues
        for equipment_id, metrics in final_metrics.items():
            if 'FIL' in equipment_id:
                state = metrics.get('state', 'UNKNOWN')
                if 'STARVED' in state:
                    print(f"  - {equipment_id} is STARVED (no input material)")
                elif 'BLOCKED' in state:
                    print(f"  - {equipment_id} is BLOCKED (output full)")
    
    return results


if __name__ == "__main__":
    # Run simulation
    results = run_ontology_simulation(duration=10.0)
    
    # Show summary
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print(f"Total production across all lines: {results['total_production']:.1f} units")
    print("=" * 60)