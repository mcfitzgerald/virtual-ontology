"""Test script to run the simulation and verify material flow."""

import simpy
from pathlib import Path
from twin_model.model_builder_ontology import OntologyDrivenModelBuilder
from twin_model.transduction import FlowTransducer
from twin_model.monitoring import FlowMonitor

def run_simulation(duration: float = 1.0) -> dict:
    """Run a simple simulation to test material flow.
    
    Args:
        duration: Simulation duration in minutes
        
    Returns:
        Dictionary with results
    """
    # Create environment
    env = simpy.Environment()
    
    # Build model from ontology
    builder = OntologyDrivenModelBuilder(env)
    primitives = builder.build_from_ontology()
    
    print(f"Created {len(primitives)} primitives:")
    for name, primitive in primitives.items():
        print(f"  - {name}: {type(primitive).__name__}")
    
    # Create transducer and monitor
    transducer = FlowTransducer(env)
    monitor = FlowMonitor(env, monitor_interval=0.1)
    
    # Register primitives with transducer
    for name, primitive in primitives.items():
        transducer.register_primitive(name, primitive)
    
    # Register transducer with monitor
    monitor.register_transducer(transducer)
    
    # Start all primitives
    for name, primitive in primitives.items():
        if hasattr(primitive, 'start'):
            primitive.start()
            print(f"Started: {name}")
    
    # Run simulation
    print(f"\nRunning simulation for {duration} minutes...")
    env.run(until=duration)
    
    # Collect results
    results = {
        "primitives": len(primitives),
        "simulation_time": env.now,
        "production": {}
    }
    
    # Check production for each line
    for name, primitive in primitives.items():
        if "SINK" in name:
            if hasattr(primitive, 'total_collected'):
                results["production"][name] = primitive.total_collected
                print(f"{name}: {primitive.total_collected:.2f} units collected")
            
        if "SOURCE" in name:
            if hasattr(primitive, 'flow_metrics'):
                print(f"{name}: {primitive.flow_metrics.total_output:.2f} units generated")
    
    # Get OEE from sinks
    for name, primitive in primitives.items():
        if "SINK" in name and hasattr(primitive, 'calculate_oee'):
            oee_metrics = primitive.calculate_oee(duration)
            if oee_metrics:
                print(f"\n{name} OEE Metrics:")
                print(f"  OEE: {oee_metrics.oee:.1%}")
                print(f"  Availability: {oee_metrics.availability:.1%}")
                print(f"  Performance: {oee_metrics.performance:.1%}")
                print(f"  Quality: {oee_metrics.quality:.1%}")
    
    return results

if __name__ == "__main__":
    # Run short test
    results = run_simulation(duration=0.5)
    
    # Check if production is happening
    total_production = sum(results["production"].values())
    if total_production > 0:
        print(f"\n✅ SUCCESS: Production is working! Total: {total_production:.2f} units")
    else:
        print("\n❌ FAILURE: No production detected")
        print("Debugging information:")
        print(f"  - Primitives created: {results['primitives']}")
        print(f"  - Simulation ran for: {results['simulation_time']} minutes")