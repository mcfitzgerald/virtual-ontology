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
        
    def build_graph(self) -> nx.DiGraph:
        """Build the complete graph from ontology data."""
        self._add_class_nodes()
        self._add_property_nodes()
        self._add_relationship_nodes()
        self._add_business_rule_nodes()
        self._add_edges()
        self._add_cross_ontology_edges()
        self._calculate_metrics()
        
        return self.graph
    
    def _add_class_nodes(self):
        """Add class nodes to the graph."""
        for cls in self.data['classes']:
            self.graph.add_node(
                cls['id'],
                label=cls['name'],
                node_type='class',
                namespace=cls['namespace'],
                description=cls['description'],
                level=cls['level'],
                parent=cls['parent'],
                conditions=json.dumps(cls['conditions']),
                maps_to=json.dumps(cls['maps_to'])
            )
            
            # Add inheritance edges
            if cls['parent']:
                parent_id = f"{cls['namespace']}:{cls['parent']}"
                self.graph.add_edge(parent_id, cls['id'], edge_type='inheritance')
    
    def _add_property_nodes(self):
        """Add property nodes to the graph."""
        for prop in self.data['properties']:
            self.graph.add_node(
                prop['id'],
                label=prop['name'],
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
                examples=json.dumps(prop['examples'])
            )
            
            # Add property-to-class edges
            if prop['class']:
                class_id = f"{prop['namespace']}:{prop['class']}"
                if class_id in self.graph:
                    self.graph.add_edge(class_id, prop['id'], edge_type='has_property')
    
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
        """Add business rule nodes to the graph."""
        for rule in self.data['business_rules']:
            self.graph.add_node(
                rule['id'],
                label=rule['name'],
                node_type='business_rule',
                namespace=rule['namespace'],
                description=rule['description'],
                when=json.dumps(rule['when']),
                implies=rule['implies'],
                sql_hint=rule['sql_hint']
            )
            
            # Add rule-to-class edges
            if 'class' in rule['when']:
                class_id = f"{rule['namespace']}:{rule['when']['class']}"
                if class_id in self.graph:
                    self.graph.add_edge(class_id, rule['id'], edge_type='has_rule')
    
    def _add_edges(self):
        """Add relationship edges between classes."""
        for rel in self.data['relationships']:
            if rel['from'] and rel['to']:
                from_id = f"{rel['namespace']}:{rel['from']}"
                to_id = f"{rel['namespace']}:{rel['to']}"
                
                if from_id in self.graph and to_id in self.graph:
                    self.graph.add_edge(
                        from_id, 
                        to_id,
                        edge_type='relationship',
                        relationship=rel['name'],
                        description=rel['description']
                    )
    
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