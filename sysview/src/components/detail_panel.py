"""
Detail Panel Component
Displays detailed information about selected nodes.
"""

from dash import html, dcc
import json


def create_detail_panel(node_data=None):
    """Create the detail panel component."""
    if not node_data:
        return html.Div(
            id='detail-panel',
            className='detail-panel',
            children=[
                html.H3('Node Details'),
                html.P('Select a node to view details', className='placeholder-text')
            ]
        )
    
    # Parse node data
    details = []
    
    # Basic information
    details.append(html.H3(node_data.get('label', 'Unknown')))
    details.append(html.P(f"Type: {node_data.get('node_type', 'Unknown')}", className='node-type'))
    details.append(html.P(f"Namespace: {node_data.get('namespace', 'Unknown')}", className='namespace'))
    
    # Description
    if 'description' in node_data:
        details.append(html.Div([
            html.H4('Description'),
            html.P(node_data['description'])
        ]))
    
    # Node-type specific details
    node_type = node_data.get('node_type', '')
    
    if node_type == 'class':
        details.extend(_get_class_details(node_data))
    elif node_type == 'property':
        details.extend(_get_property_details(node_data))
    elif node_type == 'relationship':
        details.extend(_get_relationship_details(node_data))
    elif node_type == 'business_rule':
        details.extend(_get_business_rule_details(node_data))
    
    # Graph metrics
    if any(k in node_data for k in ['degree', 'betweenness_centrality']):
        metrics = []
        if 'degree' in node_data:
            metrics.append(html.P(f"Connections: {node_data['degree']}"))
        if 'betweenness_centrality' in node_data:
            metrics.append(html.P(f"Centrality: {node_data['betweenness_centrality']:.3f}"))
        
        details.append(html.Div([
            html.H4('Graph Metrics'),
            html.Div(metrics)
        ]))
    
    return html.Div(
        id='detail-panel',
        className='detail-panel',
        children=details
    )


def _get_class_details(node_data):
    """Get details specific to class nodes."""
    details = []
    
    # Parent class
    if 'parent' in node_data and node_data['parent']:
        details.append(html.Div([
            html.H4('Parent Class'),
            html.P(node_data['parent'])
        ]))
    
    # Conditions
    if 'conditions' in node_data:
        try:
            conditions = json.loads(node_data['conditions'])
            if conditions:
                condition_items = []
                for cond in conditions:
                    condition_items.append(
                        html.Li(f"{cond.get('field', '')} {cond.get('operator', '')} {cond.get('value', '')}")
                    )
                details.append(html.Div([
                    html.H4('Conditions'),
                    html.Ul(condition_items)
                ]))
        except:
            pass
    
    # Mappings
    if 'maps_to' in node_data:
        try:
            maps_to = json.loads(node_data['maps_to'])
            if maps_to:
                mapping_items = []
                for system, concept in maps_to.items():
                    mapping_items.append(html.Li(f"{system}: {concept}"))
                details.append(html.Div([
                    html.H4('Maps To'),
                    html.Ul(mapping_items)
                ]))
        except:
            pass
    
    return details


def _get_property_details(node_data):
    """Get details specific to property nodes."""
    details = []
    
    # Data type
    if 'data_type' in node_data:
        details.append(html.P(f"Data Type: {node_data['data_type']}"))
    
    # SQL information
    sql_info = []
    if 'sql_column' in node_data and node_data['sql_column']:
        sql_info.append(html.P(f"Column: {node_data['sql_column']}"))
    if 'sql_table' in node_data and node_data['sql_table']:
        sql_info.append(html.P(f"Table: {node_data['sql_table']}"))
    
    if sql_info:
        details.append(html.Div([
            html.H4('SQL Information'),
            html.Div(sql_info)
        ]))
    
    # Unit and business name
    if 'unit' in node_data and node_data['unit']:
        details.append(html.P(f"Unit: {node_data['unit']}"))
    if 'business_name' in node_data and node_data['business_name']:
        details.append(html.P(f"Business Name: {node_data['business_name']}"))
    
    # Required flag
    if 'required' in node_data:
        details.append(html.P(f"Required: {'Yes' if node_data['required'] else 'No'}"))
    
    # Validation rules
    if 'validation' in node_data:
        try:
            validation = json.loads(node_data['validation'])
            if validation:
                val_items = []
                for key, value in validation.items():
                    val_items.append(html.Li(f"{key}: {value}"))
                details.append(html.Div([
                    html.H4('Validation'),
                    html.Ul(val_items)
                ]))
        except:
            pass
    
    # Examples
    if 'examples' in node_data:
        try:
            examples = json.loads(node_data['examples'])
            if examples:
                details.append(html.Div([
                    html.H4('Examples'),
                    html.P(', '.join(str(ex) for ex in examples))
                ]))
        except:
            pass
    
    return details


def _get_relationship_details(node_data):
    """Get details specific to relationship nodes."""
    details = []
    
    # From and To classes
    if 'from_class' in node_data:
        details.append(html.P(f"From: {node_data['from_class']}"))
    if 'to_class' in node_data:
        details.append(html.P(f"To: {node_data['to_class']}"))
    
    # Relationship type
    if 'rel_type' in node_data:
        details.append(html.P(f"Type: {node_data['rel_type']}"))
    
    # SQL hint
    if 'sql_hint' in node_data and node_data['sql_hint']:
        details.append(html.Div([
            html.H4('SQL Hint'),
            html.Pre(node_data['sql_hint'], className='code-block')
        ]))
    
    # Inverse relationship
    if 'inverse' in node_data and node_data['inverse']:
        details.append(html.P(f"Inverse: {node_data['inverse']}"))
    
    return details


def _get_business_rule_details(node_data):
    """Get details specific to business rule nodes."""
    details = []
    
    # When conditions
    if 'when' in node_data:
        try:
            when = json.loads(node_data['when'])
            if when:
                when_items = []
                for key, value in when.items():
                    when_items.append(html.Li(f"{key}: {value}"))
                details.append(html.Div([
                    html.H4('When'),
                    html.Ul(when_items)
                ]))
        except:
            pass
    
    # Implications
    if 'implies' in node_data and node_data['implies']:
        details.append(html.Div([
            html.H4('Implies'),
            html.P(node_data['implies'])
        ]))
    
    # SQL hint
    if 'sql_hint' in node_data and node_data['sql_hint']:
        details.append(html.Div([
            html.H4('SQL Hint'),
            html.Pre(node_data['sql_hint'], className='code-block')
        ]))
    
    return details