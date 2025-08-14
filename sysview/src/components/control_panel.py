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
            
            # Legend
            html.Div([
                html.H4('Legend'),
                html.Div([
                    # Namespace colors
                    html.Div([
                        html.Span('■', style={'color': '#B3E5FC', 'fontSize': '20px', 'fontWeight': 'bold'}),
                        html.Span(' MES Ontology (Blue)', style={'marginLeft': '8px', 'fontSize': '12px'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span('■', style={'color': '#C8E6C9', 'fontSize': '20px', 'fontWeight': 'bold'}),
                        html.Span(' Twin Ontology (Green)', style={'marginLeft': '8px', 'fontSize': '12px'})
                    ], style={'marginBottom': '10px'}),
                    
                    html.Hr(style={'margin': '10px 0', 'opacity': '0.3'}),
                    
                    # Node types
                    html.Div([
                        html.Div([
                            html.Span('▢', style={'fontSize': '16px', 'marginRight': '8px'}),
                            html.Span('Classes', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('●', style={'fontSize': '16px', 'marginRight': '8px'}),
                            html.Span('Properties', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('⬡', style={'fontSize': '16px', 'marginRight': '8px'}),
                            html.Span('Business Rules', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                    ]),
                    
                    html.Hr(style={'margin': '10px 0', 'opacity': '0.3'}),
                    
                    # Edge types legend
                    html.Div([
                        html.H5('Edge Types', style={'fontSize': '12px', 'fontWeight': 'bold', 'marginBottom': '5px'}),
                        html.Div([
                            html.Span('━━━', style={'fontSize': '14px', 'fontWeight': 'bold', 'marginRight': '8px'}),
                            html.Span('Inheritance (is-a)', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('┈┈┈', style={'fontSize': '14px', 'marginRight': '8px'}),
                            html.Span('Has Property', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('- - -', style={'fontSize': '14px', 'marginRight': '8px'}),
                            html.Span('Relationship', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('• • •', style={'fontSize': '14px', 'marginRight': '8px', 'color': '#f39c12'}),
                            html.Span('Cross-Ontology Mapping', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('- - -', style={'fontSize': '14px', 'marginRight': '8px', 'color': '#e74c3c'}),
                            html.Span('Has Business Rule', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                    ]),
                    
                    html.Hr(style={'margin': '10px 0', 'opacity': '0.3'}),
                    
                    # Arrow types legend
                    html.Div([
                        html.H5('Arrow Types', style={'fontSize': '12px', 'fontWeight': 'bold', 'marginBottom': '5px'}),
                        html.Div([
                            html.Span('▶', style={'fontSize': '12px', 'marginRight': '8px'}),
                            html.Span('Standard Arrow - Direction of relationship', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('▷⊤', style={'fontSize': '12px', 'marginRight': '8px'}),
                            html.Span('Triangle-Tee - Inheritance (child to parent)', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span('>', style={'fontSize': '12px', 'marginRight': '8px'}),
                            html.Span('Vee Arrow - Cross-ontology mapping', style={'fontSize': '11px'})
                        ], style={'marginBottom': '3px'}),
                    ])
                ], style={
                    'backgroundColor': '#f8f9fa',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'fontSize': '12px'
                })
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