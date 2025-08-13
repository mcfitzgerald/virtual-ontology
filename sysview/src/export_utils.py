"""
Export Utilities Module
Provides functions to export the graph in various formats.
"""

import json
import networkx as nx
from pyvis.network import Network
from pathlib import Path
from typing import Dict, List, Any
import zipfile
import io


def export_to_pyvis(elements: List[Dict]) -> str:
    """
    Export Cytoscape elements to an interactive PyVis HTML string.
    
    Args:
        elements: List of Cytoscape elements (nodes and edges)
    
    Returns:
        HTML string containing the PyVis visualization
    """
    net = Network(height='800px', width='100%', directed=True, notebook=False)
    net.barnes_hut()
    
    # Configure physics
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 95,
                "springConstant": 0.04,
                "damping": 0.09
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100
        }
    }
    """)
    
    # Add nodes from Cytoscape elements
    for element in elements:
        if 'source' not in element.get('data', {}):  # It's a node
            data = element['data']
            color = _get_node_color(data)
            shape = _get_node_shape(data)
            title = _create_node_tooltip(data)
            
            net.add_node(
                data['id'],
                label=data.get('label', data['id']),
                color=color,
                shape=shape,
                title=title,
                size=20 + data.get('degree', 0) * 2
            )
    
    # Add edges from Cytoscape elements
    for element in elements:
        if 'source' in element.get('data', {}):  # It's an edge
            data = element['data']
            edge_type = data.get('edge_type', 'default')
            color = _get_edge_color(edge_type)
            
            net.add_edge(
                data['source'],
                data['target'],
                color=color,
                title=data.get('description', ''),
                arrows='to'
            )
    
    # Return HTML string
    return net.generate_html()


def export_to_obsidian(elements: List[Dict], ontology_data: Dict = None) -> bytes:
    """
    Export Cytoscape elements to Obsidian-compatible markdown files as a zip.
    
    Args:
        elements: List of Cytoscape elements
        ontology_data: Optional original ontology data for richer export
    
    Returns:
        Bytes of zip file containing Obsidian vault
    """
    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Process nodes by namespace
        nodes_by_namespace = {'mes': [], 'twin': [], 'other': []}
        edges_list = []
        
        for element in elements:
            if 'source' not in element.get('data', {}):  # It's a node
                data = element['data']
                namespace = data.get('namespace', 'other')
                if namespace not in nodes_by_namespace:
                    namespace = 'other'
                nodes_by_namespace[namespace].append(data)
            else:  # It's an edge
                edges_list.append(element['data'])
        
        # Create folders and notes for each namespace
        for namespace, nodes in nodes_by_namespace.items():
            if not nodes:
                continue
                
            # Create namespace folder
            folder_name = namespace.upper()
            
            for node in nodes:
                # Create markdown content for node
                content = _create_node_markdown(node, edges_list)
                
                # Add to zip
                file_path = f"{folder_name}/{node.get('label', node['id'])}.md"
                zipf.writestr(file_path, content)
        
        # Create index file
        index_content = _create_obsidian_index(nodes_by_namespace, edges_list)
        zipf.writestr("README.md", index_content)
    
    # Return zip bytes
    zip_buffer.seek(0)
    return zip_buffer.read()


def _create_node_markdown(node: Dict, edges: List[Dict]) -> str:
    """Create markdown content for a node."""
    content = []
    
    # YAML frontmatter
    content.append("---")
    content.append(f"type: {node.get('node_type', 'unknown')}")
    content.append(f"namespace: {node.get('namespace', 'unknown')}")
    content.append(f"id: {node.get('id', '')}")
    content.append("---")
    content.append("")
    
    # Title and description
    content.append(f"# {node.get('label', node.get('id', 'Unknown'))}")
    content.append("")
    if 'description' in node and node['description']:
        content.append(node['description'])
        content.append("")
    
    # Node type specific details
    node_type = node.get('node_type', '')
    
    if node_type == 'class':
        if 'parent' in node and node['parent']:
            content.append("## Parent Class")
            content.append(f"- [[{node['parent']}]]")
            content.append("")
    
    elif node_type == 'property':
        content.append("## Details")
        if 'data_type' in node:
            content.append(f"- **Data Type**: {node['data_type']}")
        if 'sql_column' in node and node['sql_column']:
            content.append(f"- **SQL Column**: `{node['sql_column']}`")
        if 'sql_table' in node and node['sql_table']:
            content.append(f"- **SQL Table**: `{node['sql_table']}`")
        if 'unit' in node and node['unit']:
            content.append(f"- **Unit**: {node['unit']}")
        if 'required' in node:
            content.append(f"- **Required**: {'Yes' if node['required'] else 'No'}")
        content.append("")
    
    elif node_type == 'relationship':
        content.append("## Connection")
        if 'from_class' in node and 'to_class' in node:
            content.append(f"[[{node['from_class']}]] → [[{node['to_class']}]]")
        if 'rel_type' in node:
            content.append(f"- **Type**: {node['rel_type']}")
        if 'sql_hint' in node and node['sql_hint']:
            content.append("")
            content.append("## SQL Hint")
            content.append("```sql")
            content.append(node['sql_hint'])
            content.append("```")
        content.append("")
    
    elif node_type == 'business_rule':
        if 'when' in node:
            content.append("## Conditions")
            try:
                when_data = json.loads(node['when']) if isinstance(node['when'], str) else node['when']
                for key, value in when_data.items():
                    content.append(f"- **{key}**: {value}")
            except:
                content.append(f"- {node['when']}")
            content.append("")
        if 'implies' in node and node['implies']:
            content.append("## Implications")
            content.append(node['implies'])
            content.append("")
    
    # Find connections
    connections = []
    node_id = node.get('id', '')
    
    for edge in edges:
        if edge.get('source') == node_id:
            target_label = edge.get('target', '').split(':')[-1]
            connections.append(f"- → [[{target_label}]]")
        elif edge.get('target') == node_id:
            source_label = edge.get('source', '').split(':')[-1]
            connections.append(f"- ← [[{source_label}]]")
    
    if connections:
        content.append("## Connections")
        content.extend(connections)
        content.append("")
    
    # Tags
    content.append("## Tags")
    tags = [f"#{node.get('node_type', 'node')}", f"#{node.get('namespace', 'unknown')}"]
    content.append(' '.join(tags))
    
    return '\n'.join(content)


def _create_obsidian_index(nodes_by_namespace: Dict, edges: List[Dict]) -> str:
    """Create index file for Obsidian vault."""
    content = []
    content.append("# Ontology Knowledge Graph")
    content.append("")
    content.append("This vault contains the structured representation of the Manufacturing Execution System (MES) and Virtual Twin ontologies.")
    content.append("")
    
    # Statistics
    content.append("## Statistics")
    total_nodes = sum(len(nodes) for nodes in nodes_by_namespace.values())
    content.append(f"- **Total Nodes**: {total_nodes}")
    content.append(f"- **Total Edges**: {len(edges)}")
    content.append("")
    
    # Breakdown by namespace
    content.append("## Namespaces")
    for namespace, nodes in nodes_by_namespace.items():
        if nodes:
            content.append(f"- **{namespace.upper()}**: {len(nodes)} nodes")
    content.append("")
    
    # Node types breakdown
    node_types = {}
    for nodes in nodes_by_namespace.values():
        for node in nodes:
            node_type = node.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
    
    content.append("## Node Types")
    for node_type, count in sorted(node_types.items()):
        content.append(f"- **{node_type}**: {count}")
    content.append("")
    
    content.append("## Navigation")
    content.append("Use Obsidian's Graph View to explore the connections between concepts.")
    content.append("")
    
    content.append("## Tags")
    content.append("#ontology #knowledge_graph #manufacturing #mes #virtual_twin")
    
    return '\n'.join(content)


def _get_node_color(data: Dict) -> str:
    """Get node color based on type and namespace."""
    node_type = data.get('node_type', '')
    namespace = data.get('namespace', '')
    
    if node_type == 'class':
        return '#3498db' if namespace == 'mes' else '#2ecc71'
    elif node_type == 'property':
        return '#85C1E9' if namespace == 'mes' else '#82E0AA'
    elif node_type == 'relationship':
        return '#9b59b6'
    elif node_type == 'business_rule':
        return '#e74c3c'
    else:
        return '#95a5a6'


def _get_node_shape(data: Dict) -> str:
    """Get node shape based on type."""
    node_type = data.get('node_type', '')
    
    shapes = {
        'class': 'box',
        'property': 'ellipse',
        'relationship': 'diamond',
        'business_rule': 'hexagon'
    }
    
    return shapes.get(node_type, 'dot')


def _get_edge_color(edge_type: str) -> str:
    """Get edge color based on type."""
    colors = {
        'inheritance': '#34495e',
        'has_property': '#7f8c8d',
        'relationship': '#9b59b6',
        'cross_mapping': '#f39c12',
        'has_rule': '#e74c3c'
    }
    
    return colors.get(edge_type, '#95a5a6')


def _create_node_tooltip(data: Dict) -> str:
    """Create HTML tooltip for a node."""
    lines = []
    lines.append(f"<b>{data.get('label', 'Unknown')}</b>")
    lines.append(f"Type: {data.get('node_type', 'Unknown')}")
    lines.append(f"Namespace: {data.get('namespace', 'Unknown')}")
    
    if 'description' in data and data['description']:
        desc = data['description']
        if len(desc) > 100:
            desc = desc[:100] + '...'
        lines.append(f"<br>{desc}")
    
    return '<br>'.join(lines)