"""
Control Panel Component
Provides interactive controls for filtering and layout.
"""

from dash import html, dcc
from src.cytoscape_styles import get_layout_options


def create_control_panel(node_types, namespaces):
    """Create the control panel component."""
    return html.Div(
        id='control-panel',
        className='control-panel',
        children=[
            html.H3('Controls'),
            
            # Layout selector
            html.Div([
                html.Label('Layout'),
                dcc.Dropdown(
                    id='layout-dropdown',
                    options=get_layout_options(),
                    value='breadthfirst',
                    clearable=False
                )
            ], className='control-group'),
            
            # Namespace filter
            html.Div([
                html.Label('Namespace'),
                dcc.Dropdown(
                    id='namespace-dropdown',
                    options=[{'label': 'All', 'value': 'all'}] + 
                            [{'label': ns.upper(), 'value': ns} for ns in namespaces],
                    value='all',
                    clearable=False
                )
            ], className='control-group'),
            
            # Node type filter
            html.Div([
                html.Label('Node Types'),
                dcc.Checklist(
                    id='node-type-checklist',
                    options=[{'label': nt.replace('_', ' ').title(), 'value': nt} 
                            for nt in node_types],
                    value=node_types,
                    labelStyle={'display': 'block'}
                )
            ], className='control-group'),
            
            # Search box
            html.Div([
                html.Label('Search'),
                dcc.Input(
                    id='search-input',
                    type='text',
                    placeholder='Search nodes...',
                    debounce=True
                )
            ], className='control-group'),
            
            # Display options
            html.Div([
                html.Label('Display Options'),
                dcc.Checklist(
                    id='display-options',
                    options=[
                        {'label': 'Show Labels', 'value': 'labels'},
                        {'label': 'Show Edges', 'value': 'edges'},
                        {'label': 'Animate Layout', 'value': 'animate'}
                    ],
                    value=['labels', 'edges'],
                    labelStyle={'display': 'block'}
                )
            ], className='control-group'),
            
            # Export buttons
            html.Div([
                html.H4('Export'),
                html.Button('Download Image', id='export-image-btn', className='export-btn'),
                html.Button('Export to PyVis', id='export-pyvis-btn', className='export-btn'),
                html.Button('Export to Obsidian', id='export-obsidian-btn', className='export-btn'),
                dcc.Download(id='download-output')
            ], className='export-group')
        ]
    )