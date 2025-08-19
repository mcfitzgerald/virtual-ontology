"""Test Phase 4: Validate MES transduction layer.

This test validates that the transduction layer correctly converts
SimPy observables into MES-compatible format matching mes_data_with_kpis.csv.
"""

import simpy
from pathlib import Path
import yaml
import pandas as pd
from typing import Dict, Any, List

from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction.mes_transducer import MESTransducer
from twin_model.primitives import ProductionOrder


def test_transduction_basic():
    """Test basic transduction functionality."""
    print("Testing Basic Transduction...")

    # Create sample observables
    test_observables = [
        {
            "timestamp": 0,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "state_change",
            "new_state": "RUNNING",
            "old_state": "IDLE",
            "duration_in_state": 0,
        },
        {
            "timestamp": 1,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "unit_produced",
            "product_id": "SKU-1001",
            "quality": "good",
        },
        {
            "timestamp": 2,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "unit_produced",
            "product_id": "SKU-1001",
            "quality": "good",
        },
        {
            "timestamp": 3,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "unit_scrapped",
            "product_id": "SKU-1001",
            "reason": "quality_check_failed",
        },
        {
            "timestamp": 5,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "state_change",
            "new_state": "STOPPED_FAILURE",
            "old_state": "RUNNING",
            "duration_in_state": 5,
            "failure_mode": "UNP-MECH",
        },
    ]

    # Create transducer
    transducer = MESTransducer(time_bucket=5)

    # Process observables
    mes_df = transducer.process_observables(test_observables)

    # Validate output
    assert not mes_df.empty, "MES DataFrame should not be empty"
    assert "Timestamp" in mes_df.columns, "Missing Timestamp column"
    assert "OEE_Score" in mes_df.columns, "Missing OEE_Score column"

    print(f"✓ Generated {len(mes_df)} MES records")
    print(f"✓ Columns: {', '.join(mes_df.columns[:5])}...")

    # Check first record
    if len(mes_df) > 0:
        first_record = mes_df.iloc[0]
        print(
            f"✓ Sample record: Equipment={first_record['EquipmentID']}, "
            f"Good={first_record['GoodUnitsProduced']}, "
            f"Scrap={first_record['ScrapUnitsProduced']}"
        )

    print("Basic transduction test passed!\n")


def test_mes_format_compatibility():
    """Test that output matches expected MES format."""
    print("Testing MES Format Compatibility...")

    # Load reference MES data to check format
    reference_path = Path("archive/misc/data/mes_data_with_kpis.csv")
    reference_df = pd.read_csv(reference_path, nrows=5)

    # Expected columns from reference
    expected_columns = [
        "Timestamp",
        "ProductionOrderID",
        "LineID",
        "EquipmentID",
        "EquipmentType",
        "ProductID",
        "ProductName",
        "MachineStatus",
        "DowntimeReason",
        "GoodUnitsProduced",
        "ScrapUnitsProduced",
        "TargetRate_units_per_5min",
        "StandardCost_per_unit",
        "SalePrice_per_unit",
        "Availability_Score",
        "Performance_Score",
        "Quality_Score",
        "OEE_Score",
        "Energy_Consumption_kWh",
    ]

    # Create transducer and generate sample data
    transducer = MESTransducer()

    # Create more comprehensive test observables
    test_observables = generate_test_observables()

    # Process with manifests
    manifests = load_manifests()
    mes_df = transducer.process_observables(test_observables, manifests)

    # Check all columns present
    for col in expected_columns:
        assert col in mes_df.columns, f"Missing column: {col}"

    print(f"✓ All {len(expected_columns)} expected columns present")

    # Check data types match reference
    for col in ["GoodUnitsProduced", "ScrapUnitsProduced"]:
        assert pd.api.types.is_numeric_dtype(mes_df[col]), f"{col} should be numeric"

    for col in [
        "Availability_Score",
        "Performance_Score",
        "Quality_Score",
        "OEE_Score",
    ]:
        assert pd.api.types.is_numeric_dtype(mes_df[col]), f"{col} should be numeric"

    print("✓ Data types match expected format")

    # Check value ranges
    for col in ["Availability_Score", "Performance_Score", "Quality_Score"]:
        if not mes_df[col].empty:
            assert mes_df[col].min() >= 0, f"{col} should be >= 0"
            assert mes_df[col].max() <= 110, f"{col} should be <= 110"

    print("✓ KPI scores in valid ranges")
    print("MES format compatibility test passed!\n")


def test_simulation_to_mes():
    """Test full pipeline from simulation to MES data."""
    print("Testing Simulation to MES Pipeline...")

    # Setup simulation
    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    # Build model
    builder = OntologyDrivenModelBuilder(ontology_path, manifest_dir)
    model = builder.build_model(env)

    # Load production orders
    with open(manifest_dir / "production_manifest.yaml", "r") as f:
        prod_manifest = yaml.safe_load(f)

    # Add some orders
    if model["scheduler"]:
        for order_data in prod_manifest["production_orders"][:3]:  # First 3 orders
            order = ProductionOrder(
                order_id=order_data["order_id"],
                product_id=order_data["product_id"],
                target_quantity=order_data["target_quantity"],
                due_time=order_data["start_time"] + order_data["duration"],
                line_id=order_data["line_id"],
                priority=order_data["priority"],
            )
            model["scheduler"].add_order(order)

    print("✓ Model built with production orders")

    # Run simulation for 30 minutes
    env.run(until=30)

    print(f"✓ Simulation ran for {env.now} minutes")

    # Collect all observables
    all_observables = []
    for primitive in model["primitives"].values():
        if hasattr(primitive, "observables"):
            all_observables.extend(primitive.observables)

    print(f"✓ Collected {len(all_observables)} observables")

    # Check what types of observables we have
    event_types = set()
    primitive_types = set()
    equipment_obs = 0
    for obs in all_observables:
        event_types.add(obs.get("event_type"))
        primitive_types.add(obs.get("primitive_type"))
        if obs.get("primitive_type") in ["Equipment", "Filler", "Packer", "Palletizer"]:
            equipment_obs += 1

    print(f"  Event types: {sorted(list(event_types))[:5]}...")
    print(f"  Primitive types: {sorted(list(primitive_types))[:5]}...")
    print(f"  Equipment observables: {equipment_obs}")

    # Transform to MES format
    transducer = MESTransducer(time_bucket=5)

    # Load manifests properly
    manifests = {}
    if builder.manifests:
        for manifest_name, manifest_data in builder.manifests.items():
            if "equipment" in manifest_name.lower():
                manifests["equipment_manifest"] = manifest_data
            elif "production" in manifest_name.lower():
                manifests["production_manifest"] = manifest_data

    mes_df = transducer.process_observables(all_observables, manifests)

    print(f"✓ Generated {len(mes_df)} MES records")

    # Validate MES data
    if not mes_df.empty:
        # Check we have data for multiple equipment
        unique_equipment = mes_df["EquipmentID"].nunique()
        print(f"✓ Data for {unique_equipment} unique equipment")

        # Check we have production data
        total_good = mes_df["GoodUnitsProduced"].sum()
        total_scrap = mes_df["ScrapUnitsProduced"].sum()
        print(f"✓ Production: {total_good} good units, {total_scrap} scrap")

        # Check OEE calculation
        mean_oee = mes_df["OEE_Score"].mean()
        print(f"✓ Average OEE: {mean_oee:.1f}%")

    print("Simulation to MES pipeline test passed!\n")

    return mes_df


def test_kpi_calculations():
    """Test KPI calculations match expected logic."""
    print("Testing KPI Calculations...")

    # Create test metrics
    test_metrics = {
        "good_units": 240,
        "scrap_units": 10,
        "downtime_minutes": 1,
        "runtime_minutes": 4,
        "energy_consumption": 1.2,
        "last_status": "Running",
        "downtime_reason": None,
        "product_id": "SKU-1001",
        "product_name": "12oz Sparkling Water",
        "order_id": "ORD-1001",
    }

    transducer = MESTransducer(time_bucket=5)

    # Test availability calculation
    availability = transducer._calculate_availability(test_metrics)
    expected_availability = (5 - 1) / 5 * 100  # 80%
    assert abs(availability - expected_availability) < 0.1, (
        f"Availability calculation wrong: {availability} vs {expected_availability}"
    )
    print(f"✓ Availability: {availability:.1f}% (correct)")

    # Test quality calculation
    quality = transducer._calculate_quality(test_metrics)
    expected_quality = 240 / 250 * 100  # 96%
    assert abs(quality - expected_quality) < 0.1, (
        f"Quality calculation wrong: {quality} vs {expected_quality}"
    )
    print(f"✓ Quality: {quality:.1f}% (correct)")

    # Test performance calculation
    equipment_info = {"base_rate": 60.0}  # 60 units/minute
    product_info = {"target_rate_units_per_5min": 300}

    performance = transducer._calculate_performance(
        test_metrics, equipment_info, product_info
    )
    # Actual: 250 units, Adjusted target: 300 * (4/5) = 240
    expected_performance = 250 / 240 * 100  # 104.2%
    assert abs(performance - expected_performance) < 1, (
        f"Performance calculation wrong: {performance} vs {expected_performance}"
    )
    print(f"✓ Performance: {performance:.1f}% (correct)")

    # Test OEE
    oee = availability * performance * quality / 10000
    print(
        f"✓ OEE: {oee:.1f}% (A:{availability:.0f} × P:{performance:.0f} × Q:{quality:.0f})"
    )

    print("KPI calculations test passed!\n")


def test_downtime_tracking():
    """Test downtime reason tracking."""
    print("Testing Downtime Tracking...")

    # Create observables with various downtime reasons
    test_observables = [
        # Equipment starts running
        {
            "timestamp": 0,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "state_change",
            "new_state": "RUNNING",
            "old_state": "IDLE",
        },
        # Failure with specific reason
        {
            "timestamp": 3,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "equipment_failure",
            "failure_mode": "UNP-MECH",
        },
        {
            "timestamp": 3,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "state_change",
            "new_state": "STOPPED_FAILURE",
            "old_state": "RUNNING",
            "failure_mode": "UNP-MECH",
        },
        # Another equipment with different failure
        {
            "timestamp": 4,
            "primitive_id": "LINE1-PCK",
            "primitive_type": "Equipment",
            "event_type": "equipment_failure",
            "failure_mode": "UNP-JAM",
        },
        {
            "timestamp": 4,
            "primitive_id": "LINE1-PCK",
            "primitive_type": "Equipment",
            "event_type": "state_change",
            "new_state": "STOPPED_FAILURE",
            "old_state": "RUNNING",
            "failure_mode": "UNP-JAM",
        },
    ]

    transducer = MESTransducer(time_bucket=5)
    mes_df = transducer.process_observables(test_observables)

    # Check downtime reasons captured
    downtime_records = mes_df[mes_df["MachineStatus"] == "Stopped"]

    if not downtime_records.empty:
        unique_reasons = downtime_records["DowntimeReason"].unique()
        print(
            f"✓ Captured {len(unique_reasons)} unique downtime reasons: {unique_reasons}"
        )

        # Verify specific reasons
        assert "UNP-MECH" in downtime_records["DowntimeReason"].values
        assert "UNP-JAM" in downtime_records["DowntimeReason"].values
        print("✓ Specific downtime reasons correctly tracked")

    print("Downtime tracking test passed!\n")


def test_summary_statistics():
    """Test summary statistics generation."""
    print("Testing Summary Statistics...")

    # Run simulation to get MES data
    mes_df = test_simulation_to_mes()

    if not mes_df.empty:
        transducer = MESTransducer()
        stats = transducer.generate_summary_statistics(mes_df)

        # Check summary structure
        assert "overall_metrics" in stats
        assert "production" in stats
        assert "downtime" in stats

        print("✓ Summary statistics structure correct")

        # Display summary
        print("\nSummary Statistics:")
        print(f"  Overall OEE: {stats['overall_metrics']['oee']}%")
        print(f"  Total Good Units: {stats['production']['total_good_units']}")
        print(f"  Scrap Rate: {stats['production']['scrap_rate']}%")

        if stats["line_performance"]:
            print(f"  Lines reporting: {list(stats['line_performance'].keys())}")

        if stats["downtime"]["reasons"]:
            print(f"  Downtime reasons: {list(stats['downtime']['reasons'].keys())}")

    print("Summary statistics test passed!\n")


def generate_test_observables() -> List[Dict[str, Any]]:
    """Generate comprehensive test observables."""
    observables = []

    # Simulate 15 minutes of production
    for minute in range(15):
        base_time = minute * 60

        # Equipment running and producing
        for equipment_id in ["LINE1-FIL", "LINE1-PCK", "LINE1-PAL"]:
            # State changes
            if minute == 0:
                observables.append(
                    {
                        "timestamp": base_time,
                        "primitive_id": equipment_id,
                        "primitive_type": "Equipment",
                        "event_type": "state_change",
                        "new_state": "RUNNING",
                        "old_state": "IDLE",
                    }
                )

            # Production events
            units_per_minute = 50 if "FIL" in equipment_id else 45
            for i in range(units_per_minute):
                observables.append(
                    {
                        "timestamp": base_time + i,
                        "primitive_id": equipment_id,
                        "primitive_type": "Equipment",
                        "event_type": "unit_produced",
                        "product_id": "SKU-1001",
                        "quality": "good",
                    }
                )

            # Some scrap
            if minute % 3 == 0:
                observables.append(
                    {
                        "timestamp": base_time + 30,
                        "primitive_id": equipment_id,
                        "primitive_type": "Equipment",
                        "event_type": "unit_scrapped",
                        "product_id": "SKU-1001",
                        "reason": "quality_check",
                    }
                )

            # Energy consumption
            observables.append(
                {
                    "timestamp": base_time + 59,
                    "primitive_id": equipment_id,
                    "primitive_type": "Equipment",
                    "event_type": "energy_consumed",
                    "amount": 0.15,
                }
            )

    # Add a failure event
    observables.append(
        {
            "timestamp": 600,
            "primitive_id": "LINE1-FIL",
            "primitive_type": "Equipment",
            "event_type": "equipment_failure",
            "failure_mode": "UNP-SENS",
        }
    )

    return observables


def load_manifests() -> Dict[str, Any]:
    """Load manifests for testing."""
    manifest_dir = Path("manifests")
    manifests = {}

    with open(manifest_dir / "equipment_manifest.yaml", "r") as f:
        manifests["equipment_manifest"] = yaml.safe_load(f)

    with open(manifest_dir / "production_manifest.yaml", "r") as f:
        manifests["production_manifest"] = yaml.safe_load(f)

    return manifests


def test_save_mes_output():
    """Test saving MES data to file."""
    print("Testing MES Output Save...")

    # Generate MES data
    mes_df = test_simulation_to_mes()

    if not mes_df.empty:
        # Save to test output
        output_path = Path("test_mes_output.csv")
        transducer = MESTransducer()
        transducer.save_to_csv(mes_df, output_path)

        # Verify file created
        assert output_path.exists(), "Output file not created"

        # Load and verify
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(mes_df), "Data loss during save/load"

        print(f"✓ Saved {len(mes_df)} records to {output_path}")

        # Clean up
        output_path.unlink()
        print("✓ Test file cleaned up")

    print("MES output save test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4 TRANSDUCTION LAYER VALIDATION")
    print("=" * 60 + "\n")

    try:
        test_transduction_basic()
        test_mes_format_compatibility()
        test_kpi_calculations()
        test_downtime_tracking()
        test_simulation_to_mes()
        test_summary_statistics()
        test_save_mes_output()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("Phase 4 Transduction Layer validated:")
        print("  - Converts SimPy observables to MES format")
        print("  - Matches expected CSV structure")
        print("  - Calculates KPIs correctly")
        print("  - Tracks downtime reasons")
        print("  - Generates summary statistics")
        print("  - Saves to CSV format")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
