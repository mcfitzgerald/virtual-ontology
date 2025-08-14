"""
Final test of the fixed ontology visualization system
"""

from src.ontology_parser import OntologyParser
from src.graph_builder import GraphBuilder
import networkx as nx

def test_graph_structure():
    """Test the graph structure after fixes."""
    # Parse and build graph
    parser = OntologyParser(
        mes_path='../ontology/ontology_spec.yaml',
        twin_path='../ontology/twin_ontology_spec.yaml'
    )
    ontology_data = parser.parse_all()
    builder = GraphBuilder(ontology_data)
    graph = builder.build_graph()
    
    print("=" * 60)
    print("ONTOLOGY GRAPH STRUCTURE TEST RESULTS")
    print("=" * 60)
    print()
    
    # Basic metrics
    print("📊 GRAPH METRICS:")
    print(f"  Total nodes: {graph.number_of_nodes()}")
    print(f"  Total edges: {graph.number_of_edges()}")
    print(f"  Graph density: {nx.density(graph):.3f}")
    print()
    
    # Node type breakdown
    print("📦 NODE TYPES:")
    node_types = {}
    for node, data in graph.nodes(data=True):
        node_type = data.get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    for node_type, count in sorted(node_types.items()):
        print(f"  {node_type}: {count}")
    
    # Check for relationship nodes (should be 0!)
    relationship_nodes = [n for n, d in graph.nodes(data=True) 
                         if d.get('node_type') == 'relationship']
    if relationship_nodes:
        print(f"  ❌ ERROR: Found {len(relationship_nodes)} relationship nodes!")
        print(f"     These should be edges, not nodes: {relationship_nodes[:3]}")
    else:
        print(f"  ✅ No relationship nodes (correct!)")
    print()
    
    # Edge type breakdown
    print("🔗 EDGE TYPES:")
    edge_types = {}
    for _, _, data in graph.edges(data=True):
        edge_type = data.get('edge_type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    for edge_type, count in sorted(edge_types.items()):
        print(f"  {edge_type}: {count}")
    print()
    
    # Cross-namespace analysis
    print("🌐 CROSS-NAMESPACE CONNECTIONS:")
    cross_edges = []
    for source, target, data in graph.edges(data=True):
        source_ns = source.split(':')[0] if ':' in source else 'unknown'
        target_ns = target.split(':')[0] if ':' in target else 'unknown'
        if source_ns != target_ns:
            cross_edges.append((source, target, data))
    
    print(f"  Total cross-namespace edges: {len(cross_edges)}")
    if cross_edges:
        print("  Examples:")
        for source, target, data in cross_edges[:3]:
            rel_name = data.get('relationship', data.get('edge_type', 'unknown'))
            print(f"    {source} -> {target}")
            print(f"      Relationship: {rel_name}")
            print(f"      Description: {data.get('description', 'N/A')[:50]}...")
    print()
    
    # Connectivity analysis
    print("🔌 CONNECTIVITY ANALYSIS:")
    disconnected = [n for n in graph.nodes() if graph.degree(n) == 0]
    if disconnected:
        print(f"  ⚠️  {len(disconnected)} disconnected nodes found:")
        for node in disconnected[:5]:
            node_data = graph.nodes[node]
            print(f"    - {node} (type: {node_data.get('node_type', 'unknown')})")
    else:
        print("  ✅ All nodes are connected!")
    
    # Find most connected nodes
    node_degrees = [(n, graph.degree(n)) for n in graph.nodes()]
    node_degrees.sort(key=lambda x: x[1], reverse=True)
    print("\n  Most connected nodes:")
    for node, degree in node_degrees[:5]:
        node_data = graph.nodes[node]
        print(f"    {node}: {degree} connections")
        print(f"      Type: {node_data.get('node_type')}")
        print(f"      Description: {node_data.get('description', 'N/A')[:40]}...")
    print()
    
    # Test specific namespace resolution cases
    print("🔍 NAMESPACE RESOLUTION TESTS:")
    test_cases = [
        ("twin:observes should connect to mes:Equipment", 
         "twin:VirtualSensor", "mes:Equipment"),
        ("twin:simulatesEquipment should connect to mes:Equipment",
         "twin:SimulationRun", "mes:Equipment"),
        ("twin:synchronizedWith should connect to mes:Equipment",
         "twin:TwinState", "mes:Equipment")
    ]
    
    for test_name, expected_source, expected_target in test_cases:
        edges = list(graph.edges(expected_source, data=True))
        found = False
        for _, target, data in edges:
            if target == expected_target:
                found = True
                break
        
        if found:
            print(f"  ✅ {test_name}")
        else:
            print(f"  ❌ {test_name}")
    print()
    
    # Additional features
    print("📚 ADDITIONAL FEATURES:")
    if 'glossary' in ontology_data and ontology_data['glossary']:
        print(f"  ✅ Glossary: {len(ontology_data['glossary'])} terms")
        sample_terms = list(ontology_data['glossary'].keys())[:3]
        print(f"     Sample terms: {', '.join(sample_terms)}")
    else:
        print("  ❌ No glossary found")
    
    if 'metadata' in ontology_data:
        print(f"  ✅ Metadata preserved for both ontologies")
    
    if 'common_queries' in ontology_data:
        print(f"  ✅ Common queries: {len(ontology_data['common_queries'])}")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY:")
    issues = []
    successes = []
    
    if not relationship_nodes:
        successes.append("Relationship nodes removed successfully")
    else:
        issues.append(f"{len(relationship_nodes)} relationship nodes still exist")
    
    if cross_edges:
        successes.append(f"{len(cross_edges)} cross-namespace connections working")
    else:
        issues.append("No cross-namespace connections found")
    
    if disconnected:
        issues.append(f"{len(disconnected)} disconnected nodes remain")
    else:
        successes.append("All nodes connected")
    
    print("✅ Successes:")
    for success in successes:
        print(f"  - {success}")
    
    if issues:
        print("\n⚠️  Issues to address:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n🎉 All tests passed!")
    
    print("=" * 60)
    
    return graph, ontology_data

if __name__ == "__main__":
    graph, data = test_graph_structure()