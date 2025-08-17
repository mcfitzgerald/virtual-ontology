"""
Test the transduction layer with actual simulation data.

This script:
1. Runs a twin_model simulation
2. Applies the transduction layer
3. Validates the output format
4. Saves results as CSV for inspection
"""

import sys
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from twin_model import (
    SimulationRunner,
    ActionableParameters,
    SimulationConfig,
)
from twin_model.config import (
    LineConfig,
    EquipmentConfig,
    EquipmentType,
)
from twin_model.transduction import (
    MESTransducer,
    ProductInfo,
    create_transducer_from_ontology,
)


def create_full_line_config() -> LineConfig:
    """Create a complete production line configuration.
    
    Returns:
        LineConfig with three equipment pieces
    """
    equipment_configs = [
        EquipmentConfig(
            equipment_id="LINE1-FIL",
            equipment_type=EquipmentType.FILLER,
            base_rate=60.0,  # units per minute
            mtbf=480.0,  # mean time between failures
            mttr=30.0,  # mean time to repair
            base_scrap_rate=0.02,
        ),
        EquipmentConfig(
            equipment_id="LINE1-PCK",
            equipment_type=EquipmentType.PACKER,
            base_rate=55.0,
            mtbf=600.0,
            mttr=20.0,
            base_scrap_rate=0.01,
        ),
        EquipmentConfig(
            equipment_id="LINE1-PAL",
            equipment_type=EquipmentType.PALLETIZER,
            base_rate=50.0,
            mtbf=720.0,
            mttr=15.0,
            base_scrap_rate=0.005,
        ),
    ]
    
    return LineConfig(
        line_id="LINE1",
        equipment_configs=equipment_configs,
        source_arrival_rate=65.0,
    )


def validate_mes_format(df: pd.DataFrame) -> Dict[str, bool]:
    """Validate that DataFrame matches expected MES format.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dictionary of validation results
    """
    validations = {}
    
    # Check required columns
    required_columns = [
        "Timestamp", "ProductionOrderID", "LineID", "EquipmentID",
        "EquipmentType", "ProductID", "ProductName", "MachineStatus",
        "DowntimeReason", "GoodUnitsProduced", "ScrapUnitsProduced",
        "TargetRate_units_per_5min", "StandardCost_per_unit",
        "SalePrice_per_unit", "Availability_Score", "Performance_Score",
        "Quality_Score", "OEE_Score"
    ]
    
    validations["has_all_columns"] = all(col in df.columns for col in required_columns)
    validations["correct_column_count"] = len(df.columns) == len(required_columns)
    
    if not df.empty:
        # Check data types
        validations["timestamp_is_string"] = df["Timestamp"].dtype == object
        validations["production_is_numeric"] = pd.api.types.is_numeric_dtype(df["GoodUnitsProduced"])
        validations["scores_are_numeric"] = all(
            pd.api.types.is_numeric_dtype(df[col])
            for col in ["Availability_Score", "Performance_Score", "Quality_Score", "OEE_Score"]
        )
        
        # Check value ranges
        validations["scores_in_range"] = all(
            (df[col] >= 0).all() and (df[col] <= 100).all()
            for col in ["Availability_Score", "Performance_Score", "Quality_Score"]
        )
        
        # Check machine status values
        valid_statuses = {"Running", "Stopped", "Idle"}
        validations["valid_machine_status"] = df["MachineStatus"].isin(valid_statuses).all()
        
        # Check structure: should have multiple equipment per timestamp
        timestamps = df["Timestamp"].unique()
        equipment_per_timestamp = df.groupby("Timestamp")["EquipmentID"].count()
        validations["multiple_equipment_per_timestamp"] = (equipment_per_timestamp > 1).any()
    
    return validations


def main() -> None:
    """Run the transduction test."""
    print("Testing MES Transduction Layer")
    print("=" * 60)
    
    # Step 1: Create and run simulation
    print("\n1. Running simulation...")
    config = SimulationConfig(
        duration_days=1/24,  # 1 hour
        mes_logging_interval=5.0,  # every 5 minutes
        line_configs=[create_full_line_config()],
        random_seed=42,
    )
    
    runner = SimulationRunner(config)
    params = ActionableParameters()
    
    # Run with some parameter variations to create interesting data
    params.micro_stop_probability = 1.2  # More failures
    params.performance_factor = 0.95  # Slightly slower
    params.scrap_multiplier = 1.5  # More scrap
    
    results = runner.run_simulation(params, duration_days=1/24, seed=42)
    
    print(f"   Simulation completed: {len(results.mes_data)} snapshots")
    
    # Step 2: Apply transduction
    print("\n2. Applying transduction layer...")
    
    # Create transducer with custom product info
    product_info = ProductInfo(
        product_id="SKU-2002",
        product_name="16oz Energy Drink",
        target_rate_per_5min=300,  # 60 units/min * 5 min
        standard_cost_per_unit=0.55,
        sale_price_per_unit=1.75,
    )
    
    transducer = MESTransducer(
        base_timestamp=datetime(2025, 6, 1),
        order_id="ORD-1000",
        product_info=product_info,
    )
    
    # Convert to MES format
    mes_df = transducer.transduce_simulation(results)
    
    print(f"   Generated {len(mes_df)} MES records")
    print(f"   Shape: {mes_df.shape}")
    
    # Step 3: Validate format
    print("\n3. Validating MES format...")
    validations = validate_mes_format(mes_df)
    
    for check, passed in validations.items():
        status = "✓" if passed else "✗"
        print(f"   {status} {check}: {passed}")
    
    # Step 4: Show sample data
    print("\n4. Sample MES Data (first 5 rows):")
    print("-" * 60)
    
    if not mes_df.empty:
        # Display subset of columns for readability
        display_cols = [
            "Timestamp", "LineID", "EquipmentID", "MachineStatus",
            "GoodUnitsProduced", "OEE_Score"
        ]
        print(mes_df[display_cols].head().to_string(index=False))
    
    # Step 5: Analyze data
    print("\n5. Data Analysis:")
    print("-" * 60)
    
    if not mes_df.empty:
        # Equipment breakdown
        equipment_counts = mes_df["EquipmentID"].value_counts()
        print(f"   Records per equipment:")
        for equip, count in equipment_counts.items():
            print(f"     {equip}: {count}")
        
        # Status breakdown
        status_counts = mes_df["MachineStatus"].value_counts()
        print(f"\n   Machine status distribution:")
        for status, count in status_counts.items():
            print(f"     {status}: {count} ({count/len(mes_df)*100:.1f}%)")
        
        # Production summary
        total_good = mes_df["GoodUnitsProduced"].sum()
        total_scrap = mes_df["ScrapUnitsProduced"].sum()
        avg_oee = mes_df["OEE_Score"].mean()
        
        print(f"\n   Production summary:")
        print(f"     Total good units: {total_good:,.0f}")
        print(f"     Total scrap units: {total_scrap:,.0f}")
        print(f"     Average OEE: {avg_oee:.1f}%")
    
    # Step 6: Save to CSV
    output_file = Path("mes_output_transduced.csv")
    mes_df.to_csv(output_file, index=False)
    print(f"\n6. Saved MES data to: {output_file}")
    
    # Step 7: Test ontology-driven transducer
    print("\n7. Testing ontology-driven transducer...")
    try:
        ontology_transducer = create_transducer_from_ontology(
            "ontology/twin_ontology.yaml"
        )
        print("   ✓ Successfully created transducer from ontology")
        
        # Show loaded mappings
        print(f"   State mappings loaded: {len(ontology_transducer.state_mapping)}")
        for simpy_state, mes_status in ontology_transducer.state_mapping.items():
            print(f"     {simpy_state} → {mes_status}")
            
    except Exception as e:
        print(f"   ✗ Failed to create from ontology: {e}")
    
    print("\n" + "=" * 60)
    print("Transduction test complete!")


if __name__ == "__main__":
    main()