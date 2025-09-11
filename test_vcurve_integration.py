#!/usr/bin/env python
"""Integration test for V-Curve controller with production line."""

import logging
import simpy
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder
from twin_model.control import VCurveController, VCurveMode, VCurveParameters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_vcurve_integration():
    """Test V-Curve controller integration with production system."""
    
    print("=" * 80)
    print("V-CURVE CONTROLLER INTEGRATION TEST")
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
    
    # Identify equipment for V-curve control
    equipment = {}
    for equip_id, primitive in primitives.items():
        if hasattr(primitive, "processing"):
            equipment[equip_id] = primitive
            print(f"  - {equip_id}: nominal rate = {primitive.processing.nominal_rate:.1f}")
    
    # Test 1: No V-Curve (baseline)
    print("\n" + "=" * 80)
    print("TEST 1: BASELINE (No V-Curve)")
    print("=" * 80)
    
    env.run(until=60)
    
    baseline_production = {}
    for line_num in [1, 2, 3]:
        sink_id = f"LINE{line_num}-SINK"
        if sink_id in primitives and hasattr(primitives[sink_id], 'total_collected'):
            baseline_production[line_num] = primitives[sink_id].total_collected
            print(f"LINE{line_num} baseline: {baseline_production[line_num]:,.0f} units")
    
    # Reset environment for V-curve test
    env = simpy.Environment()
    
    # Rebuild model
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=Path("ontology/filling_line_ontology.yaml"),
        manifest_path=Path("manifests/equipment_manifest.yaml"),
        config_path=Path("config/calibrated_parameters.yaml")
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    
    # Get equipment for V-curve
    equipment = {}
    for equip_id, primitive in primitives.items():
        if hasattr(primitive, "processing"):
            equipment[equip_id] = primitive
    
    # Test 2: With Sub-optimal V-Curve
    print("\n" + "=" * 80)
    print("TEST 2: SUB-OPTIMAL V-CURVE (5% differentials)")
    print("=" * 80)
    
    # Create sub-optimal V-curve controller
    vcurve_params = VCurveParameters(
        mode=VCurveMode.FIXED_CONSTRAINT,
        constraint_equipment="LINE1-FIL",  # Filler as constraint
        upstream_differential=0.05,  # Sub-optimal: only 5% increase
        downstream_differential=0.05,  # Sub-optimal: only 5% increase
        update_interval=1.0,
    )
    
    controller = VCurveController(env, equipment, vcurve_params)
    controller.start()
    
    # Run simulation
    env.run(until=60)
    
    # Get metrics
    vcurve_metrics = controller.get_metrics()
    print(f"\n📊 V-Curve Metrics (Sub-optimal):")
    print(f"  - Constraint: {vcurve_metrics['constraint_id']}")
    print(f"  - Starvation rate: {vcurve_metrics['constraint_starvation_rate']*100:.1f}%")
    print(f"  - Blocking rate: {vcurve_metrics['constraint_blocking_rate']*100:.1f}%")
    
    suboptimal_production = {}
    for line_num in [1, 2, 3]:
        sink_id = f"LINE{line_num}-SINK"
        if sink_id in primitives and hasattr(primitives[sink_id], 'total_collected'):
            suboptimal_production[line_num] = primitives[sink_id].total_collected
            print(f"LINE{line_num} with sub-optimal V-curve: {suboptimal_production[line_num]:,.0f} units")
    
    # Test 3: With Optimal V-Curve
    print("\n" + "=" * 80)
    print("TEST 3: OPTIMAL V-CURVE (20%/15% differentials)")
    print("=" * 80)
    
    # Reset and rebuild
    env = simpy.Environment()
    
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=Path("ontology/filling_line_ontology.yaml"),
        manifest_path=Path("manifests/equipment_manifest.yaml"),
        config_path=Path("config/calibrated_parameters.yaml")
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    
    equipment = {}
    for equip_id, primitive in primitives.items():
        if hasattr(primitive, "processing"):
            equipment[equip_id] = primitive
    
    # Create optimal V-curve controller
    vcurve_params_optimal = VCurveParameters(
        mode=VCurveMode.FIXED_CONSTRAINT,
        constraint_equipment="LINE1-FIL",
        upstream_differential=0.20,  # Optimal: 20% increase upstream
        downstream_differential=0.15,  # Optimal: 15% increase downstream
        update_interval=1.0,
    )
    
    controller_optimal = VCurveController(env, equipment, vcurve_params_optimal)
    controller_optimal.start()
    
    # Run simulation
    env.run(until=60)
    
    # Get metrics
    vcurve_metrics_optimal = controller_optimal.get_metrics()
    print(f"\n📊 V-Curve Metrics (Optimal):")
    print(f"  - Constraint: {vcurve_metrics_optimal['constraint_id']}")
    print(f"  - Starvation rate: {vcurve_metrics_optimal['constraint_starvation_rate']*100:.1f}%")
    print(f"  - Blocking rate: {vcurve_metrics_optimal['constraint_blocking_rate']*100:.1f}%")
    
    print(f"\n🔧 Speed Adjustments:")
    for equip_id, multiplier in vcurve_metrics_optimal['speed_adjustments'].items():
        if "LINE1" in equip_id:
            print(f"  - {equip_id}: {multiplier:.2f}x")
    
    optimal_production = {}
    for line_num in [1, 2, 3]:
        sink_id = f"LINE{line_num}-SINK"
        if sink_id in primitives and hasattr(primitives[sink_id], 'total_collected'):
            optimal_production[line_num] = primitives[sink_id].total_collected
            print(f"LINE{line_num} with optimal V-curve: {optimal_production[line_num]:,.0f} units")
    
    # Compare results
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    for line_num in [1]:  # Focus on LINE1 with V-curve
        if line_num in baseline_production:
            baseline = baseline_production[line_num]
            suboptimal = suboptimal_production.get(line_num, 0)
            optimal = optimal_production.get(line_num, 0)
            
            print(f"\n📈 LINE{line_num} Production:")
            print(f"  - Baseline (no V-curve): {baseline:,.0f} units")
            print(f"  - Sub-optimal V-curve: {suboptimal:,.0f} units ({(suboptimal-baseline)/baseline*100:+.1f}%)")
            print(f"  - Optimal V-curve: {optimal:,.0f} units ({(optimal-baseline)/baseline*100:+.1f}%)")
            
            print(f"\n🎯 V-Curve Impact:")
            print(f"  - Sub-optimal improvement: {suboptimal - baseline:,.0f} units")
            print(f"  - Optimal improvement: {optimal - baseline:,.0f} units")
            print(f"  - Optimization potential: {optimal - suboptimal:,.0f} units")
    
    return baseline_production, suboptimal_production, optimal_production

if __name__ == "__main__":
    try:
        baseline, suboptimal, optimal = test_vcurve_integration()
        print("\n" + "=" * 80)
        if optimal[1] > suboptimal[1] > baseline[1]:
            print("✅ V-CURVE CONTROLLER WORKING CORRECTLY")
            print("   Optimal > Sub-optimal > Baseline")
        else:
            print("⚠️ CHECK V-CURVE IMPLEMENTATION")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()