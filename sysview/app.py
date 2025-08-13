"""
Ontology Knowledge Graph Visualization Dashboard
Main Dash application for interactive ontology exploration.
"""

import dash
from dash import html, dcc, Input, Output, State, ALL
import dash_cytoscape as cyto
from pathlib import Path
import json
import base64

# Load extra layouts for Cytoscape - enables image export
cyto.load_extra_layouts()

# Import custom modules
from src.ontology_parser import OntologyParser
from src.graph_builder import GraphBuilder
from src.cytoscape_styles import (
    get_default_stylesheet, 
    get_hierarchical_layout,
    get_force_directed_layout,
    get_circular_layout,
    get_concentric_layout
)
from src.components.detail_panel import create_detail_panel
from src.components.control_panel import create_control_panel

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Ontology Knowledge Graph Viewer"

# Parse ontologies and build graph
print("Loading ontologies...")
parser = OntologyParser(
    mes_path='../ontology/ontology_spec.yaml',
    twin_path='../ontology/twin_ontology_spec.yaml'
)
ontology_data = parser.parse_all()

print("Building graph...")
builder = GraphBuilder(ontology_data)
graph = builder.build_graph()
elements = builder.get_cytoscape_elements()
node_types = builder.get_node_types()
namespaces = builder.get_namespaces()

print(f"Graph built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")

# Define the app layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Manufacturing Ontology Knowledge Graph"),
        html.P("Interactive visualization of MES and Virtual Twin ontologies")
    ], className='header'),
    
    # Main container
    html.Div([
        # Left panel - Controls
        html.Div([
            create_control_panel(node_types, namespaces)
        ], className='left-panel'),
        
        # Center - Graph
        html.Div([
            cyto.Cytoscape(
                id='cytoscape-graph',
                elements=elements,
                stylesheet=get_default_stylesheet(),
                layout=get_hierarchical_layout(),
                style={'width': '100%', 'height': '100%'},
                minZoom=0.1,
                maxZoom=3
            )
        ], className='graph-container'),
        
        # Right panel - Details
        html.Div([
            create_detail_panel()
        ], className='right-panel', id='right-panel-container')
    ], className='main-container'),
    
    # Hidden stores for data
    dcc.Store(id='filtered-elements', data=elements),
    dcc.Store(id='selected-node-data')
])

# Callback for filtering elements
@app.callback(
    Output('filtered-elements', 'data'),
    [Input('namespace-dropdown', 'value'),
     Input('node-type-checklist', 'value'),
     Input('search-input', 'value')]
)
def filter_elements(namespace, node_types_selected, search_term):
    """Filter graph elements based on user selections."""
    filtered = []
    visible_nodes = set()
    
    # Filter nodes
    for element in elements:
        if 'source' not in element['data']:  # It's a node
            node_data = element['data']
            
            # Check namespace filter
            if namespace != 'all' and node_data.get('namespace') != namespace:
                continue
            
            # Check node type filter
            if node_data.get('node_type') not in node_types_selected:
                continue
            
            # Check search term
            if search_term:
                search_lower = search_term.lower()
                if not any(search_lower in str(v).lower() 
                          for v in [node_data.get('label', ''), 
                                   node_data.get('description', '')]):
                    continue
            
            filtered.append(element)
            visible_nodes.add(node_data['id'])
    
    # Add edges between visible nodes
    for element in elements:
        if 'source' in element['data']:  # It's an edge
            if (element['data']['source'] in visible_nodes and 
                element['data']['target'] in visible_nodes):
                filtered.append(element)
    
    return filtered

# Callback for updating graph elements and layout
@app.callback(
    Output('cytoscape-graph', 'elements'),
    Output('cytoscape-graph', 'layout'),
    [Input('filtered-elements', 'data'),
     Input('layout-dropdown', 'value'),
     Input('display-options', 'value')]
)
def update_graph(filtered_elements, layout_name, display_options):
    """Update graph elements and layout."""
    # Handle None or empty elements
    if not filtered_elements:
        filtered_elements = []
    
    # Handle None display_options
    if display_options is None:
        display_options = ['labels', 'edges']
    
    # Apply display options
    elements_to_show = filtered_elements.copy()
    
    if 'edges' not in display_options:
        # Remove edges
        elements_to_show = [e for e in elements_to_show if 'source' not in e['data']]
    
    # Get layout configuration
    layout_config = {
        'breadthfirst': get_hierarchical_layout(),
        'cose': get_force_directed_layout(),
        'circle': get_circular_layout(),
        'concentric': get_concentric_layout(),
        'grid': {'name': 'grid'},
        'random': {'name': 'random'}
    }.get(layout_name, get_hierarchical_layout())
    
    # Add animation if selected
    if 'animate' in display_options:
        layout_config['animate'] = True
        layout_config['animationDuration'] = 500
    
    return elements_to_show, layout_config

# Callback for node selection
@app.callback(
    Output('selected-node-data', 'data'),
    Input('cytoscape-graph', 'tapNodeData')
)
def select_node(node_data):
    """Store selected node data."""
    return node_data

# Callback for updating detail panel
@app.callback(
    Output('right-panel-container', 'children'),
    Input('selected-node-data', 'data')
)
def update_detail_panel(node_data):
    """Update the detail panel with selected node information."""
    return create_detail_panel(node_data)

# Callback for highlighting connected nodes
@app.callback(
    Output('cytoscape-graph', 'stylesheet'),
    [Input('selected-node-data', 'data'),
     Input('display-options', 'value')],
    State('cytoscape-graph', 'elements')
)
def highlight_connected(selected_node, display_options, current_elements):
    """Highlight selected node and its connections."""
    stylesheet = get_default_stylesheet()
    
    # Handle None display_options
    if display_options is None:
        display_options = ['labels', 'edges']
    
    # Handle None current_elements
    if not current_elements:
        current_elements = []
    
    if selected_node:
        node_id = selected_node['id']
        
        # Find connected nodes
        connected = {node_id}
        for element in current_elements:
            if 'source' in element['data']:
                if element['data']['source'] == node_id:
                    connected.add(element['data']['target'])
                elif element['data']['target'] == node_id:
                    connected.add(element['data']['source'])
        
        # Add highlighting styles
        for node in connected:
            stylesheet.append({
                'selector': f'node[id = "{node}"]',
                'style': {
                    'border-width': 4,
                    'border-color': '#f39c12',
                    'z-index': 999
                }
            })
        
        # Fade non-connected nodes
        stylesheet.append({
            'selector': 'node',
            'style': {
                'opacity': 0.3
            }
        })
        
        for node in connected:
            stylesheet.append({
                'selector': f'node[id = "{node}"]',
                'style': {
                    'opacity': 1
                }
            })
    
    # Handle label visibility
    if 'labels' not in display_options:
        stylesheet.append({
            'selector': 'node',
            'style': {
                'label': ''
            }
        })
    
    return stylesheet

# Callback for image export  
@app.callback(
    [Output('cytoscape-graph', 'generateImage'),
     Output('download-output', 'data')],
    [Input('export-image-btn', 'n_clicks'),
     Input('export-pyvis-btn', 'n_clicks'),
     Input('export-obsidian-btn', 'n_clicks')],
    [State('cytoscape-graph', 'elements')],
    prevent_initial_call=True
)
def handle_export(image_clicks, pyvis_clicks, obsidian_clicks, elements):
    """Handle export button clicks."""
    from dash import ctx
    
    if not ctx.triggered:
        return {}, None
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'export-image-btn':
        # Trigger image generation from Cytoscape
        # This will generate a PNG image
        return {
            'type': 'png',
            'action': 'download',
            'filename': 'ontology_graph.png',
            'options': {
                'output': 'blob',
                'bg': 'white',
                'width': 1920,
                'height': 1080,
                'maxWidth': 5000,
                'maxHeight': 5000
            }
        }, None
    
    elif button_id == 'export-pyvis-btn':
        # Export to PyVis HTML
        from src.export_utils import export_to_pyvis
        html_content = export_to_pyvis(elements)
        return {}, dict(content=html_content, filename="ontology_graph.html")
    
    elif button_id == 'export-obsidian-btn':
        # Export to Obsidian vault
        from src.export_utils import export_to_obsidian
        zip_content = export_to_obsidian(elements, ontology_data)
        return {}, dict(content=zip_content, filename="obsidian_vault.zip", type="application/zip")
    
    return {}, None

# Add CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .header h1 {
                margin: 0 0 10px 0;
                font-size: 28px;
            }
            .header p {
                margin: 0;
                opacity: 0.9;
            }
            .main-container {
                display: flex;
                height: calc(100vh - 100px);
            }
            .left-panel, .right-panel {
                width: 300px;
                background: white;
                padding: 20px;
                overflow-y: auto;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .graph-container {
                flex: 1;
                position: relative;
                background: white;
                margin: 0 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .control-group {
                margin-bottom: 20px;
            }
            .control-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #333;
            }
            .export-group {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
            }
            .export-btn {
                display: block;
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: background 0.3s;
            }
            .export-btn:hover {
                background: #5a67d8;
            }
            .detail-panel h3 {
                color: #667eea;
                margin-top: 0;
            }
            .detail-panel h4 {
                color: #333;
                margin-top: 20px;
                margin-bottom: 10px;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .code-block {
                background: #f8f8f8;
                padding: 10px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
                overflow-x: auto;
            }
            .placeholder-text {
                color: #999;
                font-style: italic;
            }
            .node-type, .namespace {
                color: #666;
                font-size: 14px;
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)