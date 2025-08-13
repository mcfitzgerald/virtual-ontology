"""
Export Utilities Module
Provides functions to export the graph in various formats.
"""

import json
import networkx as nx
from pyvis.network import Network
from pathlib import Path
from typing import Dict, List, Any


def export_to_pyvis(graph: nx.DiGraph, output_path: str = 'ontology_graph.html'):
    """Export the graph to an interactive PyVis HTML file."""
    net = Network(height='800px', width='100%', directed=True)
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
    
    # Add nodes with styling
    for node_id, data in graph.nodes(data=True):
        color = _get_node_color(data)
        shape = _get_node_shape(data)
        title = _create_node_tooltip(data)
        
        net.add_node(
            node_id,
            label=data.get('label', node_id),
            color=color,
            shape=shape,
            title=title,
            size=20 + data.get('degree', 0) * 2
        )
    
    # Add edges
    for source, target, data in graph.edges(data=True):
        edge_type = data.get('edge_type', 'default')
        color = _get_edge_color(edge_type)
        
        net.add_edge(
            source,
            target,
            color=color,
            title=data.get('description', ''),
            arrows='to'
        )
    
    # Save the network
    net.save_graph(output_path)
    return output_path


def export_to_obsidian(ontology_data: Dict, output_dir: str = 'obsidian_vault'):
    """Export ontology to Obsidian-compatible markdown files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create folders for different namespaces
    mes_path = output_path / 'MES'
    twin_path = output_path / 'Twin'
    mes_path.mkdir(exist_ok=True)
    twin_path.mkdir(exist_ok=True)
    
    # Export classes
    for cls in ontology_data['classes']:
        _create_class_note(cls, output_path)
    
    # Export properties
    props_path = output_path / 'Properties'
    props_path.mkdir(exist_ok=True)
    for prop in ontology_data['properties']:
        _create_property_note(prop, props_path)
    
    # Export relationships
    rels_path = output_path / 'Relationships'
    rels_path.mkdir(exist_ok=True)
    for rel in ontology_data['relationships']:
        _create_relationship_note(rel, rels_path)
    
    # Export business rules
    rules_path = output_path / 'BusinessRules'
    rules_path.mkdir(exist_ok=True)
    for rule in ontology_data['business_rules']:
        _create_business_rule_note(rule, rules_path)
    
    # Create index file
    _create_index_note(ontology_data, output_path)
    
    return str(output_path)


def _create_class_note(cls: Dict, base_path: Path):
    """Create an Obsidian note for a class."""
    namespace = cls['namespace'].upper()
    folder = base_path / namespace
    folder.mkdir(exist_ok=True)
    
    file_path = folder / f"{cls['name']}.md"
    
    content = []
    
    # YAML frontmatter
    content.append("---")
    content.append(f"type: class")
    content.append(f"namespace: {cls['namespace']}")
    if cls['parent']:
        content.append(f"parent: {cls['parent']}")
    content.append(f"level: {cls['level']}")
    content.append("---")
    content.append("")
    
    # Title and description
    content.append(f"# {cls['name']}")
    content.append("")
    content.append(cls['description'])
    content.append("")
    
    # Parent class link
    if cls['parent']:
        content.append("## Parent Class")
        content.append(f"- [[{cls['parent']}]]")
        content.append("")
    
    # Conditions
    if cls['conditions']:
        content.append("## Conditions")
        for cond in cls['conditions']:
            content.append(f"- {cond.get('field', '')} {cond.get('operator', '')} {cond.get('value', '')}")
        content.append("")
    
    # Cross-system mappings
    if cls['maps_to']:
        content.append("## Maps To")
        for system, concept in cls['maps_to'].items():
            content.append(f"- **{system}**: {concept}")
        content.append("")
    
    # Tags
    content.append("## Tags")
    content.append(f"#class #{namespace} #{cls['name'].replace(' ', '_')}")
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(content))


def _create_property_note(prop: Dict, props_path: Path):
    """Create an Obsidian note for a property."""
    file_path = props_path / f"{prop['name']}.md"
    
    content = []
    
    # YAML frontmatter
    content.append("---")
    content.append(f"type: property")
    content.append(f"namespace: {prop['namespace']}")
    content.append(f"class: {prop['class']}")
    content.append(f"datatype: {prop['type']}")
    content.append("---")
    content.append("")
    
    # Title and description
    content.append(f"# {prop['name']}")
    content.append("")
    content.append(prop['description'])
    content.append("")
    
    # Class link
    if prop['class']:
        content.append("## Belongs To")
        content.append(f"- [[{prop['class']}]]")
        content.append("")
    
    # Technical details
    content.append("## Technical Details")
    content.append(f"- **Data Type**: {prop['type']}")
    if prop['sql_column']:
        content.append(f"- **SQL Column**: `{prop['sql_column']}`")
    if prop['sql_table']:
        content.append(f"- **SQL Table**: `{prop['sql_table']}`")
    if prop['unit']:
        content.append(f"- **Unit**: {prop['unit']}")
    if prop['business_name']:
        content.append(f"- **Business Name**: {prop['business_name']}")
    content.append(f"- **Required**: {'Yes' if prop['required'] else 'No'}")
    content.append("")
    
    # Validation
    if prop['validation']:
        content.append("## Validation Rules")
        for key, value in prop['validation'].items():
            content.append(f"- **{key}**: {value}")
        content.append("")
    
    # Examples
    if prop['examples']:
        content.append("## Examples")
        for example in prop['examples']:
            content.append(f"- `{example}`")
        content.append("")
    
    # Tags
    content.append("## Tags")
    content.append(f"#property #{prop['namespace']} #{prop['type']}")
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(content))


def _create_relationship_note(rel: Dict, rels_path: Path):
    """Create an Obsidian note for a relationship."""
    file_path = rels_path / f"{rel['name']}.md"
    
    content = []
    
    # YAML frontmatter
    content.append("---")
    content.append(f"type: relationship")
    content.append(f"namespace: {rel['namespace']}")
    content.append(f"from: {rel['from']}")
    content.append(f"to: {rel['to']}")
    content.append("---")
    content.append("")
    
    # Title and description
    content.append(f"# {rel['name']}")
    content.append("")
    content.append(rel['description'])
    content.append("")
    
    # Relationship details
    content.append("## Connection")
    content.append(f"[[{rel['from']}]] → [[{rel['to']}]]")
    content.append("")
    content.append(f"- **Type**: {rel['type']}")
    if rel['inverse']:
        content.append(f"- **Inverse**: {rel['inverse']}")
    content.append("")
    
    # SQL hint
    if rel['sql_hint']:
        content.append("## SQL Hint")
        content.append("```sql")
        content.append(rel['sql_hint'])
        content.append("```")
        content.append("")
    
    # Tags
    content.append("## Tags")
    content.append(f"#relationship #{rel['namespace']}")
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(content))


def _create_business_rule_note(rule: Dict, rules_path: Path):
    """Create an Obsidian note for a business rule."""
    file_path = rules_path / f"{rule['name']}.md"
    
    content = []
    
    # YAML frontmatter
    content.append("---")
    content.append(f"type: business_rule")
    content.append(f"namespace: {rule['namespace']}")
    content.append("---")
    content.append("")
    
    # Title and description
    content.append(f"# {rule['name']}")
    content.append("")
    content.append(rule['description'])
    content.append("")
    
    # Rule conditions
    if rule['when']:
        content.append("## When")
        for key, value in rule['when'].items():
            content.append(f"- **{key}**: {value}")
        content.append("")
    
    # Implications
    if rule['implies']:
        content.append("## Implies")
        content.append(rule['implies'])
        content.append("")
    
    # SQL hint
    if rule['sql_hint']:
        content.append("## SQL Implementation")
        content.append("```sql")
        content.append(rule['sql_hint'])
        content.append("```")
        content.append("")
    
    # Tags
    content.append("## Tags")
    content.append(f"#business_rule #{rule['namespace']}")
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(content))


def _create_index_note(ontology_data: Dict, output_path: Path):
    """Create an index note for the Obsidian vault."""
    file_path = output_path / "README.md"
    
    content = []
    content.append("# Manufacturing Ontology Knowledge Graph")
    content.append("")
    content.append("This vault contains the structured representation of the Manufacturing Execution System (MES) and Virtual Twin ontologies.")
    content.append("")
    
    # Metadata
    content.append("## Ontology Metadata")
    content.append("")
    content.append("### MES Ontology")
    mes_meta = ontology_data['metadata']['mes']
    content.append(f"- **Name**: {mes_meta.get('name', 'N/A')}")
    content.append(f"- **Version**: {mes_meta.get('version', 'N/A')}")
    content.append(f"- **Description**: {mes_meta.get('description', 'N/A')}")
    content.append("")
    
    content.append("### Twin Ontology")
    twin_meta = ontology_data['metadata']['twin']
    content.append(f"- **Name**: {twin_meta.get('name', 'N/A')}")
    content.append(f"- **Version**: {twin_meta.get('version', 'N/A')}")
    content.append(f"- **Description**: {twin_meta.get('description', 'N/A')}")
    content.append("")
    
    # Statistics
    content.append("## Statistics")
    content.append(f"- **Total Classes**: {len(ontology_data['classes'])}")
    content.append(f"- **Total Properties**: {len(ontology_data['properties'])}")
    content.append(f"- **Total Relationships**: {len(ontology_data['relationships'])}")
    content.append(f"- **Total Business Rules**: {len(ontology_data['business_rules'])}")
    content.append(f"- **Cross-Ontology Mappings**: {len(ontology_data['cross_mappings'])}")
    content.append("")
    
    # Navigation
    content.append("## Navigation")
    content.append("")
    content.append("### By Namespace")
    content.append("- [[MES]] - Manufacturing Execution System ontology")
    content.append("- [[Twin]] - Virtual Twin ontology")
    content.append("")
    
    content.append("### By Component Type")
    content.append("- [[Properties]] - Data properties and attributes")
    content.append("- [[Relationships]] - Connections between entities")
    content.append("- [[BusinessRules]] - Business logic and constraints")
    content.append("")
    
    content.append("## Graph View")
    content.append("Use Obsidian's Graph View to explore the connections between concepts.")
    content.append("")
    
    content.append("## Tags")
    content.append("#ontology #knowledge_graph #manufacturing #mes #virtual_twin")
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(content))


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
    
    if 'description' in data:
        lines.append(f"<br>{data['description']}")
    
    return '<br>'.join(lines)