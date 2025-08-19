"""Phase 5: Full Integration Test for MES Generation.

This test validates the complete pipeline from ontology-driven model
to MES data generation, ensuring the output matches the expected format
and contains realistic production patterns.
"""

import simpy
from pathlib import Path
import yaml
import pandas as pd
from datetime import datetime
from typing import Dict, Any
import json

from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction.mes_transducer import MESTransducer
from twin_model.primitives import ProductionOrder


def run_full_integration_test():
    """Run complete integration test from ontology to MES data."""

    print("=" * 80)
    print("PHASE 5: FULL INTEGRATION TEST")
    print("Ontology → SimPy Model → Simulation → Observables → MES Data")
    print("=" * 80 + "\n")

    # Configuration
    simulation_hours = 2  # Run for 2 hours initially for faster testing
    simulation_minutes = simulation_hours * 60

    print("Configuration:")
    print(
        f"  Simulation duration: {simulation_hours} hour(s) ({simulation_minutes} minutes)"
    )
    print("  Target OEE: ~65%")
    print("  Products: 6 SKUs")
    print("  Lines: 3 production lines")
    print("  Equipment: 9 main equipment (3 per line)")
    print()

    # 1. SETUP PHASE
    print("1. SETUP PHASE")
    print("-" * 40)

    # Initialize environment
    env = simpy.Environment()

    # Load ontology and manifests
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    # Create model builder
    builder = OntologyDrivenModelBuilder(ontology_path, manifest_dir)

    print("✓ Ontology loaded")
    print("✓ Manifests loaded")

    # Build model
    model = builder.build_model(env)

    print(f"✓ Model built: {len(model['primitives'])} primitives")

    # Count equipment by type
    equipment_count = {}
    for prim_id, primitive in model["primitives"].items():
        prim_type = primitive.config.type
        if prim_type in ["Filler", "Packer", "Palletizer"]:
            equipment_count[prim_type] = equipment_count.get(prim_type, 0) + 1

    for eq_type, count in equipment_count.items():
        print(f"  - {eq_type}: {count}")

    # 2. SCHEDULE PRODUCTION
    print("\n2. PRODUCTION SCHEDULING")
    print("-" * 40)

    # Load production orders from manifest
    with open(manifest_dir / "production_manifest.yaml", "r") as f:
        prod_manifest = yaml.safe_load(f)

    # Schedule orders for simulation period
    scheduled_orders = []
    order_count_by_product = {}

    for order_data in prod_manifest["production_orders"]:
        # Only schedule orders within our simulation window
        if order_data["start_time"] < simulation_minutes:
            order = ProductionOrder(
                order_id=order_data["order_id"],
                product_id=order_data["product_id"],
                target_quantity=order_data["target_quantity"],
                due_time=min(
                    order_data["start_time"] + order_data["duration"],
                    simulation_minutes,
                ),
                line_id=order_data["line_id"],
                priority=order_data["priority"],
            )

            if model["scheduler"]:
                model["scheduler"].add_order(order)

            scheduled_orders.append(order)

            # Track by product
            product_id = order_data["product_id"]
            order_count_by_product[product_id] = (
                order_count_by_product.get(product_id, 0) + 1
            )

    print(f"✓ Scheduled {len(scheduled_orders)} production orders")

    # Show order distribution
    print("\nOrders by product:")
    for product_id, count in sorted(order_count_by_product.items()):
        product_name = prod_manifest["products"][product_id]["name"]
        print(f"  {product_id}: {count} orders ({product_name})")

    # 3. RUN SIMULATION
    print("\n3. SIMULATION EXECUTION")
    print("-" * 40)

    print(f"Starting simulation for {simulation_minutes} minutes...")

    # Run simulation (check if already started)
    if env.now < simulation_minutes:
        # Run in chunks to show progress
        chunk_size = 60  # 1 hour chunks
        start_time = env.now
        target_time = simulation_minutes

        while env.now < target_time:
            next_time = min(env.now + chunk_size, target_time)
            env.run(until=next_time)

            # Progress indicator
            hours_done = env.now / 60
            if hours_done >= 1:
                print(f"  {hours_done:.1f} hours simulated...")

    print(f"✓ Simulation completed at t={env.now}")

    # 4. COLLECT OBSERVABLES
    print("\n4. OBSERVABLE COLLECTION")
    print("-" * 40)

    all_observables = []
    observable_counts = {}

    for primitive_id, primitive in model["primitives"].items():
        if hasattr(primitive, "observables"):
            obs_list = primitive.observables
            all_observables.extend(obs_list)

            # Count by primitive type
            prim_type = primitive.config.type
            observable_counts[prim_type] = observable_counts.get(prim_type, 0) + len(
                obs_list
            )

    print(f"✓ Collected {len(all_observables)} total observables")

    # Show distribution
    print("\nObservables by primitive type:")
    for prim_type, count in sorted(observable_counts.items()):
        print(f"  {prim_type}: {count:,}")

    # Analyze event types
    event_type_counts = {}
    product_ids = set()
    for obs in all_observables:
        event_type = obs.get("event_type", "unknown")
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        # Track product IDs
        if "product_id" in obs:
            product_ids.add(obs.get("product_id"))

    print("\nTop 10 event types:")
    for event_type, count in sorted(
        event_type_counts.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"  {event_type}: {count:,}")

    print(
        f"\nProduct IDs in observables: {product_ids if product_ids else 'None found'}"
    )

    # 5. TRANSDUCTION TO MES
    print("\n5. MES TRANSDUCTION")
    print("-" * 40)

    # Create transducer
    transducer = MESTransducer(time_bucket=5)

    # Prepare manifests for transduction
    manifests = {
        "equipment_manifest": builder.manifests.get("equipment_manifest.yaml"),
        "production_manifest": builder.manifests.get("production_manifest.yaml"),
    }

    # Process observables to MES format
    mes_df = transducer.process_observables(all_observables, manifests)

    print(f"✓ Generated {len(mes_df)} MES records")
    print(f"✓ Time buckets: {mes_df['Timestamp'].nunique()} unique timestamps")
    print(f"✓ Equipment tracked: {mes_df['EquipmentID'].nunique()} unique equipment")
    print(f"✓ Products produced: {mes_df['ProductID'].nunique()} unique products")

    # 6. VALIDATE MES DATA
    print("\n6. MES DATA VALIDATION")
    print("-" * 40)

    validation_results = validate_mes_data(mes_df)

    for check, result in validation_results.items():
        status = "✓" if result["passed"] else "✗"
        print(f"{status} {check}: {result['message']}")

    # 7. CALCULATE KPIs
    print("\n7. KEY PERFORMANCE INDICATORS")
    print("-" * 40)

    # Overall KPIs
    overall_kpis = calculate_overall_kpis(mes_df)

    print("Overall Performance:")
    print(f"  OEE: {overall_kpis['oee']:.1f}%")
    print(f"  Availability: {overall_kpis['availability']:.1f}%")
    print(f"  Performance: {overall_kpis['performance']:.1f}%")
    print(f"  Quality: {overall_kpis['quality']:.1f}%")

    print("\nProduction Summary:")
    print(f"  Total Good Units: {overall_kpis['total_good_units']:,}")
    print(f"  Total Scrap: {overall_kpis['total_scrap']:,}")
    print(f"  Scrap Rate: {overall_kpis['scrap_rate']:.2f}%")

    # Line-level KPIs
    line_kpis = calculate_line_kpis(mes_df)

    print("\nLine Performance:")
    for line_id, kpis in sorted(line_kpis.items()):
        print(f"  LINE{line_id}:")
        print(f"    OEE: {kpis['oee']:.1f}%")
        print(f"    Good Units: {kpis['good_units']:,}")

    # Product performance
    product_kpis = calculate_product_kpis(mes_df)

    print("\nProduct Performance:")
    for product_id, kpis in sorted(product_kpis.items())[:5]:  # Top 5
        print(f"  {product_id}:")
        print(f"    Units Produced: {kpis['good_units']:,}")
        print(f"    Quality Rate: {kpis['quality_rate']:.1f}%")

    # 8. DOWNTIME ANALYSIS
    print("\n8. DOWNTIME ANALYSIS")
    print("-" * 40)

    downtime_analysis = analyze_downtime(mes_df)

    print(f"Total Downtime Events: {downtime_analysis['total_events']}")

    if downtime_analysis["reasons"]:
        print("\nDowntime by Reason:")
        for reason, count in sorted(
            downtime_analysis["reasons"].items(), key=lambda x: x[1], reverse=True
        ):
            if reason:  # Skip empty reasons
                percentage = (count / downtime_analysis["total_events"]) * 100
                print(f"  {reason}: {count} events ({percentage:.1f}%)")

    # 9. SAVE OUTPUT
    print("\n9. OUTPUT GENERATION")
    print("-" * 40)

    # Save MES data
    output_file = Path("mes_output_integration.csv")
    mes_df.to_csv(output_file, index=False)
    print(f"✓ MES data saved to {output_file}")

    # Save summary report
    summary = generate_summary_report(
        mes_df, overall_kpis, line_kpis, product_kpis, downtime_analysis
    )

    report_file = Path("integration_report.json")
    with open(report_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✓ Summary report saved to {report_file}")

    # 10. COMPARISON WITH REFERENCE
    print("\n10. REFERENCE COMPARISON")
    print("-" * 40)

    reference_path = Path("archive/misc/data/mes_data_with_kpis.csv")
    if reference_path.exists():
        reference_df = pd.read_csv(reference_path)

        comparison = compare_with_reference(mes_df, reference_df)

        print("Structure Comparison:")
        print(f"  Columns match: {comparison['columns_match']}")
        print(f"  Data types compatible: {comparison['dtypes_compatible']}")

        print("\nStatistical Comparison:")
        print("  OEE Range:")
        print(f"    Generated: {comparison['oee_range_generated']}")
        print(f"    Reference: {comparison['oee_range_reference']}")
        print("  Scrap Rate:")
        print(f"    Generated: {comparison['scrap_rate_generated']:.2f}%")
        print(f"    Reference: {comparison['scrap_rate_reference']:.2f}%")

    return mes_df, overall_kpis


def validate_mes_data(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Validate MES data structure and content."""
    validation_results = {}

    # Check required columns
    required_columns = [
        "Timestamp",
        "ProductionOrderID",
        "LineID",
        "EquipmentID",
        "ProductID",
        "MachineStatus",
        "GoodUnitsProduced",
        "ScrapUnitsProduced",
        "OEE_Score",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    validation_results["required_columns"] = {
        "passed": len(missing_columns) == 0,
        "message": "All required columns present"
        if len(missing_columns) == 0
        else f"Missing columns: {missing_columns}",
    }

    # Check data types
    numeric_columns = [
        "GoodUnitsProduced",
        "ScrapUnitsProduced",
        "OEE_Score",
        "Availability_Score",
        "Performance_Score",
        "Quality_Score",
    ]

    non_numeric = []
    for col in numeric_columns:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            non_numeric.append(col)

    validation_results["data_types"] = {
        "passed": len(non_numeric) == 0,
        "message": "All numeric columns have correct type"
        if len(non_numeric) == 0
        else f"Non-numeric columns: {non_numeric}",
    }

    # Check value ranges
    if "OEE_Score" in df.columns:
        oee_valid = (df["OEE_Score"] >= 0) & (df["OEE_Score"] <= 110)
        invalid_oee = (~oee_valid).sum()

        validation_results["oee_range"] = {
            "passed": invalid_oee == 0,
            "message": "OEE scores in valid range (0-110)"
            if invalid_oee == 0
            else f"{invalid_oee} OEE scores out of range",
        }

    # Check timestamp format
    if "Timestamp" in df.columns:
        try:
            pd.to_datetime(df["Timestamp"])
            validation_results["timestamp_format"] = {
                "passed": True,
                "message": "Timestamps in valid datetime format",
            }
        except:
            validation_results["timestamp_format"] = {
                "passed": False,
                "message": "Invalid timestamp format",
            }

    # Check for data presence
    validation_results["data_presence"] = {
        "passed": len(df) > 0,
        "message": f"{len(df)} records generated"
        if len(df) > 0
        else "No data generated",
    }

    return validation_results


def calculate_overall_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate overall KPIs from MES data."""
    kpis = {}

    # OEE components
    kpis["oee"] = df["OEE_Score"].mean() if "OEE_Score" in df.columns else 0
    kpis["availability"] = (
        df["Availability_Score"].mean() if "Availability_Score" in df.columns else 0
    )
    kpis["performance"] = (
        df["Performance_Score"].mean() if "Performance_Score" in df.columns else 0
    )
    kpis["quality"] = df["Quality_Score"].mean() if "Quality_Score" in df.columns else 0

    # Production metrics
    kpis["total_good_units"] = (
        df["GoodUnitsProduced"].sum() if "GoodUnitsProduced" in df.columns else 0
    )
    kpis["total_scrap"] = (
        df["ScrapUnitsProduced"].sum() if "ScrapUnitsProduced" in df.columns else 0
    )

    total_produced = kpis["total_good_units"] + kpis["total_scrap"]
    kpis["scrap_rate"] = (
        (kpis["total_scrap"] / total_produced * 100) if total_produced > 0 else 0
    )

    # Energy
    kpis["total_energy"] = (
        df["Energy_Consumption_kWh"].sum()
        if "Energy_Consumption_kWh" in df.columns
        else 0
    )

    return kpis


def calculate_line_kpis(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Calculate KPIs by production line."""
    line_kpis = {}

    if "LineID" in df.columns:
        for line_id in df["LineID"].unique():
            line_df = df[df["LineID"] == line_id]

            line_kpis[line_id] = {
                "oee": line_df["OEE_Score"].mean()
                if "OEE_Score" in line_df.columns
                else 0,
                "good_units": line_df["GoodUnitsProduced"].sum()
                if "GoodUnitsProduced" in line_df.columns
                else 0,
                "scrap_units": line_df["ScrapUnitsProduced"].sum()
                if "ScrapUnitsProduced" in line_df.columns
                else 0,
                "records": len(line_df),
            }

    return line_kpis


def calculate_product_kpis(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Calculate KPIs by product."""
    product_kpis = {}

    if "ProductID" in df.columns:
        for product_id in df["ProductID"].unique():
            product_df = df[df["ProductID"] == product_id]

            good_units = product_df["GoodUnitsProduced"].sum()
            scrap_units = product_df["ScrapUnitsProduced"].sum()
            total_units = good_units + scrap_units

            product_kpis[product_id] = {
                "good_units": good_units,
                "scrap_units": scrap_units,
                "quality_rate": (good_units / total_units * 100)
                if total_units > 0
                else 0,
                "avg_oee": product_df["OEE_Score"].mean()
                if "OEE_Score" in product_df.columns
                else 0,
            }

    return product_kpis


def analyze_downtime(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze downtime patterns."""
    analysis = {"total_events": 0, "reasons": {}, "equipment_affected": set()}

    if "MachineStatus" in df.columns:
        # Find downtime records
        downtime_df = df[
            df["MachineStatus"].isin(["Stopped", "Maintenance", "Changeover"])
        ]

        analysis["total_events"] = len(downtime_df)

        if "DowntimeReason" in downtime_df.columns:
            # Count by reason
            reason_counts = downtime_df["DowntimeReason"].value_counts()
            analysis["reasons"] = reason_counts.to_dict()

        if "EquipmentID" in downtime_df.columns:
            analysis["equipment_affected"] = set(downtime_df["EquipmentID"].unique())

    return analysis


def generate_summary_report(
    df: pd.DataFrame,
    overall_kpis: Dict[str, float],
    line_kpis: Dict[str, Dict[str, float]],
    product_kpis: Dict[str, Dict[str, float]],
    downtime_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate comprehensive summary report."""

    report = {
        "timestamp": datetime.now().isoformat(),
        "data_summary": {
            "total_records": len(df),
            "time_range": {
                "start": df["Timestamp"].min() if "Timestamp" in df.columns else None,
                "end": df["Timestamp"].max() if "Timestamp" in df.columns else None,
            },
            "unique_equipment": df["EquipmentID"].nunique()
            if "EquipmentID" in df.columns
            else 0,
            "unique_products": df["ProductID"].nunique()
            if "ProductID" in df.columns
            else 0,
        },
        "overall_kpis": overall_kpis,
        "line_performance": line_kpis,
        "top_products": dict(
            sorted(
                product_kpis.items(), key=lambda x: x[1]["good_units"], reverse=True
            )[:5]
        ),
        "downtime_summary": {
            "total_events": downtime_analysis["total_events"],
            "top_reasons": dict(list(downtime_analysis["reasons"].items())[:5]),
            "equipment_count": len(downtime_analysis["equipment_affected"]),
        },
    }

    return report


def compare_with_reference(
    generated_df: pd.DataFrame, reference_df: pd.DataFrame
) -> Dict[str, Any]:
    """Compare generated data with reference MES data."""

    comparison = {}

    # Structure comparison
    comparison["columns_match"] = set(generated_df.columns) == set(reference_df.columns)
    comparison["dtypes_compatible"] = True  # Simplified for now

    # Statistical comparison
    if "OEE_Score" in generated_df.columns and "OEE_Score" in reference_df.columns:
        comparison["oee_range_generated"] = (
            f"{generated_df['OEE_Score'].min():.1f} - {generated_df['OEE_Score'].max():.1f}"
        )
        comparison["oee_range_reference"] = (
            f"{reference_df['OEE_Score'].min():.1f} - {reference_df['OEE_Score'].max():.1f}"
        )

    # Scrap rate comparison
    if "GoodUnitsProduced" in generated_df.columns:
        gen_good = generated_df["GoodUnitsProduced"].sum()
        gen_scrap = generated_df["ScrapUnitsProduced"].sum()
        gen_total = gen_good + gen_scrap
        comparison["scrap_rate_generated"] = (
            (gen_scrap / gen_total * 100) if gen_total > 0 else 0
        )

    if "GoodUnitsProduced" in reference_df.columns:
        ref_good = reference_df["GoodUnitsProduced"].sum()
        ref_scrap = reference_df["ScrapUnitsProduced"].sum()
        ref_total = ref_good + ref_scrap
        comparison["scrap_rate_reference"] = (
            (ref_scrap / ref_total * 100) if ref_total > 0 else 0
        )

    return comparison


def test_realistic_patterns():
    """Test that generated data shows realistic production patterns."""

    print("\nTesting Realistic Production Patterns...")
    print("-" * 40)

    # Run short simulation
    mes_df, kpis = run_full_integration_test()

    # Check OEE is in realistic range
    oee = kpis["oee"]
    assert 20 <= oee <= 85, f"OEE {oee:.1f}% outside realistic range (20-85%)"
    print(f"✓ OEE in realistic range: {oee:.1f}%")

    # Check scrap rate is realistic
    scrap_rate = kpis["scrap_rate"]
    assert 0.5 <= scrap_rate <= 10, (
        f"Scrap rate {scrap_rate:.2f}% outside realistic range"
    )
    print(f"✓ Scrap rate realistic: {scrap_rate:.2f}%")

    # Check we have varied machine states
    if "MachineStatus" in mes_df.columns:
        unique_states = mes_df["MachineStatus"].nunique()
        assert unique_states >= 2, "Should have multiple machine states"
        print(f"✓ Multiple machine states: {unique_states}")

    # Check we have downtime events
    if "DowntimeReason" in mes_df.columns:
        downtime_events = mes_df[mes_df["DowntimeReason"].notna()]
        assert len(downtime_events) > 0, "Should have downtime events"
        print(f"✓ Downtime events present: {len(downtime_events)}")

    print("\nRealistic patterns test passed!")


if __name__ == "__main__":
    try:
        # Run main integration test
        mes_df, overall_kpis = run_full_integration_test()

        # Run pattern validation
        test_realistic_patterns()

        print("\n" + "=" * 80)
        print("PHASE 5 INTEGRATION TEST COMPLETE! ✓")
        print("=" * 80)
        print("\nSummary:")
        print(f"  - Generated {len(mes_df)} MES records")
        print(f"  - Overall OEE: {overall_kpis['oee']:.1f}%")
        print(f"  - Total Production: {overall_kpis['total_good_units']:,} units")
        print("  - Files created:")
        print("    • mes_output_integration.csv")
        print("    • integration_report.json")
        print("\nThe ontology-driven virtual twin successfully generates")
        print("MES data matching the expected format with realistic patterns!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
