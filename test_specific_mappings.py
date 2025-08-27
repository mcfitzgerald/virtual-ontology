"""Debug specific control mappings."""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.control.control_manager import ControlManager, ParameterMapping, MappingFunction


def test_specific_mappings():
    """Test specific problematic mappings."""
    
    # Initialize control manager
    control_mgr = ControlManager(
        ontology_path=Path("ontology/twin_ontology.yaml"),
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=Path("manifests/control_settings.yaml")
    )
    
    print("\n" + "="*80)
    print("TESTING SPECIFIC MAPPINGS")
    print("="*80)
    
    # Test performance_factor mapping with operator_training_hours
    print("\n1. Performance Factor (operator_training_hours -> performance_factor)")
    print("-" * 50)
    
    for hours in [0, 8, 20, 40]:
        control_mgr.set_control_value('operator_training_hours', hours)
        params = control_mgr.get_all_parameters()
        perf = params.get('performance_factor', 0)
        print(f"  Training hours: {hours:2d} -> performance_factor: {perf:.4f}")
    
    print("\nExpected: Should start at 0.85 and increase with training")
    print("Formula: logarithmic with base=1.0, coefficient=0.05")
    
    # Manual calculation
    print("\nManual calculation:")
    base_perf = 0.85
    for hours in [0, 8, 20, 40]:
        # Logarithmic: base * log(1 + coefficient * value)
        multiplier = 1.0 * np.log(1 + 0.05 * hours)
        result = base_perf * multiplier
        print(f"  {hours:2d} hours: 0.85 * {multiplier:.4f} = {result:.4f}")
    
    # Test micro_stop_probability mapping with sensor_calibration_frequency
    print("\n2. Micro-Stop Probability (sensor_calibration_frequency -> micro_stop_probability)")
    print("-" * 50)
    
    for days in [1, 7, 14, 30]:
        control_mgr.set_control_value('sensor_calibration_frequency', days)
        params = control_mgr.get_all_parameters()
        prob = params.get('micro_stop_probability', 0)
        print(f"  Calibration every {days:2d} days -> micro_stop_probability: {prob:.4f}")
    
    print("\nExpected: Should be 0.15 at 7 days, increase after that")
    print("Formula: linear with base=1.0, coefficient=0.03, reference=7")
    
    # Manual calculation
    print("\nManual calculation:")
    base_prob = 0.15
    for days in [1, 7, 14, 30]:
        # Linear: base + coefficient * (value - reference)
        multiplier = 1.0 + 0.03 * (days - 7)
        multiplier = min(1.5, multiplier)  # max 1.5
        result = base_prob * multiplier
        print(f"  {days:2d} days: 0.15 * {multiplier:.4f} = {result:.4f}")
    
    # Check what mappings are actually found
    print("\n3. Actual Mappings Found")
    print("-" * 50)
    
    perf_mappings = [m for m in control_mgr.mappings if m.parameter_name == 'performance_factor']
    print(f"\nPerformance factor mappings: {len(perf_mappings)}")
    for m in perf_mappings:
        print(f"  {m.control_name} -> {m.parameter_name}")
        print(f"    Function: {m.function}")
        print(f"    Config: {m.config}")
    
    prob_mappings = [m for m in control_mgr.mappings if m.parameter_name == 'micro_stop_probability']
    print(f"\nMicro-stop probability mappings: {len(prob_mappings)}")
    for m in prob_mappings:
        print(f"  {m.control_name} -> {m.parameter_name}")
        print(f"    Function: {m.function}")
        print(f"    Config: {m.config}")


if __name__ == "__main__":
    test_specific_mappings()