"""
Ontology Parser Module
Parses YAML ontology specifications and extracts classes, relationships, properties, and business rules.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
import json


class OntologyParser:
    def __init__(self, mes_path: str, twin_path: str):
        """Initialize the parser with paths to ontology files."""
        self.mes_path = Path(mes_path)
        self.twin_path = Path(twin_path)
        self.mes_ontology = None
        self.twin_ontology = None
        
    def load_ontologies(self) -> Tuple[Dict, Dict]:
        """Load both ontology YAML files."""
        with open(self.mes_path, 'r') as f:
            self.mes_ontology = yaml.safe_load(f)
        
        with open(self.twin_path, 'r') as f:
            self.twin_ontology = yaml.safe_load(f)
            
        return self.mes_ontology, self.twin_ontology
    
    def extract_classes(self, ontology: Dict, namespace: str) -> List[Dict]:
        """Extract all classes from an ontology."""
        classes = []
        
        def process_class(name: str, data: Dict, parent: str = None, level: int = 0):
            """Recursively process class and its subclasses."""
            class_info = {
                'id': f"{namespace}:{name}",
                'name': name,
                'namespace': namespace,
                'description': data.get('description', ''),
                'parent': parent,
                'level': level,
                'conditions': data.get('conditions', []),
                'maps_to': data.get('maps_to', {})
            }
            classes.append(class_info)
            
            # Process subclasses
            if 'subclasses' in data:
                for subclass_name, subclass_data in data['subclasses'].items():
                    process_class(subclass_name, subclass_data, name, level + 1)
        
        # Process top-level classes
        if 'classes' in ontology:
            for class_name, class_data in ontology['classes'].items():
                process_class(class_name, class_data)
                
        return classes
    
    def extract_relationships(self, ontology: Dict, namespace: str) -> List[Dict]:
        """Extract all relationships from an ontology."""
        relationships = []
        
        if 'relationships' in ontology:
            for rel_name, rel_data in ontology['relationships'].items():
                rel_info = {
                    'id': f"{namespace}:{rel_name}",
                    'name': rel_name,
                    'namespace': namespace,
                    'from': rel_data.get('from', ''),
                    'to': rel_data.get('to', ''),
                    'description': rel_data.get('description', ''),
                    'type': rel_data.get('type', ''),
                    'sql_hint': rel_data.get('sql_hint', ''),
                    'inverse': rel_data.get('inverse', '')
                }
                relationships.append(rel_info)
                
        return relationships
    
    def extract_properties(self, ontology: Dict, namespace: str) -> List[Dict]:
        """Extract all properties from an ontology."""
        properties = []
        
        if 'properties' in ontology:
            for prop_name, prop_data in ontology['properties'].items():
                prop_info = {
                    'id': f"{namespace}:{prop_name}",
                    'name': prop_name,
                    'namespace': namespace,
                    'class': prop_data.get('class', ''),
                    'type': prop_data.get('type', ''),
                    'description': prop_data.get('description', ''),
                    'sql_column': prop_data.get('sql_column', ''),
                    'sql_table': prop_data.get('sql_table', ''),
                    'unit': prop_data.get('unit', ''),
                    'business_name': prop_data.get('business_name', ''),
                    'required': prop_data.get('required', False),
                    'validation': prop_data.get('validation', {}),
                    'examples': prop_data.get('examples', [])
                }
                properties.append(prop_info)
                
        return properties
    
    def extract_business_rules(self, ontology: Dict, namespace: str) -> List[Dict]:
        """Extract all business rules from an ontology."""
        rules = []
        
        if 'business_rules' in ontology:
            for rule_name, rule_data in ontology['business_rules'].items():
                rule_info = {
                    'id': f"{namespace}:{rule_name}",
                    'name': rule_name,
                    'namespace': namespace,
                    'description': rule_data.get('description', ''),
                    'when': rule_data.get('when', {}),
                    'implies': rule_data.get('implies', ''),
                    'sql_hint': rule_data.get('sql_hint', '')
                }
                rules.append(rule_info)
                
        return rules
    
    def extract_common_queries(self, ontology: Dict, namespace: str) -> List[Dict]:
        """Extract common queries from an ontology."""
        queries = []
        
        if 'common_queries' in ontology:
            for query in ontology['common_queries']:
                query_info = {
                    'id': f"{namespace}:{query.get('name', 'unnamed')}",
                    'name': query.get('name', ''),
                    'namespace': namespace,
                    'question': query.get('question', ''),
                    'involves': query.get('involves', []),
                    'sql_pattern': query.get('sql_pattern', '')
                }
                queries.append(query_info)
                
        return queries
    
    def parse_all(self) -> Dict:
        """Parse both ontologies and extract all components."""
        self.load_ontologies()
        
        # Extract from MES ontology
        mes_classes = self.extract_classes(self.mes_ontology, 'mes')
        mes_relationships = self.extract_relationships(self.mes_ontology, 'mes')
        mes_properties = self.extract_properties(self.mes_ontology, 'mes')
        mes_rules = self.extract_business_rules(self.mes_ontology, 'mes')
        mes_queries = self.extract_common_queries(self.mes_ontology, 'mes')
        
        # Extract from Twin ontology
        twin_classes = self.extract_classes(self.twin_ontology, 'twin')
        twin_relationships = self.extract_relationships(self.twin_ontology, 'twin')
        twin_properties = self.extract_properties(self.twin_ontology, 'twin')
        twin_rules = self.extract_business_rules(self.twin_ontology, 'twin')
        twin_queries = self.extract_common_queries(self.twin_ontology, 'twin')
        
        # Extract cross-system mappings
        cross_mappings = self._extract_cross_mappings()
        
        return {
            'classes': mes_classes + twin_classes,
            'relationships': mes_relationships + twin_relationships,
            'properties': mes_properties + twin_properties,
            'business_rules': mes_rules + twin_rules,
            'common_queries': mes_queries + twin_queries,
            'cross_mappings': cross_mappings,
            'metadata': {
                'mes': self.mes_ontology.get('ontology', {}),
                'twin': self.twin_ontology.get('ontology', {})
            }
        }
    
    def _extract_cross_mappings(self) -> List[Dict]:
        """Extract cross-ontology mappings."""
        mappings = []
        
        # Extract mappings from Twin ontology that reference MES
        if 'system_mappings' in self.twin_ontology:
            if 'mes_system' in self.twin_ontology['system_mappings']:
                mes_mappings = self.twin_ontology['system_mappings']['mes_system']
                if 'mappings' in mes_mappings:
                    for mapping in mes_mappings['mappings']:
                        mapping_info = {
                            'from_concept': f"twin:{mapping.get('our_concept', '')}",
                            'to_concept': f"mes:{mapping.get('their_concept', '')}",
                            'join_key': mapping.get('join_key', ''),
                            'notes': mapping.get('notes', '')
                        }
                        mappings.append(mapping_info)
        
        return mappings