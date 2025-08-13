"""
Cytoscape Styles Module
Defines visual styles for the network graph.
"""

def get_default_stylesheet():
    """Get the default stylesheet for the Cytoscape graph."""
    return [
        # Node styles by type
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '10px',
                'width': '40px',
                'height': '40px',
                'border-width': 2,
                'border-color': '#666',
                'text-wrap': 'wrap',
                'text-max-width': '80px'
            }
        },
        
        # Class nodes
        {
            'selector': '.class',
            'style': {
                'shape': 'roundrectangle',
                'width': '60px',
                'height': '40px',
                'font-weight': 'bold'
            }
        },
        {
            'selector': '.class.mes',
            'style': {
                'background-color': '#3498db',
                'color': '#fff'
            }
        },
        {
            'selector': '.class.twin',
            'style': {
                'background-color': '#2ecc71',
                'color': '#fff'
            }
        },
        
        # Property nodes
        {
            'selector': '.property',
            'style': {
                'shape': 'ellipse',
                'width': '30px',
                'height': '30px',
                'font-size': '8px'
            }
        },
        {
            'selector': '.property.mes',
            'style': {
                'background-color': '#85C1E9',
                'border-color': '#3498db'
            }
        },
        {
            'selector': '.property.twin',
            'style': {
                'background-color': '#82E0AA',
                'border-color': '#2ecc71'
            }
        },
        
        # Relationship nodes
        {
            'selector': '.relationship',
            'style': {
                'shape': 'diamond',
                'width': '35px',
                'height': '35px',
                'background-color': '#9b59b6',
                'color': '#fff',
                'font-size': '9px'
            }
        },
        
        # Business rule nodes
        {
            'selector': '.business_rule',
            'style': {
                'shape': 'hexagon',
                'width': '45px',
                'height': '45px',
                'background-color': '#e74c3c',
                'color': '#fff',
                'font-size': '9px'
            }
        },
        
        # Edge styles
        {
            'selector': 'edge',
            'style': {
                'width': 2,
                'line-color': '#95a5a6',
                'target-arrow-color': '#95a5a6',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'font-size': '8px',
                'text-rotation': 'autorotate',
                'text-margin-y': -10
            }
        },
        
        # Inheritance edges
        {
            'selector': '.inheritance',
            'style': {
                'line-style': 'solid',
                'line-color': '#34495e',
                'target-arrow-color': '#34495e',
                'width': 3,
                'target-arrow-shape': 'triangle-tee'
            }
        },
        
        # Property edges
        {
            'selector': '.has_property',
            'style': {
                'line-style': 'dotted',
                'line-color': '#7f8c8d',
                'target-arrow-color': '#7f8c8d',
                'width': 1
            }
        },
        
        # Relationship edges
        {
            'selector': '.relationship',
            'style': {
                'line-style': 'dashed',
                'line-color': '#9b59b6',
                'target-arrow-color': '#9b59b6',
                'label': 'data(relationship)'
            }
        },
        
        # Cross-mapping edges
        {
            'selector': '.cross_mapping',
            'style': {
                'line-style': 'dotted',
                'line-color': '#f39c12',
                'target-arrow-color': '#f39c12',
                'width': 2,
                'target-arrow-shape': 'vee'
            }
        },
        
        # Business rule edges
        {
            'selector': '.has_rule',
            'style': {
                'line-style': 'dashed',
                'line-color': '#e74c3c',
                'target-arrow-color': '#e74c3c',
                'width': 1
            }
        },
        
        # Selected nodes
        {
            'selector': ':selected',
            'style': {
                'border-width': 4,
                'border-color': '#f39c12',
                'background-blacken': -0.1
            }
        },
        
        # Highlighted nodes
        {
            'selector': '.highlighted',
            'style': {
                'border-width': 3,
                'border-color': '#e67e22',
                'background-blacken': -0.2,
                'z-index': 999
            }
        },
        
        # Faded nodes (for focus mode)
        {
            'selector': '.faded',
            'style': {
                'opacity': 0.25
            }
        }
    ]


def get_layout_options():
    """Get available layout options for the graph."""
    return [
        {'label': 'Hierarchical', 'value': 'breadthfirst'},
        {'label': 'Force-Directed', 'value': 'cose'},
        {'label': 'Circle', 'value': 'circle'},
        {'label': 'Grid', 'value': 'grid'},
        {'label': 'Concentric', 'value': 'concentric'},
        {'label': 'Random', 'value': 'random'}
    ]


def get_hierarchical_layout():
    """Get hierarchical layout configuration."""
    return {
        'name': 'breadthfirst',
        'directed': True,
        'spacingFactor': 1.5,
        'avoidOverlap': True,
        'nodeDimensionsIncludeLabels': True
    }


def get_force_directed_layout():
    """Get force-directed layout configuration."""
    return {
        'name': 'cose',
        'animate': True,
        'animationDuration': 1000,
        'nodeRepulsion': 8000,
        'idealEdgeLength': 50,
        'edgeElasticity': 100,
        'nestingFactor': 5,
        'gravity': 80,
        'numIter': 1000,
        'initialTemp': 200,
        'coolingFactor': 0.95,
        'minTemp': 1.0
    }


def get_circular_layout():
    """Get circular layout configuration."""
    return {
        'name': 'circle',
        'avoidOverlap': True,
        'nodeDimensionsIncludeLabels': True,
        'spacingFactor': 1.5,
        'startAngle': 0,
        'sweep': 2 * 3.14159
    }


def get_concentric_layout():
    """Get concentric layout configuration."""
    return {
        'name': 'concentric',
        'minNodeSpacing': 50
        # levelWidth removed - not a valid parameter for concentric layout
    }