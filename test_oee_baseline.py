#!/usr/bin/env python3
"""Test to achieve 40-65% baseline OEE.

This test configures the system with parameters that should achieve
a realistic baseline OEE of 40-65%, as is typical for manufacturing.
"""

import sys
from pathlib import Path
import simpy
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.model_builder import OntologyDrivenModelBuilderV2 as ModelBuilderV2
from twin_model.control.control_manager import ControlManager
from twin_model.primitives.equipment import EquipmentState

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def run_baseline_test():
    """Run simulation with baseline parameters for 40-65% OEE."""
    
    print("\n" + "="*80)
    print("BASELINE OEE TEST (Target: 40-65%)")
    print("="*80)
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    # Initialize control manager
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml"
    )
    
    # Create model builder
    builder = ModelBuilderV2(
        env=env,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr
    )
    
    # Build model
    model = builder.build_model()
    
    # Configure for baseline OEE (40-65% target)
    print("\nSetting baseline parameters:")
    print("  - Micro-stops: 10% probability per 5 min")
    print("  - Performance: 85% of theoretical")
    print("  - Quality: 95% (5% scrap)")
    print("  - MTBF: 480 min (8 hours)")
    print("  - MTTR: 30 min")
    
    for prim_id, prim in model['primitives'].items():
        if hasattr(prim, 'micro_stop_probability'):
            # Baseline parameters for 40-65% OEE
            prim.micro_stop_probability = 0.10  # 10% chance per 5 min
            prim.performance_factor = 0.85      # 85% speed
            prim.scrap_rate = 0.05              # 5% quality loss
            
            # Set in config for failure process
            prim.config.properties['mtbf'] = 480  # 8 hours
            prim.config.properties['mttr'] = 30   # 30 min
            prim.config.properties['minor_failure_probability'] = 0.01
            prim.config.properties['major_failure_probability'] = 0.005
    
    # Configure sources for stable generation
    for primitive in model['primitives'].values():
        if hasattr(primitive, 'order_mode'):
            primitive.order_mode = False
            primitive.arrival_rate = 90  # Slightly above equipment capacity
            primitive.disruption_probability = 0.01  # 1% chance
    
    # Start processes
    for primitive in model['primitives'].values():
        if hasattr(primitive, 'start'):
            primitive.start()
    
    # Run simulation
    duration = 480  # 8 hours for stable results
    print(f"\nRunning {duration} minute simulation...")
    env.run(until=duration)
    
    # Finalize state durations
    for primitive in model['primitives'].values():
        if hasattr(primitive, 'state_durations') and hasattr(primitive, 'state'):
            if hasattr(primitive, 'state_start_time'):
                remaining_duration = env.now - primitive.state_start_time
                primitive.state_durations[primitive.state] += remaining_duration
    
    # Calculate and display OEE
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    oee_values = []
    
    for line_id in ['LINE1', 'LINE2', 'LINE3']:
        print(f"\n{line_id}:")
        line = model['lines'][line_id]
        
        for eq_entity in line.equipment:
            eq_id = eq_entity.entity_id
            if eq_id in model['primitives']:
                eq = model['primitives'][eq_id]
                
                # Get state times
                running_time = eq.state_durations.get(EquipmentState.RUNNING, 0)
                stopped_time = eq.state_durations.get(EquipmentState.STOPPED_FAILURE, 0)
                idle_time = eq.state_durations.get(EquipmentState.IDLE, 0)
                starved_time = eq.state_durations.get(EquipmentState.STARVED, 0)
                blocked_time = eq.state_durations.get(EquipmentState.BLOCKED, 0)
                
                # Calculate OEE components
                scheduled_time = duration - idle_time
                availability = running_time / scheduled_time if scheduled_time > 0 else 0
                
                base_rate = eq.config.properties.get('base_rate', 80)
                theoretical_output = running_time * base_rate
                actual_output = getattr(eq, 'units_produced', 0)
                performance = actual_output / theoretical_output if theoretical_output > 0 else 0
                
                good_units = getattr(eq, 'units_produced', 0)
                total_units = good_units + getattr(eq, 'units_scrapped', 0)
                quality = good_units / total_units if total_units > 0 else 0
                
                oee = availability * performance * quality
                oee_values.append(oee)
                
                print(f"  {eq_id}:")
                print(f"    Units: {good_units} good, {getattr(eq, 'units_scrapped', 0)} scrap")
                print(f"    Failures: {getattr(eq, 'micro_stop_count', 0)} micro-stops, "
                      f"{getattr(eq, 'failure_count', 0)} total")
                print(f"    States: Run={running_time:.1f}min, Stop={stopped_time:.1f}min, "
                      f"Starve={starved_time:.1f}min, Block={blocked_time:.1f}min")
                print(f"    OEE: {oee:.1%} (A:{availability:.1%} P:{performance:.1%} Q:{quality:.1%})")
    
    # Summary
    avg_oee = sum(oee_values) / len(oee_values) if oee_values else 0
    print("\n" + "="*80)
    print(f"Average OEE: {avg_oee:.1%}")
    
    if 0.40 <= avg_oee <= 0.65:
        print("✅ SUCCESS: Achieved target baseline OEE (40-65%)")
    else:
        print(f"❌ FAILED: OEE {avg_oee:.1%} outside target range (40-65%)")
    
    return avg_oee


if __name__ == "__main__":
    oee = run_baseline_test()
    sys.exit(0 if 0.40 <= oee <= 0.65 else 1)