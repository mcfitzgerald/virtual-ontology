"""
Graph Builder Module
Constructs NetworkX graph from parsed ontology data and prepares it for visualization.
"""

import networkx as nx
from typing import Dict, List, Any, Tuple
import json


class GraphBuilder:
    def __init__(self, ontology_data: Dict):
        """Initialize with parsed ontology data."""
        self.data = ontology_data
        self.graph = nx.DiGraph()
        self.class_registry = {}  # Maps class names to their full IDs
        
    def build_graph(self) -> nx.DiGraph:
        """Build the complete graph from ontology data."""
        # First, build the class registry for namespace resolution
        self._build_class_registry()
        
        # Add nodes
        self._add_class_nodes()
        self._add_property_nodes()
        # Removed: self._add_relationship_nodes() - relationships are edges, not nodes
        self._add_business_rule_nodes()
        
        # Add edges (includes relationships)
        self._add_edges()
        self._add_cross_ontology_edges()
        
        # Calculate metrics
        self._calculate_metrics()
        
        return self.graph
    
    def _build_class_registry(self):
        """Build a registry of all classes for namespace resolution."""
        self.class_registry = {'mes': set(), 'twin': set()}
        
        for cls in self.data.get('classes', []):
            namespace = cls.get('namespace', '')
            class_name = cls.get('name', '')
            if namespace and class_name:
                if namespace not in self.class_registry:
                    self.class_registry[namespace] = set()
                self.class_registry[namespace].add(class_name)
    
    def _resolve_class_name(self, class_name: str, source_namespace: str) -> str:
        """Resolve a class name to its full ID, handling cross-namespace references."""
        if not class_name:
            return None
            
        # First, try with the source namespace
        full_id = f"{source_namespace}:{class_name}"
        if full_id in self.graph:
            return full_id
        
        # For twin namespace, check if it's referring to a MES class
        if source_namespace == 'twin' and class_name in self.class_registry.get('mes', set()):
            return f"mes:{class_name}"
        
        # For mes namespace, check if it's referring to a twin class
        if source_namespace == 'mes' and class_name in self.class_registry.get('twin', set()):
            return f"twin:{class_name}"
        
        # Try all namespaces as fallback
        for ns in self.class_registry:
            if class_name in self.class_registry[ns]:
                return f"{ns}:{class_name}"
        
        # Not found - return None to handle gracefully
        return None
    
    def _format_label(self, text: str, node_type: str = 'class') -> str:
        """Format labels for display based on node type."""
        # Set max length based on node type
        if node_type == 'property':
            max_length = 15
        elif node_type == 'business_rule':
            max_length = 18
        else:  # class or other
            max_length = 20
        
        if len(text) > max_length:
            # Try to break at word boundary
            if ' ' in text[:max_length]:
                cut_point = text[:max_length].rfind(' ')
                if cut_point > 5:  # Ensure we don't cut too early
                    return text[:cut_point] + '...'
            # Fall back to simple truncation
            return text[:max_length-3] + '...'
        return text
    
    def _calculate_node_dimensions(self, label: str, node_type: str = 'class') -> tuple:
        """Calculate appropriate width and height for a node based on its label."""
        # Base dimensions for each node type
        base_dims = {
            'class': (60, 40),
            'property': (50, 30),
            'business_rule': (55, 45),
            'relationship': (50, 35)
        }
        
        base_width, base_height = base_dims.get(node_type, (60, 40))
        
        # Calculate width based on label length (approximately 6 pixels per character)
        char_width = 6
        padding = 20
        label_width = len(label) * char_width + padding
        
        # Use the larger of base width or calculated width
        width = max(base_width, min(label_width, 150))  # Cap at 150px
        
        # Height can stay mostly the same, with slight adjustments for multi-word labels
        if ' ' in label and len(label) > 15:
            height = base_height + 10
        else:
            height = base_height
            
        return width, height
    
    def _add_class_nodes(self):
        """Add class nodes to the graph."""
        for cls in self.data['classes']:
            label = self._format_label(cls['name'], 'class')
            width, height = self._calculate_node_dimensions(cls['name'], 'class')
            
            self.graph.add_node(
                cls['id'],
                label=label,
                full_name=cls['name'],
                node_type='class',
                namespace=cls['namespace'],
                description=cls['description'],
                level=cls['level'],
                parent=cls['parent'],
                conditions=json.dumps(cls['conditions']),
                maps_to=json.dumps(cls['maps_to']),
                width=width,
                height=height
            )
            
            # Add inheritance edges
            if cls['parent']:
                parent_id = f"{cls['namespace']}:{cls['parent']}"
                self.graph.add_edge(parent_id, cls['id'], edge_type='inheritance')
    
    def _add_property_nodes(self):
        """Add property nodes to the graph, skipping orphans."""
        orphaned_props = []
        
        for prop in self.data['properties']:
            # First check if parent class exists
            class_id = None
            if prop['class']:
                class_id = self._resolve_class_name(prop['class'], prop['namespace'])
            
            if class_id and class_id in self.graph:
                # Parent exists, add the property
                label = self._format_label(prop['name'], 'property')
                width, height = self._calculate_node_dimensions(prop['name'], 'property')
                
                self.graph.add_node(
                    prop['id'],
                    label=label,
                    full_name=prop['name'],  # Keep full name for tooltips
                    node_type='property',
                    namespace=prop['namespace'],
                    description=prop['description'],
                    data_type=prop['type'],
                    sql_column=prop['sql_column'],
                    sql_table=prop['sql_table'],
                    unit=prop['unit'],
                    business_name=prop['business_name'],
                    required=prop['required'],
                    validation=json.dumps(prop['validation']),
                    examples=json.dumps(prop['examples']),
                    width=width,
                    height=height
                )
                # Add edge to parent class
                self.graph.add_edge(class_id, prop['id'], edge_type='has_property')
            else:
                # No parent class found, skip this property
                orphaned_props.append(prop['name'])
        
        if orphaned_props:
            print(f"Skipped {len(orphaned_props)} orphaned properties: {', '.join(orphaned_props[:5])}...")
    
    def _add_relationship_nodes(self):
        """Add relationship nodes to the graph."""
        for rel in self.data['relationships']:
            self.graph.add_node(
                rel['id'],
                label=rel['name'],
                node_type='relationship',
                namespace=rel['namespace'],
                description=rel['description'],
                from_class=rel['from'],
                to_class=rel['to'],
                rel_type=rel['type'],
                sql_hint=rel['sql_hint'],
                inverse=rel['inverse']
            )
    
    def _add_business_rule_nodes(self):
        """Add business rule nodes with improved connection logic."""
        orphaned_rules = []
        
        for rule in self.data['business_rules']:
            # Try to find the referenced class
            class_id = None
            if 'when' in rule and 'class' in rule['when']:
                class_name = rule['when']['class']
                # Use namespace resolver for better matching
                class_id = self._resolve_class_name(class_name, rule['namespace'])
            
            if class_id and class_id in self.graph:
                # Parent class exists, add the rule
                label = self._format_label(rule['name'], 'business_rule')
                width, height = self._calculate_node_dimensions(rule['name'], 'business_rule')
                
                self.graph.add_node(
                    rule['id'],
                    label=label,
                    full_name=rule['name'],
                    node_type='business_rule',
                    namespace=rule['namespace'],
                    description=rule['description'],
                    when=json.dumps(rule['when']),
                    implies=rule['implies'],
                    sql_hint=rule['sql_hint'],
                    width=width,
                    height=height
                )
                # Add edge to the class
                self.graph.add_edge(class_id, rule['id'], edge_type='has_rule')
            else:
                # No valid class found, skip this rule
                orphaned_rules.append(rule['name'])
        
        if orphaned_rules:
            print(f"Skipped {len(orphaned_rules)} orphaned business rules: {', '.join(orphaned_rules)}")
    
    def _add_edges(self):
        """Add relationship edges between classes with namespace resolution."""
        for rel in self.data['relationships']:
            if rel['from'] and rel['to']:
                # Resolve class names with namespace awareness
                from_id = self._resolve_class_name(rel['from'], rel['namespace'])
                to_id = self._resolve_class_name(rel['to'], rel['namespace'])
                
                if from_id and to_id:
                    # Both classes exist, create the edge
                    self.graph.add_edge(
                        from_id, 
                        to_id,
                        edge_type='relationship',
                        relationship=rel['name'],
                        relationship_type=rel['type'],
                        description=rel['description'],
                        namespace=rel['namespace']
                    )
                else:
                    # Log warning about missing classes
                    missing = []
                    if not from_id:
                        missing.append(f"{rel['namespace']}:{rel['from']}")
                    if not to_id:
                        missing.append(f"{rel['namespace']}:{rel['to']}")
                    print(f"Warning: Relationship '{rel['name']}' references missing classes: {missing}")
    
    def _add_cross_ontology_edges(self):
        """Add cross-ontology mapping edges."""
        for mapping in self.data['cross_mappings']:
            from_id = mapping['from_concept']
            to_id = mapping['to_concept']
            
            if from_id in self.graph and to_id in self.graph:
                self.graph.add_edge(
                    from_id,
                    to_id,
                    edge_type='cross_mapping',
                    join_key=mapping['join_key'],
                    notes=mapping['notes']
                )
    
    def _calculate_metrics(self):
        """Calculate graph metrics for each node."""
        # Calculate centrality metrics
        try:
            betweenness = nx.betweenness_centrality(self.graph)
            for node, centrality in betweenness.items():
                self.graph.nodes[node]['betweenness_centrality'] = centrality
        except:
            pass  # Handle if graph is not suitable for centrality calculation
        
        # Calculate degree
        for node in self.graph.nodes():
            self.graph.nodes[node]['degree'] = self.graph.degree(node)
            self.graph.nodes[node]['in_degree'] = self.graph.in_degree(node)
            self.graph.nodes[node]['out_degree'] = self.graph.out_degree(node)
    
    def get_cytoscape_elements(self) -> List[Dict]:
        """Convert NetworkX graph to Cytoscape elements format."""
        elements = []
        
        # Add nodes
        for node_id, data in self.graph.nodes(data=True):
            node_element = {
                'data': {
                    'id': node_id,
                    'label': data.get('label', node_id),
                    **data  # Include all node attributes
                },
                'classes': f"{data.get('node_type', 'default')} {data.get('namespace', 'default')}"
            }
            elements.append(node_element)
        
        # Add edges
        for source, target, data in self.graph.edges(data=True):
            edge_element = {
                'data': {
                    'id': f"{source}-{target}",
                    'source': source,
                    'target': target,
                    **data  # Include all edge attributes
                },
                'classes': data.get('edge_type', 'default')
            }
            elements.append(edge_element)
        
        return elements
    
    def get_node_types(self) -> List[str]:
        """Get all unique node types in the graph."""
        node_types = set()
        for _, data in self.graph.nodes(data=True):
            node_types.add(data.get('node_type', 'unknown'))
        return sorted(list(node_types))
    
    def get_namespaces(self) -> List[str]:
        """Get all unique namespaces in the graph."""
        namespaces = set()
        for _, data in self.graph.nodes(data=True):
            namespaces.add(data.get('namespace', 'unknown'))
        return sorted(list(namespaces))