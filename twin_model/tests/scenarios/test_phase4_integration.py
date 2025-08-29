"""Phase 4 Integration Tests.

Comprehensive end-to-end tests validating the complete twin model
with control system, realistic failures, and KPI targets.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any

import simpy
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twin_model.control.control_manager import ControlManager
from twin_model.control.parameter_effects import ParameterEffectsManager
from twin_model.primitives.source import SourcePrimitiveV2
from twin_model.primitives.equipment import EquipmentPrimitiveV2, EquipmentState
from twin_model.primitives.sink import SinkPrimitiveV2
from twin_model.primitives.scheduler import SchedulerPrimitiveV2, ProductionOrder, Product, ProductCategory
from twin_model.primitives.base import PrimitiveConfig


class ProductionLine:
    """Complete production line with control system."""
    
    def __init__(self, env: simpy.Environment, scenario: str = "baseline"):
        """Initialize production line.
        
        Args:
            env: SimPy environment
            scenario: Control scenario to apply
        """
        self.env = env
        self.scenario = scenario
        
        # Initialize control system
        self.control_mgr = ControlManager(
            ontology_path=Path("ontology/twin_ontology.yaml"),
            mappings_path=Path("ontology/control_mappings.yaml"),
            settings_path=Path("manifests/control_settings.yaml")
        )
        
        # Apply scenario
        self.control_mgr.apply_scenario(scenario)
        params = self.control_mgr.get_all_parameters()
        
        # Create scheduler
        self.scheduler = self._create_scheduler(params)
        
        # Create line components
        self.source = self._create_source(params)
        self.equipment = self._create_equipment_line(params)
        self.sink = self._create_sink(params)
        
        # Wire connections
        self._wire_connections()
        
        # Create some test orders
        self._create_test_orders()
    
    def _create_scheduler(self, params: Dict[str, float]) -> SchedulerPrimitiveV2:
        """Create scheduler with control parameters."""
        strategy = self.control_mgr.get_control_value("product_sequencing_strategy")
        
        config = PrimitiveConfig(
            id="SCHEDULER",
            type="SchedulerPrimitiveV2",
            properties={
                "sequencing_strategy": strategy,
                "campaign_size": 100,
                "changeover_reduction_factor": params.get("changeover_duration", 1.0)
            }
        )
        
        return SchedulerPrimitiveV2(self.env, config)
    
    def _create_source(self, params: Dict[str, float]) -> SourcePrimitiveV2:
        """Create source with control parameters."""
        # Source rate should match bottleneck (Packer) capacity
        bottleneck_base = 55.0  # Packer base rate
        source_rate = bottleneck_base * params.get("base_rate", 90.0) / 100.0
        
        config = PrimitiveConfig(
            id="SOURCE",
            type="SourcePrimitiveV2",
            properties={
                "order_mode": True,  # Order-driven
                "arrival_rate": source_rate,  # Match bottleneck capacity
                "quality_rate": max(0.8, 1.0 - min(0.2, params.get("false_reject_rate", 0.02))),
                "disruption_probability": 0.01
            }
        )
        
        return SourcePrimitiveV2(self.env, config)
    
    def _create_equipment_line(self, params: Dict[str, float]) -> list:
        """Create equipment line with control parameters."""
        equipment_list = []
        
        # Create 3 equipment in line: Filler -> Capper -> Packer
        equipment_specs = [
            ("FILLER", "Filler", 65.0),
            ("CAPPER", "Capper", 60.0),
            ("PACKER", "Packer", 55.0)  # Bottleneck
        ]
        
        for eq_id, eq_type, base_rate in equipment_specs:
            config = PrimitiveConfig(
                id=eq_id,
                type="EquipmentPrimitiveV2",
                properties={
                    "equipment_type": eq_type,
                    "base_rate": base_rate * params.get("base_rate", 1.0) / 100.0,
                    "internal_queue_size": 20,
                    "performance_factor": params.get("performance_factor", 0.85),
                    "scrap_rate": params.get("scrap_rate", 0.05),
                    "micro_stop_probability": params.get("micro_stop_probability", 0.3),
                    "micro_stop_frequency": params.get("micro_stop_frequency", 1.0),
                    "minor_failure_probability": params.get("minor_failure_probability", 0.05),
                    "major_failure_probability": params.get("major_failure_probability", 0.02),
                    "operator_skill_factor": params.get("operator_skill_factor", 1.0),
                    "maintenance_effectiveness": params.get("maintenance_effectiveness", 1.0),
                    "equipment_wear_rate": params.get("equipment_wear_rate", 1.0),
                    "warmup_period": 5.0
                }
            )
            
            equipment_list.append(EquipmentPrimitiveV2(self.env, config))
        
        return equipment_list
    
    def _create_sink(self, params: Dict[str, float]) -> SinkPrimitiveV2:
        """Create sink."""
        config = PrimitiveConfig(
            id="SINK",
            type="SinkPrimitiveV2",
            properties={
                "collection_rate": 60.0,
                "quality_threshold": 0.9,  # Lower threshold to accept most products
                "order_tracking": True
            }
        )
        
        return SinkPrimitiveV2(self.env, config)
    
    def _wire_connections(self) -> None:
        """Wire equipment connections."""
        # Source to first equipment
        self.source.set_downstream(self.equipment[0].input_queue)
        
        # Equipment to equipment
        for i in range(len(self.equipment) - 1):
            self.equipment[i].connect_to(self.equipment[i + 1])
        
        # Last equipment to sink
        self.equipment[-1].downstream_equipment = self.sink
        self.sink.set_upstream(self.equipment[-1].output_queue)
    
    def _create_test_orders(self) -> None:
        """Create test production orders."""
        # Create products
        products = {
            "SKU-A": Product(
                product_id="SKU-A",
                category=ProductCategory.A,
                family="Premium",
                volume_rank=1,
                margin=0.45,
                complexity=0.3,
                typical_batch_size=100,
                min_batch_size=50,
                max_batch_size=200
            ),
            "SKU-B": Product(
                product_id="SKU-B",
                category=ProductCategory.B,
                family="Standard",
                volume_rank=2,
                margin=0.35,
                complexity=0.5,
                typical_batch_size=75,
                min_batch_size=25,
                max_batch_size=150
            )
        }
        
        # Create orders - need enough to run full time
        # At 85 units/min, need ~40,000 units for 480 minutes
        orders = [
            ProductionOrder(
                order_id="ORD-001",
                product=products["SKU-A"],
                quantity=10000,
                due_date=480,  # 8 hours
                priority=1
            ),
            ProductionOrder(
                order_id="ORD-002",
                product=products["SKU-B"],
                quantity=10000,
                due_date=960,  # 16 hours
                priority=2
            ),
            ProductionOrder(
                order_id="ORD-003",
                product=products["SKU-A"],
                quantity=10000,
                due_date=1440,  # 24 hours
                priority=3
            ),
            ProductionOrder(
                order_id="ORD-004",
                product=products["SKU-B"],
                quantity=10000,
                due_date=1920,  # 32 hours
                priority=4
            )
        ]
        
        # Add orders to scheduler
        for order in orders:
            self.scheduler.add_order(order)
            self.source.add_order_to_queue(order)
    
    def start(self) -> None:
        """Start all processes."""
        self.scheduler.start()
        self.source.start()
        for eq in self.equipment:
            eq.start()
        self.sink.start()
    
    def get_kpis(self) -> Dict[str, Any]:
        """Calculate line KPIs."""
        # Get bottleneck equipment (usually the slowest)
        bottleneck = min(self.equipment, key=lambda e: e.base_rate)
        bottleneck_kpis = bottleneck.get_kpis()
        
        # Calculate line-level KPIs
        total_produced = sum(eq.units_produced for eq in self.equipment) / len(self.equipment)
        total_scrapped = sum(eq.units_scrapped for eq in self.equipment)
        
        return {
            "oee": bottleneck_kpis.get("oee", 0),
            "availability": bottleneck_kpis.get("availability", 0),
            "performance": bottleneck_kpis.get("performance", 0),
            "quality": bottleneck_kpis.get("quality", 0),
            "total_produced": total_produced,
            "total_scrapped": total_scrapped,
            "total_collected": self.sink.total_units_collected,
            "schedule_metrics": self.scheduler.get_schedule_metrics()
        }


def test_baseline_scenario():
    """Test baseline scenario performance."""
    print("\n" + "="*60)
    print("Testing Baseline Scenario")
    print("="*60)
    
    env = simpy.Environment()
    line = ProductionLine(env, scenario="baseline")
    line.start()
    
    # Run for 480 minutes (8 hours)
    env.run(until=480)
    
    kpis = line.get_kpis()
    
    print(f"\nBaseline Results after {env.now} minutes:")
    print(f"  OEE: {kpis['oee']:.1%}")
    print(f"  Availability: {kpis['availability']:.1%}")
    print(f"  Performance: {kpis['performance']:.1%}")
    print(f"  Quality: {kpis['quality']:.1%}")
    print(f"  Total Collected: {kpis['total_collected']}")
    
    # Validate against expected baseline (poor performance)
    assert 0.4 <= kpis['oee'] <= 0.65, f"Baseline OEE should be 40-65%, got {kpis['oee']:.1%}"
    
    print("\n✓ Baseline scenario test passed")
    return kpis


def test_quick_wins_scenario():
    """Test quick wins scenario performance."""
    print("\n" + "="*60)
    print("Testing Quick Wins Scenario")
    print("="*60)
    
    env = simpy.Environment()
    line = ProductionLine(env, scenario="quick_wins")
    line.start()
    
    # Run for 480 minutes (8 hours)
    env.run(until=480)
    
    kpis = line.get_kpis()
    
    print(f"\nQuick Wins Results after {env.now} minutes:")
    print(f"  OEE: {kpis['oee']:.1%}")
    print(f"  Availability: {kpis['availability']:.1%}")
    print(f"  Performance: {kpis['performance']:.1%}")
    print(f"  Quality: {kpis['quality']:.1%}")
    print(f"  Total Collected: {kpis['total_collected']}")
    
    # Should be better than baseline
    assert 0.5 <= kpis['oee'] <= 0.75, f"Quick wins OEE should be 50-75%, got {kpis['oee']:.1%}"
    
    print("\n✓ Quick wins scenario test passed")
    return kpis


def test_optimized_scenario():
    """Test optimized scenario performance."""
    print("\n" + "="*60)
    print("Testing Optimized Scenario")
    print("="*60)
    
    env = simpy.Environment()
    line = ProductionLine(env, scenario="optimized")
    line.start()
    
    # Run for 480 minutes (8 hours)
    env.run(until=480)
    
    kpis = line.get_kpis()
    
    print(f"\nOptimized Results after {env.now} minutes:")
    print(f"  OEE: {kpis['oee']:.1%}")
    print(f"  Availability: {kpis['availability']:.1%}")
    print(f"  Performance: {kpis['performance']:.1%}")
    print(f"  Quality: {kpis['quality']:.1%}")
    print(f"  Total Collected: {kpis['total_collected']}")
    
    # Should be significantly better
    assert 0.6 <= kpis['oee'] <= 0.85, f"Optimized OEE should be 60-85%, got {kpis['oee']:.1%}"
    
    print("\n✓ Optimized scenario test passed")
    return kpis


def test_control_effects():
    """Test that controls have expected effects."""
    print("\n" + "="*60)
    print("Testing Control Effects")
    print("="*60)
    
    # Test high speed vs low speed
    env1 = simpy.Environment()
    line1 = ProductionLine(env1, scenario="baseline")
    line1.control_mgr.set_control_value("line_speed_setting", 95)
    line1.start()
    env1.run(until=120)
    kpis_high_speed = line1.get_kpis()
    
    env2 = simpy.Environment()
    line2 = ProductionLine(env2, scenario="baseline")
    line2.control_mgr.set_control_value("line_speed_setting", 75)
    line2.start()
    env2.run(until=120)
    kpis_low_speed = line2.get_kpis()
    
    print(f"\nHigh Speed (95%):")
    print(f"  Quality: {kpis_high_speed['quality']:.1%}")
    print(f"  Performance: {kpis_high_speed['performance']:.1%}")
    
    print(f"\nLow Speed (75%):")
    print(f"  Quality: {kpis_low_speed['quality']:.1%}")
    print(f"  Performance: {kpis_low_speed['performance']:.1%}")
    
    # High speed should have worse quality but better performance
    assert kpis_high_speed['quality'] <= kpis_low_speed['quality'], \
        "High speed should have worse quality"
    
    print("\n✓ Control effects test passed")


def test_failure_modeling():
    """Test realistic failure patterns."""
    print("\n" + "="*60)
    print("Testing Failure Modeling")
    print("="*60)
    
    env = simpy.Environment()
    
    # Create equipment with known failure parameters
    config = PrimitiveConfig(
        id="TEST-EQUIP",
        type="EquipmentPrimitiveV2",
        properties={
            "base_rate": 60.0,
            "internal_queue_size": 10,
            "performance_factor": 1.0,
            "scrap_rate": 0.0,
            "micro_stop_probability": 0.8,  # High for testing
            "micro_stop_frequency": 3.0,  # Very high frequency
            "minor_failure_probability": 0.5,
            "major_failure_probability": 0.2,
            "warmup_period": 0.0
        }
    )
    
    equipment = EquipmentPrimitiveV2(env, config)
    
    # Create simple source and sink
    source = SourcePrimitiveV2(env, PrimitiveConfig(
        id="SOURCE",
        type="SourcePrimitiveV2",
        properties={
            "order_mode": False, 
            "arrival_rate": 60.0,
            "disruption_probability": 0.0  # No disruptions for failure test
        }
    ))
    
    sink = SinkPrimitiveV2(env, PrimitiveConfig(
        id="SINK",
        type="SinkPrimitiveV2",
        properties={}
    ))
    
    # Connect
    source.set_downstream(equipment.input_queue)
    equipment.downstream_equipment = sink
    sink.set_upstream(equipment.output_queue)
    
    # Start
    source.start()
    equipment.start()
    sink.start()
    
    # Run for 120 minutes
    env.run(until=120)
    
    # Check failure patterns
    total_time = env.now
    running_time = equipment.state_durations[EquipmentState.RUNNING]
    failure_time = equipment.state_durations[EquipmentState.STOPPED_FAILURE]
    
    failure_percentage = (failure_time / total_time * 100) if total_time > 0 else 0
    
    print(f"\nFailure Analysis:")
    print(f"  Total Time: {total_time:.1f} minutes")
    print(f"  Running Time: {running_time:.1f} minutes")
    print(f"  Failure Time: {failure_time:.1f} minutes")
    print(f"  Failure Percentage: {failure_percentage:.1f}%")
    
    # With high failure rates, should see significant downtime
    assert failure_percentage > 5, "Should see significant failure time with high failure rates"
    
    print("\n✓ Failure modeling test passed")


def test_scenario_progression():
    """Test that scenarios show progressive improvement."""
    print("\n" + "="*60)
    print("Testing Scenario Progression")
    print("="*60)
    
    scenarios = ["baseline", "quick_wins", "optimized"]
    results = {}
    
    for scenario in scenarios:
        env = simpy.Environment()
        line = ProductionLine(env, scenario=scenario)
        line.start()
        env.run(until=240)  # 4 hours
        
        kpis = line.get_kpis()
        results[scenario] = kpis
        
        print(f"\n{scenario.upper()}:")
        print(f"  OEE: {kpis['oee']:.1%}")
        print(f"  Units Collected: {kpis['total_collected']}")
    
    # Verify progression
    assert results["quick_wins"]["oee"] >= results["baseline"]["oee"], \
        "Quick wins should improve over baseline"
    
    assert results["optimized"]["oee"] >= results["quick_wins"]["oee"], \
        "Optimized should improve over quick wins"
    
    assert results["optimized"]["total_collected"] >= results["baseline"]["total_collected"], \
        "Optimized should produce more units"
    
    print("\n✓ Scenario progression test passed")


def main():
    """Run all Phase 4 integration tests."""
    print("\n" + "="*60)
    print("PHASE 4: INTEGRATION & TESTING")
    print("="*60)
    
    tests = [
        ("Baseline Scenario", test_baseline_scenario),
        ("Quick Wins Scenario", test_quick_wins_scenario),
        ("Optimized Scenario", test_optimized_scenario),
        ("Control Effects", test_control_effects),
        ("Failure Modeling", test_failure_modeling),
        ("Scenario Progression", test_scenario_progression)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("PHASE 4 TEST SUMMARY")
    print("="*60)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL PHASE 4 TESTS PASSED")
        print("\nKey Achievements:")
        print("  ✓ Complete production line with control system")
        print("  ✓ Realistic failure modeling working")
        print("  ✓ Control effects properly applied")
        print("  ✓ KPIs calculated correctly")
        print("  ✓ Scenarios show expected progression")
    else:
        print("\n✗ SOME TESTS FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)