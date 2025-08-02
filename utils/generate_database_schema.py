#!/usr/bin/env python3
"""
Generate database schema YAML from FastAPI schema endpoint
Maps database columns to ontology properties automatically
"""

import requests
import yaml
from datetime import datetime
from typing import Dict, Any, List

# Configuration
API_URL = "http://localhost:8000/schema"
OUTPUT_FILE = "database_schema_lean.yaml"
ONTOLOGY_NAMESPACE = "mes"  # Should match ontology namespace

def get_schema_from_api() -> Dict[str, Any]:
    """Fetch schema information from API"""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching schema: {e}")
        exit(1)

def map_column_to_property(column_name: str) -> str:
    """Map database column name to ontology property name"""
    # Convert snake_case to camelCase
    parts = column_name.split('_')
    if len(parts) > 1:
        # Special cases
        if column_name == "production_order_id":
            return "hasOrderID"
        elif column_name == "line_id":
            return "hasLineID"
        elif column_name == "equipment_id":
            return "hasEquipmentID"
        elif column_name == "product_id":
            return "hasProductID"
        elif column_name == "oee_score":
            return "hasOEEScore"
        
        # General conversion
        return 'has' + ''.join(word.capitalize() for word in parts)
    return 'has' + column_name.capitalize()

def get_business_name(column_name: str) -> str:
    """Generate business-friendly name"""
    special_names = {
        "oee_score": "OEE",
        "good_units_produced": "Good Units",
        "scrap_units_produced": "Scrap Units",
        "target_rate_units_per_5min": "Target Rate (5 min)",
        "standard_cost_per_unit": "Unit Cost",
        "sale_price_per_unit": "Sale Price",
        "availability_score": "Availability %",
        "performance_score": "Performance %",
        "quality_score": "Quality %",
        "downtime_reason": "Downtime Code"
    }
    
    if column_name in special_names:
        return special_names[column_name]
    
    # Default: capitalize and replace underscores
    return ' '.join(word.capitalize() for word in column_name.split('_'))

def get_validation_rules(column_name: str, column_info: Dict) -> Dict:
    """Generate validation rules based on column name and type"""
    validation = {}
    
    # Score fields should be 0-100
    if 'score' in column_name:
        validation['min'] = 0
        validation['max'] = 100
    
    # Units should be non-negative
    if 'units' in column_name or 'rate' in column_name:
        validation['min'] = 0
    
    # Cost and price should be non-negative
    if 'cost' in column_name or 'price' in column_name:
        validation['min'] = 0
    
    # Status fields
    if column_name == 'machine_status':
        validation['values'] = ['Running', 'Stopped']
    
    # Line ID
    if column_name == 'line_id':
        validation['values'] = ['1', '2', '3']
    
    return validation if validation else None

def get_unit_label(column_name: str) -> str:
    """Get unit label for numeric fields"""
    if 'score' in column_name:
        return 'percent'
    elif 'cost' in column_name or 'price' in column_name:
        return 'USD'
    elif 'units' in column_name or 'rate' in column_name:
        return 'units per 5 min'
    return None

def generate_lean_schema(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate lean database schema from API data"""
    
    # Get the first (and only) table
    table_name = list(api_data['database']['tables'].keys())[0]
    table_info = api_data['database']['tables'][table_name]
    
    # Build properties from columns
    properties = {}
    for column in table_info['columns']:
        col_name = column['name']
        
        # Skip the id column (it's just a primary key)
        if col_name == 'id':
            continue
        
        prop = {
            'type': column['simple_type'],
            'sql_column': col_name,
            'required': not column['nullable']
        }
        
        # Add business name
        business_name = get_business_name(col_name)
        if business_name != col_name:
            prop['business_name'] = business_name
        
        # Add validation if applicable
        validation = get_validation_rules(col_name, column)
        if validation:
            prop['validation'] = validation
        
        # Add unit if applicable
        unit = get_unit_label(col_name)
        if unit:
            prop['unit'] = unit
        
        # Map to ontology property
        ontology_property = map_column_to_property(col_name)
        properties[ontology_property] = prop
    
    # Build the lean schema structure
    schema = {
        'database': {
            'name': 'MES Database',
            'type': api_data['database']['type'],
            'file': api_data['database']['file'],
            'description': 'Manufacturing Execution System database with production metrics'
        },
        
        'table': {
            'name': table_name,
            'description': 'Main MES data table with 5-minute production snapshots',
            'primary_key': 'id',
            'indexes': [idx['columns'][0] for idx in table_info['indexes']]
        },
        
        'properties': properties,
        
        'mappings': {
            'ontology_namespace': ONTOLOGY_NAMESPACE,
            'auto_mapped': True,
            'mapping_rules': {
                'snake_case_to_camelCase': True,
                'prefix_with_has': True
            }
        },
        
        'metadata': {
            'generated': datetime.now().isoformat(),
            'source': 'FastAPI schema endpoint',
            'api_endpoint': '/data'
        }
    }
    
    return schema

def main():
    """Main execution"""
    print(f"Fetching schema from {API_URL}...")
    api_data = get_schema_from_api()
    
    print("Generating lean database schema...")
    schema = generate_lean_schema(api_data)
    
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"✓ Database schema generated successfully: {OUTPUT_FILE}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  - Database: {schema['database']['type']}")
    print(f"  - Table: {schema['table']['name']}")
    print(f"  - Properties: {len(schema['properties'])}")
    print(f"  - Indexes: {len(schema['table']['indexes'])}")

if __name__ == "__main__":
    main()