#!/usr/bin/env python3
"""Verify alignment between CSV, database schema, and ontology"""

import csv
import yaml
from pathlib import Path

def load_csv_headers(csv_path):
    """Load CSV headers"""
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
    return headers

def load_yaml(yaml_path):
    """Load YAML file"""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def csv_to_snake_case(csv_col):
    """Convert CSV column name to snake_case"""
    # Handle special cases for camelCase columns
    if csv_col == "ProductionOrderID":
        return "production_order_id"
    elif csv_col == "LineID":
        return "line_id"
    elif csv_col == "EquipmentID":
        return "equipment_id"
    elif csv_col == "EquipmentType":
        return "equipment_type"
    elif csv_col == "ProductID":
        return "product_id"
    elif csv_col == "ProductName":
        return "product_name"
    elif csv_col == "MachineStatus":
        return "machine_status"
    elif csv_col == "DowntimeReason":
        return "downtime_reason"
    elif csv_col == "GoodUnitsProduced":
        return "good_units_produced"
    elif csv_col == "ScrapUnitsProduced":
        return "scrap_units_produced"
    elif csv_col == "TargetRate_units_per_5min":
        return "target_rate_units_per_5min"
    elif csv_col == "StandardCost_per_unit":
        return "standard_cost_per_unit"
    elif csv_col == "SalePrice_per_unit":
        return "sale_price_per_unit"
    else:
        # For already snake_case columns (like scores), just lowercase
        return csv_col.lower()

def verify_alignment():
    """Verify alignment between all three files"""
    
    # Load files
    csv_headers = load_csv_headers('data/mes_data_with_kpis.csv')
    ontology = load_yaml('ontology/ontology_spec.yaml')
    db_schema = load_yaml('ontology/database_schema.yaml')
    
    print("=" * 60)
    print("ALIGNMENT VERIFICATION REPORT")
    print("=" * 60)
    
    # Extract properties from ontology and database
    onto_props = ontology['properties']
    db_props = db_schema['properties']
    
    # Check each CSV column
    print("\n📊 CSV to Database/Ontology Mapping:")
    print("-" * 40)
    
    all_aligned = True
    for csv_col in csv_headers:
        # Convert CSV column to snake_case (lowercase with underscores)
        snake_case = csv_to_snake_case(csv_col)
        
        # Find in database schema - need to check all properties
        db_col = None
        onto_prop = None
        
        for prop_name, prop_data in db_props.items():
            # Compare snake_case version of CSV column with database column
            if prop_data['sql_column'] == snake_case:
                db_col = prop_data['sql_column']
                onto_prop = prop_name
                break
        
        # Check if ontology property exists
        onto_exists = onto_prop in onto_props if onto_prop else False
        
        # Check if sql_column matches in ontology
        onto_sql_match = False
        if onto_exists and onto_prop:
            onto_sql_col = onto_props[onto_prop].get('sql_column', '')
            onto_sql_match = onto_sql_col == snake_case
        
        status = "✅" if db_col and onto_exists and onto_sql_match else "❌"
        if status == "❌":
            all_aligned = False
            
        print(f"{status} CSV: {csv_col:30} → DB: {db_col or 'MISSING':30} → Onto: {onto_prop or 'MISSING'}")
        
        if not onto_sql_match and onto_exists:
            print(f"   ⚠️  Ontology sql_column mismatch: {onto_props[onto_prop].get('sql_column')}")
    
    print("\n" + "=" * 60)
    if all_aligned:
        print("✅ PERFECT ALIGNMENT! All columns map correctly across all three files.")
    else:
        print("⚠️  Some misalignments detected. Please review above.")
    print("=" * 60)
    
    # Summary statistics
    print(f"\n📈 Summary:")
    print(f"  - CSV columns: {len(csv_headers)}")
    print(f"  - Database properties: {len(db_props)}")
    print(f"  - Ontology properties: {len(onto_props)}")

if __name__ == "__main__":
    verify_alignment()