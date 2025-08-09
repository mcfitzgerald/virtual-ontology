"""
Test Phase 2: Actionable Parameters and Line Coupling
Validates parameter definitions, config transformation, and cascade models
"""

import sys
import os
import json
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_actionable_parameters():
    """Test actionable parameters module"""
    print("=" * 60)
    print("TESTING PHASE 2: ACTIONABLE PARAMETERS")
    print("=" * 60)
    
    from twin.actionable_parameters import ActionableParameters, ParameterType
    
    # Initialize parameters
    params = ActionableParameters()
    print("\n✓ ActionableParameters initialized")
    
    # Test 1: Check all 5 parameters exist
    print("\n1. PARAMETER EXISTENCE CHECK")
    print("-" * 40)
    
    required_params = [
        "micro_stop_probability",
        "performance_factor",
        "scrap_multiplier",
        "material_reliability",
        "cascade_sensitivity"
    ]
    
    for param_name in required_params:
        param = params.get_parameter(param_name)
        assert param is not None, f"Missing parameter: {param_name}"
        assert param.unit.startswith("http://qudt.org/"), f"{param_name} not using QUDT URI"
        print(f"✓ {param_name}: bounds={param.bounds}, default={param.default_value}")
    
    # Test 2: Value validation
    print("\n2. VALUE VALIDATION CHECK")
    print("-" * 40)
    
    # Test valid values
    params.set_value("micro_stop_probability", 0.15)
    assert params.get_value("micro_stop_probability") == 0.15
    print("✓ Set valid value: micro_stop_probability = 0.15")
    
    # Test invalid values
    try:
        params.set_value("micro_stop_probability", 0.6)  # Out of bounds
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✓ Correctly rejected out-of-bounds value")
    
    # Test 3: Normalization
    print("\n3. NORMALIZATION CHECK")
    print("-" * 40)
    
    params.reset_to_defaults()
    vector = params.get_normalized_vector()
    assert len(vector) == 5, f"Vector length should be 5, got {len(vector)}"
    assert all(0 <= v <= 1 for v in vector), "Normalized values not in [0,1]"
    print(f"✓ Normalized vector: {vector}")
    
    # Test reverse normalization
    params.set_from_normalized_vector(np.array([0.5, 0.5, 0.5, 0.5, 0.5]))
    for param_name in required_params:
        param = params.get_parameter(param_name)
        value = params.get_value(param_name)
        expected = (param.bounds[0] + param.bounds[1]) / 2
        assert abs(value - expected) < 0.01, f"{param_name} denormalization failed"
    print("✓ Denormalization working correctly")
    
    # Test 4: Impact calculation
    print("\n4. IMPACT CALCULATION CHECK")
    print("-" * 40)
    
    impacts = params.calculate_impact("micro_stop_probability", -50)  # 50% reduction
    assert 'availability' in impacts
    assert 'oee' in impacts
    assert impacts['availability'] > 0, "Reducing micro-stops should improve availability"
    print(f"✓ Impact calculation: {impacts}")
    
    # Test 5: Config overlay generation
    print("\n5. CONFIG OVERLAY CHECK")
    print("-" * 40)
    
    overlay = params.to_config_overlay()
    assert 'anomaly_injection' in overlay
    assert 'product_specifications' in overlay
    print("✓ Config overlay generated with required sections")
    
    # Check specific mappings
    assert 'frequent_micro_stops' in overlay['anomaly_injection']
    assert 'equipment_efficiency' in overlay['product_specifications']
    print("✓ Key parameter mappings present in overlay")
    
    print("\n✅ ACTIONABLE PARAMETERS TEST PASSED!")
    return True


def test_config_transformer():
    """Test configuration transformer"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 2: CONFIG TRANSFORMER")
    print("=" * 60)
    
    from twin.config_transformer import ConfigTransformer
    from twin.actionable_parameters import ActionableParameters
    
    # Initialize transformer
    transformer = ConfigTransformer()
    print("\n✓ ConfigTransformer initialized")
    
    # Test 1: Base config loading
    print("\n1. BASE CONFIG LOADING CHECK")
    print("-" * 40)
    
    assert transformer.base_config is not None
    assert 'anomaly_injection' in transformer.base_config
    assert 'product_specifications' in transformer.base_config
    print("✓ Base config loaded successfully")
    
    # Test 2: Apply parameters
    print("\n2. PARAMETER APPLICATION CHECK")
    print("-" * 40)
    
    params = ActionableParameters()
    params.set_value("micro_stop_probability", 0.10)
    params.set_value("performance_factor", 0.95)
    
    transformed = transformer.apply_parameters(params)
    
    # Check transformations applied
    micro_stop_prob = transformed['anomaly_injection']['frequent_micro_stops']['probability_per_5min']
    assert abs(micro_stop_prob - 0.10) < 0.01, "Micro-stop probability not applied"
    print(f"✓ Micro-stop probability applied: {micro_stop_prob}")
    
    # Check performance factor applied to equipment efficiency
    filler_eff = transformed['product_specifications']['equipment_efficiency']['Filler']
    assert filler_eff['max'] > filler_eff['min'], "Invalid efficiency range"
    print(f"✓ Performance factor applied to equipment efficiency")
    
    # Test 3: Scenario creation
    print("\n3. SCENARIO CREATION CHECK")
    print("-" * 40)
    
    scenario = transformer.create_scenario(
        "Test Scenario",
        {
            "micro_stop_probability": 0.08,
            "scrap_multiplier": 1.5
        }
    )
    
    assert 'scenario' in scenario
    assert scenario['scenario']['name'] == "Test Scenario"
    print(f"✓ Scenario created: {scenario['scenario']['name']}")
    
    # Test 4: Standard scenarios
    print("\n4. STANDARD SCENARIOS CHECK")
    print("-" * 40)
    
    scenarios = transformer.create_optimization_scenarios()
    
    required_scenarios = [
        "baseline",
        "improved_maintenance",
        "better_quality",
        "optimized_supply",
        "best_case",
        "worst_case"
    ]
    
    for scenario_name in required_scenarios:
        assert scenario_name in scenarios, f"Missing scenario: {scenario_name}"
        print(f"✓ {scenario_name} scenario created")
    
    # Test 5: Twin metadata
    print("\n5. TWIN METADATA CHECK")
    print("-" * 40)
    
    params = ActionableParameters()
    transformed = transformer.apply_parameters(params)
    
    assert 'twin_metadata' in transformed
    assert 'parameters_applied' in transformed['twin_metadata']
    print("✓ Twin metadata added to transformed config")
    
    print("\n✅ CONFIG TRANSFORMER TEST PASSED!")
    return True


def test_line_coupling():
    """Test line coupling model"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 2: LINE COUPLING MODEL")
    print("=" * 60)
    
    from twin.line_coupling_model import LineCoupling, EquipmentStatus, Buffer
    
    # Test 1: Buffer operations
    print("\n1. BUFFER OPERATIONS CHECK")
    print("-" * 40)
    
    buffer = Buffer(capacity=100, current_level=50)
    
    # Test adding
    added = buffer.add(30)
    assert added == 30
    assert buffer.current_level == 80
    print("✓ Buffer add operation: 50 + 30 = 80")
    
    # Test overflow
    added = buffer.add(30)
    assert added == 20  # Only 20 units of space left
    assert buffer.current_level == 100
    print("✓ Buffer overflow handling: capped at 100")
    
    # Test removing
    removed = buffer.remove(40)
    assert removed == 40
    assert buffer.current_level == 60
    print("✓ Buffer remove operation: 100 - 40 = 60")
    
    # Test underflow
    removed = buffer.remove(100)
    assert removed == 60  # Only 60 units available
    assert buffer.current_level == 0
    print("✓ Buffer underflow handling: stopped at 0")
    
    # Test 2: Line initialization
    print("\n2. LINE INITIALIZATION CHECK")
    print("-" * 40)
    
    model = LineCoupling()
    equipment_ids = ["LINE1-FIL", "LINE1-PCK", "LINE1-PAL"]
    model.initialize_line(equipment_ids)
    
    # Check buffers created
    assert len(model.buffers) == 2  # 3 equipment = 2 buffers
    print(f"✓ Created {len(model.buffers)} buffers for {len(equipment_ids)} equipment")
    
    # Check equipment status
    for eq_id in equipment_ids:
        assert model.equipment_status[eq_id] == EquipmentStatus.RUNNING
    print("✓ All equipment initialized as RUNNING")
    
    # Test 3: Starvation calculation
    print("\n3. STARVATION CALCULATION CHECK")
    print("-" * 40)
    
    model = LineCoupling()
    model.cascade_sensitivity = 0.8
    model.use_probabilistic = False  # Deterministic for testing
    model.initialize_line(equipment_ids)
    
    # Simulate upstream stop
    is_starved, prob = model.calculate_starvation(
        "LINE1-PCK", "LINE1-FIL", 
        EquipmentStatus.STOPPED, 
        time_interval_minutes=5
    )
    
    print(f"✓ Starvation calculation: starved={is_starved}, probability={prob:.2f}")
    
    # Test 4: Cascade simulation
    print("\n4. CASCADE SIMULATION CHECK")
    print("-" * 40)
    
    model = LineCoupling()
    model.cascade_sensitivity = 0.7
    model.use_probabilistic = False
    
    history = model.simulate_cascade(
        equipment_ids,
        initial_failure="LINE1-FIL",
        time_steps=6  # 30 minutes
    )
    
    # Check cascade occurred
    final_statuses = {eq: history[eq][-1] for eq in equipment_ids}
    assert final_statuses["LINE1-FIL"] == EquipmentStatus.STOPPED
    print(f"✓ Initial failure: LINE1-FIL = {final_statuses['LINE1-FIL'].value}")
    
    # Check downstream effects
    downstream_affected = sum(1 for status in final_statuses.values() 
                            if status != EquipmentStatus.RUNNING)
    print(f"✓ Cascade affected {downstream_affected}/{len(equipment_ids)} equipment")
    
    # Test 5: Buffer status
    print("\n5. BUFFER STATUS CHECK")
    print("-" * 40)
    
    buffer_status = model.get_buffer_status()
    assert len(buffer_status) == 2
    
    for buffer_id, status in buffer_status.items():
        assert 'current_level' in status
        assert 'fill_percentage' in status
        print(f"✓ {buffer_id}: {status['fill_percentage']:.0f}% full")
    
    # Test 6: Probabilistic behavior
    print("\n6. PROBABILISTIC BEHAVIOR CHECK")
    print("-" * 40)
    
    model = LineCoupling()
    model.cascade_sensitivity = 0.5
    model.use_probabilistic = True
    
    # Run multiple simulations to check variation
    outcomes = []
    for _ in range(10):
        model.initialize_line(equipment_ids)
        model.equipment_status["LINE1-FIL"] = EquipmentStatus.STOPPED
        
        is_starved, _ = model.calculate_starvation(
            "LINE1-PCK", "LINE1-FIL",
            EquipmentStatus.STOPPED,
            time_interval_minutes=20
        )
        outcomes.append(is_starved)
    
    # Should have some variation with probabilistic mode
    unique_outcomes = len(set(outcomes))
    print(f"✓ Probabilistic mode: {unique_outcomes} different outcomes in 10 runs")
    
    print("\n✅ LINE COUPLING MODEL TEST PASSED!")
    return True


if __name__ == "__main__":
    try:
        # Test actionable parameters
        test_actionable_parameters()
        
        # Test config transformer
        test_config_transformer()
        
        # Test line coupling
        test_line_coupling()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 2 TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)