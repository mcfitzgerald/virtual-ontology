"""Test database functionality"""

from database.manager import TwinDatabaseManager
from database.integration import TwinDatabaseIntegration
from sqlmodel import Session, select
from database.models import EquipmentConfig, ProductConfig
import json


def test_database():
    """Test basic database operations"""
    
    print("=== Testing Database Implementation ===\n")
    
    # Initialize manager
    manager = TwinDatabaseManager()
    
    # Test 1: Check tables created
    print("1. Checking database tables...")
    with Session(manager.engine) as session:
        # Check equipment configs
        equipment = session.exec(select(EquipmentConfig)).all()
        print(f"   ✓ Found {len(equipment)} equipment configurations")
        
        # Check product configs
        products = session.exec(select(ProductConfig)).all()
        print(f"   ✓ Found {len(products)} product configurations")
    
    # Test 2: Check YAML loading
    print("\n2. Testing YAML loading...")
    ontology = manager.load_ontology()
    print(f"   ✓ Loaded ontology version: {ontology['metadata']['version']}")
    
    equipment_manifest = manager.load_manifest("equipment_manifest")
    print(f"   ✓ Loaded equipment manifest with {len(equipment_manifest.get('equipment', {}))} items")
    
    # Test 3: Show sample equipment config
    print("\n3. Sample Equipment Configuration:")
    with Session(manager.engine) as session:
        sample = session.exec(select(EquipmentConfig).limit(1)).first()
        if sample:
            print(f"   Equipment ID: {sample.equipment_id}")
            print(f"   Type: {sample.equipment_type}")
            print(f"   Line: {sample.line_id}")
            print(f"   Base Rate: {sample.base_rate}")
            print(f"   MTBF: {sample.mtbf}")
            print(f"   MTTR: {sample.mttr}")
            if sample.failure_patterns_json != '{}':
                patterns = json.loads(sample.failure_patterns_json)
                print(f"   Failure Patterns: {list(patterns.keys())}")
    
    # Test 4: Show sample product config
    print("\n4. Sample Product Configuration:")
    with Session(manager.engine) as session:
        sample = session.exec(select(ProductConfig).limit(1)).first()
        if sample:
            print(f"   Product ID: {sample.product_id}")
            print(f"   Name: {sample.product_name}")
            print(f"   Target Rate: {sample.target_rate_units_per_5min} units/5min")
            print(f"   Standard Cost: ${sample.standard_cost_per_unit}")
            print(f"   Sale Price: ${sample.sale_price_per_unit}")
            print(f"   Scrap Rate (Normal): {sample.scrap_rate_normal*100:.1f}%")
    
    print("\n=== Database Implementation Test Complete ===")
    print("\nNext steps:")
    print("1. Run a simulation: python -m database.cli run-simulation")
    print("2. Run an experiment: python -m database.cli run-experiment")
    print("3. Check status: python -m database.cli status")


if __name__ == "__main__":
    test_database()