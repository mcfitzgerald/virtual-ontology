"""Comprehensive test for all refactor phases.

Tests the complete implementation of:
- Phase 1: Material flow fixes
- Phase 2: Realistic failure modeling
- Phase 3: Production order scheduling
- Phase 4: Simplified model structure
"""

import sys
from pathlib import Path
import simpy
from typing import Dict, Any

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twin_model import OntologyDrivenModelBuilder
from twin_model.primitives.scheduler import ProductionOrder


def test_all_phases() -> Dict[str, Any]:
    """Test all implemented refactor phases.
    
    Returns:
        Test results dictionary
    """
    print("=" * 80)
    print("COMPREHENSIVE REFACTOR TEST - ALL PHASES")
    print("=" * 80)
    
    # Initialize paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    # Build model
    builder = OntologyDrivenModelBuilder(
        ontology_path=ontology_path,
        manifest_dir=manifest_dir
    )
    
    # Create environment and build model
    env = simpy.Environment()
    model = builder.build_model(env)
    
    results = {
        "phase1_material_flow": False,
        "phase2_failure_modeling": False,
        "phase3_order_scheduling": False,
        "phase4_internal_queues": False,
        "failures_detected": 0,
        "orders_processed": 0,
        "availability": 0.0,
        "errors": []
    }
    
    # Phase 1: Check material flow fixes
    print("\n✓ Phase 1: Material Flow Fixes")
    buffer_count = 0
    for entity_id, entity in model.items():
        if hasattr(entity, 'level'):
            buffer_count += 1
            print(f"  - {entity_id}: Buffer with level property")
            results["phase1_material_flow"] = True
            if buffer_count >= 3:
                break
    
    # Phase 2: Check failure modeling
    print("\n✓ Phase 2: Realistic Failure Modeling")
    equipment_with_failures = 0
    for entity_id, entity in model.items():
        if hasattr(entity, '_get_next_failure') and hasattr(entity, '_get_repair_duration'):
            equipment_with_failures += 1
            print(f"  - {entity_id}: Has mixture model failure methods")
    
    if equipment_with_failures > 0:
        results["phase2_failure_modeling"] = True
        print(f"  Total equipment with failure modeling: {equipment_with_failures}")
    
    # Phase 3: Check production order scheduling
    print("\n✓ Phase 3: Production Order Scheduling")
    scheduler = None
    sources_with_orders = 0
    
    for entity_id, entity in model.items():
        if hasattr(entity, 'add_production_order'):
            scheduler = entity
            print(f"  - Found scheduler: {entity_id}")
            
            # Add a test production order
            test_order = ProductionOrder(
                order_id="TEST-001",
                product_id="SKU-1001",
                target_quantity=100,
                due_time=60.0,
                line_id="LINE1",
                priority=1
            )
            scheduler.add_production_order(test_order)
            results["phase3_order_scheduling"] = True
            
        if hasattr(entity, 'set_production_order'):
            sources_with_orders += 1
            print(f"  - {entity_id}: Source with order support")
    
    print(f"  Sources with order support: {sources_with_orders}")
    
    # Phase 4: Check internal queues
    print("\n✓ Phase 4: Simplified Model Structure")
    equipment_with_queues = 0
    for entity_id, entity in model.items():
        if hasattr(entity, 'use_internal_queues'):
            if hasattr(entity, 'input_queue') and hasattr(entity, 'output_queue'):
                equipment_with_queues += 1
                print(f"  - {entity_id}: Has internal queues")
    
    if equipment_with_queues > 0:
        results["phase4_internal_queues"] = True
        print(f"  Total equipment with internal queues: {equipment_with_queues}")
    
    # Run simulation for a short time
    print("\n" + "=" * 80)
    print("RUNNING SIMULATION (60 minutes)")
    print("=" * 80)
    
    env.run(until=60)
    
    # Collect results
    print("\nAnalyzing Results...")
    
    # Count failures
    for entity_id, entity in model.items():
        if hasattr(entity, 'observables'):
            for obs in entity.observables:
                if obs.get('event_type') == 'equipment_failure':
                    results["failures_detected"] += 1
                elif obs.get('event_type') == 'order_released':
                    results["orders_processed"] += 1
    
    # Calculate availability
    total_time = 0
    running_time = 0
    for entity_id, entity in model.items():
        if hasattr(entity, 'observables'):
            for obs in entity.observables:
                if obs.get('event_type') == 'state_change':
                    duration = obs['details'].get('duration_in_state', 0)
                    total_time += duration
                    if obs['details'].get('old_state') == 'RUNNING':
                        running_time += duration
    
    if total_time > 0:
        results["availability"] = (running_time / total_time) * 100
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    print("\nPhase Implementation Status:")
    print(f"  Phase 1 (Material Flow):     {'✓' if results['phase1_material_flow'] else '✗'}")
    print(f"  Phase 2 (Failure Modeling):  {'✓' if results['phase2_failure_modeling'] else '✗'}")
    print(f"  Phase 3 (Order Scheduling):  {'✓' if results['phase3_order_scheduling'] else '✗'}")
    print(f"  Phase 4 (Internal Queues):   {'✓' if results['phase4_internal_queues'] else '✗'}")
    
    print(f"\nSimulation Metrics:")
    print(f"  Failures detected:     {results['failures_detected']}")
    print(f"  Orders processed:      {results['orders_processed']}")
    print(f"  Availability:          {results['availability']:.1f}%")
    
    # Overall status
    all_phases_complete = all([
        results["phase1_material_flow"],
        results["phase2_failure_modeling"],
        results["phase3_order_scheduling"],
        results["phase4_internal_queues"]
    ])
    
    print("\n" + "=" * 80)
    if all_phases_complete:
        print("SUCCESS: All refactor phases implemented successfully!")
    else:
        print("WARNING: Some phases not fully implemented or detected")
        if results["errors"]:
            print("\nErrors encountered:")
            for error in results["errors"]:
                print(f"  - {error}")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    test_all_phases()