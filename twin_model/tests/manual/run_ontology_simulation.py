#!/usr/bin/env python3
"""Run simulation using ontology-driven model builder."""

import logging
import simpy
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_simulation(duration: float = 10.0) -> None:
    """Run the ontology-driven simulation.
    
    Args:
        duration: Simulation duration in minutes
    """
    # Create SimPy environment
    env = simpy.Environment()
    
    # Define paths
    project_root = Path(__file__).parent
    ontology_path = project_root / "ontology" / "filling_line_ontology.yaml"
    manifest_path = project_root / "manifests" / "equipment_instances.yaml"
    config_path = project_root / "config" / "tunable_parameters.yaml"
    
    # Build model
    logger.info("Building model from ontology, manifest, and config...")
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_path=manifest_path,
        config_path=config_path
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    lines = model['lines']
    
    logger.info(f"Model built with {len(primitives)} equipment pieces")
    logger.info(f"Production lines: {list(lines.keys())}")
    
    # Run simulation
    logger.info(f"Starting simulation for {duration} minutes...")
    
    # Print initial state
    print("\n" + "=" * 60)
    print("INITIAL STATE")
    print("=" * 60)
    for line_id, equipment_ids in lines.items():
        print(f"\nLine {line_id}:")
        for eq_id in equipment_ids:
            equipment = primitives[eq_id]
            print(f"  {eq_id}: {equipment.current_state}")
    
    # Run with periodic reporting
    report_interval = duration / 5  # Report 5 times during simulation
    
    for i in range(5):
        env.run(until=(i + 1) * report_interval)
        
        print("\n" + "=" * 60)
        print(f"STATE AT {env.now:.1f} MINUTES")
        print("=" * 60)
        
        # Get metrics
        metrics = builder.get_metrics()
        
        for line_id, equipment_ids in lines.items():
            print(f"\nLine {line_id}:")
            for eq_id in equipment_ids:
                equipment = primitives[eq_id]
                eq_metrics = metrics.get(eq_id, {})
                
                print(f"  {eq_id}:")
                print(f"    State: {equipment.current_state}")
                print(f"    Total Input: {eq_metrics.get('total_input', 0):.1f}")
                print(f"    Total Output: {eq_metrics.get('total_output', 0):.1f}")
                
                if hasattr(equipment, 'total_collected'):
                    print(f"    Total Collected: {equipment.total_collected:.1f}")
                
                if eq_metrics.get('total_scrap', 0) > 0:
                    print(f"    Total Scrap: {eq_metrics.get('total_scrap', 0):.1f}")
    
    # Calculate OEE for equipment
    print("\n" + "=" * 60)
    print("OVERALL EQUIPMENT EFFECTIVENESS (OEE)")
    print("=" * 60)
    
    for eq_id in ["LINE1-FIL", "LINE1-PCK", "LINE1-PAL"]:
        if eq_id in primitives:
            equipment = primitives[eq_id]
            
            # Calculate OEE components
            # Availability = (Total Time - Downtime) / Total Time
            total_time = env.now
            downtime = equipment.flow_metrics.total_downtime if hasattr(equipment, 'flow_metrics') else 0
            availability = (total_time - downtime) / total_time if total_time > 0 else 0
            
            # Performance = Actual Output / (Nominal Rate * Running Time)
            actual_output = equipment.flow_metrics.total_output if hasattr(equipment, 'flow_metrics') else 0
            nominal_rate = equipment.processing.nominal_rate if hasattr(equipment, 'processing') else 0
            running_time = total_time - downtime
            expected_output = nominal_rate * running_time
            performance = actual_output / expected_output if expected_output > 0 else 0
            
            # Quality = Good Output / Total Output
            total_output = actual_output + (equipment.flow_metrics.total_scrap if hasattr(equipment, 'flow_metrics') else 0)
            quality = actual_output / total_output if total_output > 0 else 0
            
            # OEE = Availability * Performance * Quality
            oee = availability * performance * quality
            
            print(f"\n{eq_id}:")
            print(f"  Availability: {availability:.1%}")
            print(f"  Performance: {performance:.1%}")
            print(f"  Quality: {quality:.1%}")
            print(f"  OEE: {oee:.1%}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("SIMULATION SUMMARY")
    print("=" * 60)
    
    sink = primitives.get("LINE1-SINK")
    if sink and hasattr(sink, 'total_collected'):
        print(f"Total Production: {sink.total_collected:.1f} units")
        print(f"Production Rate: {sink.total_collected / env.now:.1f} units/minute")
        
        if sink.total_collected > 0:
            print("\n✅ SIMULATION SUCCESSFUL - Production confirmed!")
        else:
            print("\n❌ SIMULATION FAILED - No production!")
    else:
        print("❌ No sink found or no collection data!")


if __name__ == "__main__":
    run_simulation(duration=10.0)