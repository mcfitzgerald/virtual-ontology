"""Test control mappings to understand why they're computing wrong values.

This test checks the control manager's parameter computation logic.
"""

import sys
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.control.control_manager import ControlManager


def test_control_mappings():
    """Test control mapping calculations."""
    print("\n" + "="*80)
    print("CONTROL MAPPINGS TEST")
    print("="*80)
    
    # Initialize control manager
    ontology_path = Path("ontology/twin_ontology.yaml")
    mappings_path = Path("ontology/control_mappings.yaml")
    settings_path = Path("manifests/control_settings.yaml")
    
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=mappings_path,
        settings_path=settings_path
    )
    
    # Print current control values
    print("\nCurrent Control Values:")
    control_names = [
        'changeover_reduction_level',
        'operator_training_hours', 
        'line_speed_setting',
        'sensor_calibration_frequency',
        'product_sequencing_strategy',
        'pm_schedule_compliance',
        'staffing_level',
        'autonomous_maintenance_level'
    ]
    
    for control in control_names:
        value = control_mgr.get_control_value(control)
        print(f"  {control}: {value}")
    
    # Get computed parameters
    print("\nComputed Parameters (Current):")
    params = control_mgr.get_all_parameters()
    
    # Focus on the problematic parameters
    problem_params = ['mtbf', 'performance_factor', 'micro_stop_probability']
    for param in problem_params:
        if param in params:
            print(f"  {param}: {params[param]}")
    
    # Now test with baseline values that should give us good OEE
    print("\n" + "-"*80)
    print("Setting Baseline Control Values...")
    
    # Set controls to reasonable baseline values
    control_mgr.set_control_value('operator_training_hours', 20)  # Moderate training
    control_mgr.set_control_value('line_speed_setting', 85)  # Normal speed
    control_mgr.set_control_value('pm_schedule_compliance', 80)  # Good compliance
    control_mgr.set_control_value('sensor_calibration_frequency', 7)  # Weekly
    control_mgr.set_control_value('autonomous_maintenance_level', 2)  # Moderate AM
    
    print("\nUpdated Control Values:")
    for control in control_names:
        value = control_mgr.get_control_value(control)
        print(f"  {control}: {value}")
    
    print("\nComputed Parameters (After Update):")
    params = control_mgr.get_all_parameters()
    for param in problem_params:
        if param in params:
            print(f"  {param}: {params[param]}")
    
    # Check what the mappings config says these should be
    print("\n" + "-"*80)
    print("Expected Baseline Values:")
    print("  mtbf: ~240 minutes (4 hours between failures)")
    print("  performance_factor: ~0.85 (85% of theoretical)")
    print("  micro_stop_probability: ~0.15 (15% chance per 5 min)")
    
    # Debug the specific mappings
    print("\n" + "-"*80)
    print("Debug Mapping Logic:")
    
    # Check pm_schedule_compliance -> mtbf mapping
    pm_compliance = control_mgr.get_control_value('pm_schedule_compliance')
    print(f"\nPM Compliance: {pm_compliance}%")
    
    # Find the MTBF mapping
    for mapping in control_mgr.mappings:
        if mapping.control_name == 'pm_schedule_compliance' and mapping.parameter_name == 'mtbf':
            print(f"  Mapping function: {mapping.function}")
            print(f"  Mapping config: {mapping.config}")
            # Apply the mapping manually
            result = control_mgr._apply_mapping(pm_compliance, mapping)
            print(f"  Computed value: {result}")
            break
    
    # Check what base MTBF value is
    print("\nBase MTBF from simulation_parameters:")
    with open(mappings_path, 'r') as f:
        mappings_data = yaml.safe_load(f)
    
    sim_params = mappings_data.get('simulation_parameters', {})
    if 'mtbf' in sim_params:
        print(f"  Base MTBF: {sim_params['mtbf']}")
    
    # Check parameter bounds
    bounds = mappings_data.get('parameter_bounds', {})
    if 'mtbf' in bounds:
        print(f"  MTBF bounds: {bounds['mtbf']}")


if __name__ == "__main__":
    test_control_mappings()