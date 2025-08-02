#!/usr/bin/env python3
"""Cross-check API schema with database_schema.yaml and ontology_spec.yaml"""

import requests
import yaml
import json
from pathlib import Path

def get_api_schema():
    """Fetch schema from API"""
    response = requests.get("http://localhost:8000/schema")
    return response.json()

def load_yaml(yaml_path):
    """Load YAML file"""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def cross_check_schemas():
    """Cross-check API schema with YAML files"""
    
    # Load data
    print("📡 Fetching schema from API...")
    api_schema = get_api_schema()
    
    print("📄 Loading database_schema.yaml...")
    db_yaml = load_yaml('ontology/database_schema.yaml')
    
    print("📄 Loading ontology_spec.yaml...")
    ontology = load_yaml('ontology/ontology_spec.yaml')
    
    print("\n" + "=" * 60)
    print("CROSS-CHECK REPORT: API vs YAML Files")
    print("=" * 60)
    
    # Extract columns from API
    api_columns = {}
    for table_name, table_data in api_schema['database']['tables'].items():
        print(f"\n📊 Table: {table_name}")
        print("-" * 40)
        
        for col in table_data['columns']:
            col_name = col['name']
            api_columns[col_name] = {
                'type': col['simple_type'],
                'nullable': col['nullable']
            }
    
    # Check each property in database_schema.yaml
    print("\n🔍 Checking Database Schema Properties:")
    print("-" * 40)
    
    all_match = True
    for prop_name, prop_data in db_yaml['properties'].items():
        sql_column = prop_data['sql_column']
        yaml_type = prop_data['type']
        required = prop_data.get('required', False)
        
        if sql_column in api_columns:
            api_type = api_columns[sql_column]['type']
            api_nullable = api_columns[sql_column]['nullable']
            
            # Check type match
            type_match = yaml_type == api_type
            
            # Check nullable/required match
            nullable_match = (not required) == api_nullable
            
            if type_match and nullable_match:
                status = "✅"
            else:
                status = "⚠️"
                all_match = False
                
            print(f"{status} {prop_name:30} → {sql_column:30}")
            
            if not type_match:
                print(f"   Type mismatch: YAML={yaml_type}, API={api_type}")
            if not nullable_match:
                print(f"   Nullable mismatch: YAML required={required}, API nullable={api_nullable}")
        else:
            print(f"❌ {prop_name:30} → {sql_column:30} (NOT IN API)")
            all_match = False
    
    # Check for API columns not in YAML
    print("\n🔍 Checking for API columns not in YAML:")
    print("-" * 40)
    
    yaml_columns = {prop['sql_column'] for prop in db_yaml['properties'].values()}
    extra_api_columns = set(api_columns.keys()) - yaml_columns
    
    if extra_api_columns:
        print("Found columns in API but not in YAML:")
        for col in sorted(extra_api_columns):
            print(f"  ❌ {col} (type: {api_columns[col]['type']})")
    else:
        print("✅ All API columns are mapped in YAML")
    
    # Check ontology alignment
    print("\n🔍 Checking Ontology Alignment:")
    print("-" * 40)
    
    onto_props = ontology['properties']
    for prop_name in db_yaml['properties'].keys():
        if prop_name in onto_props:
            onto_sql = onto_props[prop_name].get('sql_column', '')
            db_sql = db_yaml['properties'][prop_name]['sql_column']
            
            if onto_sql == db_sql:
                print(f"✅ {prop_name}: {onto_sql}")
            else:
                print(f"⚠️  {prop_name}: ontology={onto_sql}, database={db_sql}")
                all_match = False
        else:
            print(f"❌ {prop_name} missing from ontology")
            all_match = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_match:
        print("✅ PERFECT ALIGNMENT between API, Database Schema, and Ontology!")
    else:
        print("⚠️  Some misalignments detected. Review above.")
    print("=" * 60)
    
    # Statistics
    print(f"\n📈 Summary:")
    print(f"  - API columns: {len(api_columns)}")
    print(f"  - Database YAML properties: {len(db_yaml['properties'])}")
    print(f"  - Ontology properties: {len(onto_props)}")
    print(f"  - API database type: {api_schema['database']['type']}")
    print(f"  - API database file: {api_schema['database']['file']}")

if __name__ == "__main__":
    cross_check_schemas()