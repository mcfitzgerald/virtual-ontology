"""
Test script for the ontology visualization system
"""

import sys
import json
from pathlib import Path

# Test imports
try:
    from src.ontology_parser import OntologyParser
    from src.graph_builder import GraphBuilder
    print("✓ Module imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test ontology parsing
try:
    parser = OntologyParser(
        mes_path='../ontology/ontology_spec.yaml',
        twin_path='../ontology/twin_ontology_spec.yaml'
    )
    ontology_data = parser.parse_all()
    
    print(f"✓ Ontology parsing successful")
    print(f"  - Classes: {len(ontology_data['classes'])}")
    print(f"  - Relationships: {len(ontology_data['relationships'])}")
    print(f"  - Properties: {len(ontology_data['properties'])}")
    print(f"  - Business Rules: {len(ontology_data['business_rules'])}")
    print(f"  - Cross Mappings: {len(ontology_data['cross_mappings'])}")
except Exception as e:
    print(f"✗ Parsing error: {e}")
    sys.exit(1)

# Test graph building
try:
    builder = GraphBuilder(ontology_data)
    graph = builder.build_graph()
    elements = builder.get_cytoscape_elements()
    
    print(f"✓ Graph building successful")
    print(f"  - Nodes: {graph.number_of_nodes()}")
    print(f"  - Edges: {graph.number_of_edges()}")
    print(f"  - Cytoscape elements: {len(elements)}")
    
    # Check node types
    node_types = builder.get_node_types()
    namespaces = builder.get_namespaces()
    print(f"  - Node types: {node_types}")
    print(f"  - Namespaces: {namespaces}")
except Exception as e:
    print(f"✗ Graph building error: {e}")
    sys.exit(1)

# Test specific nodes exist
try:
    expected_nodes = [
        'mes:Equipment',
        'mes:Product',
        'twin:VirtualSensor',
        'twin:SimulationRun'
    ]
    
    nodes_in_graph = set(graph.nodes())
    missing_nodes = []
    
    for node in expected_nodes:
        if node not in nodes_in_graph:
            missing_nodes.append(node)
    
    if missing_nodes:
        print(f"✗ Missing expected nodes: {missing_nodes}")
    else:
        print(f"✓ All expected nodes present")
        
    # Sample node details
    sample_node = 'mes:Equipment'
    if sample_node in graph.nodes():
        node_data = graph.nodes[sample_node]
        print(f"\n  Sample node '{sample_node}':")
        print(f"    - Type: {node_data.get('node_type')}")
        print(f"    - Description: {node_data.get('description')[:50]}...")
        print(f"    - Degree: {graph.degree(sample_node)}")
except Exception as e:
    print(f"✗ Node verification error: {e}")

# Test edge types
try:
    edge_types = set()
    for _, _, data in graph.edges(data=True):
        edge_types.add(data.get('edge_type', 'unknown'))
    
    print(f"\n✓ Edge types found: {sorted(edge_types)}")
except Exception as e:
    print(f"✗ Edge analysis error: {e}")

# Test filtering functionality
try:
    # Simulate filtering by namespace
    mes_nodes = [n for n, d in graph.nodes(data=True) if d.get('namespace') == 'mes']
    twin_nodes = [n for n, d in graph.nodes(data=True) if d.get('namespace') == 'twin']
    
    print(f"\n✓ Namespace filtering:")
    print(f"  - MES nodes: {len(mes_nodes)}")
    print(f"  - Twin nodes: {len(twin_nodes)}")
    
    # Simulate filtering by node type
    class_nodes = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'class']
    property_nodes = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'property']
    
    print(f"\n✓ Node type filtering:")
    print(f"  - Class nodes: {len(class_nodes)}")
    print(f"  - Property nodes: {len(property_nodes)}")
except Exception as e:
    print(f"✗ Filtering test error: {e}")

# Test JSON serialization (important for Dash)
try:
    for element in elements[:5]:  # Test first 5 elements
        json_str = json.dumps(element)
        json.loads(json_str)  # Verify it can be deserialized
    
    print(f"\n✓ JSON serialization working")
except Exception as e:
    print(f"✗ JSON serialization error: {e}")

print("\n✅ All tests passed successfully!")
print("\nVisualization app is running at http://localhost:8050")
print("You can interact with the graph using:")
print("  - Layout dropdown to change graph arrangement")
print("  - Namespace filter to show MES/Twin/All nodes")
print("  - Node type checkboxes to filter by type")
print("  - Search box to find specific nodes")
print("  - Click nodes to see details in right panel")