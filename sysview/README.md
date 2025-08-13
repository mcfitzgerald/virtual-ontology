# Ontology Knowledge Graph Visualization

An interactive visualization system for exploring Manufacturing Execution System (MES) and Virtual Twin ontologies using Dash and Cytoscape.

## Features

- **Interactive Network Graph**: Explore ontology classes, properties, relationships, and business rules
- **Multiple Layouts**: Hierarchical, force-directed, circular, and more
- **Filtering**: Filter by namespace (MES/Twin), node types, and search terms
- **Detail Panel**: Click nodes to see detailed information
- **Export Options**: 
  - PyVis HTML for standalone interactive graphs
  - Obsidian-compatible markdown vault
  - Image export

## Installation

1. Install dependencies:
```bash
cd sysview
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python app.py
```

Then open your browser to `http://localhost:8050`

## Interface Guide

### Left Panel - Controls
- **Layout**: Choose graph layout algorithm
- **Namespace**: Filter by MES, Twin, or show all
- **Node Types**: Toggle visibility of different node types
- **Search**: Find nodes by name or description
- **Display Options**: Toggle labels, edges, and animations

### Center - Graph View
- **Click** nodes to select and view details
- **Scroll** to zoom
- **Drag** to pan
- Selected nodes and their connections are highlighted

### Right Panel - Details
Shows detailed information about the selected node including:
- Description
- Properties and validation rules
- SQL hints
- Business rules
- Cross-ontology mappings

## Node Types

- **Classes** (rectangles): Core ontology concepts
  - Blue: MES namespace
  - Green: Twin namespace
- **Properties** (circles): Data attributes
- **Relationships** (diamonds): Connections between classes
- **Business Rules** (hexagons): Constraints and logic

## Edge Types

- **Solid lines**: Class inheritance
- **Dashed lines**: Relationships
- **Dotted lines**: Properties or cross-mappings

## Export Formats

### PyVis HTML
Creates a standalone HTML file with an interactive graph that can be shared and viewed in any browser.

### Obsidian Vault
Generates a folder structure with markdown files for use in Obsidian:
- Each class, property, relationship, and rule becomes a note
- Wiki-links connect related concepts
- YAML frontmatter preserves metadata
- Use Obsidian's graph view to explore connections

## Architecture

```
sysview/
├── app.py                      # Main Dash application
├── src/
│   ├── ontology_parser.py      # YAML parsing
│   ├── graph_builder.py        # NetworkX graph construction
│   ├── cytoscape_styles.py     # Visual styling
│   ├── export_utils.py         # Export functionality
│   └── components/
│       ├── detail_panel.py     # Node details display
│       └── control_panel.py    # Filter controls
└── requirements.txt
```

## Ontology Overview

### MES Ontology
- Equipment hierarchy (Filler, Packer, Palletizer)
- Production orders and products
- Events and downtime tracking
- KPIs (OEE, Availability, Performance, Quality)

### Twin Ontology
- Virtual sensors for metrics observation
- Simulation runs and parameters
- Actionable parameters for optimization
- Cross-system synchronization

## Customization

To modify the visual appearance, edit `src/cytoscape_styles.py`:
- Node colors and shapes
- Edge styles
- Layout parameters

To add new ontologies, update paths in `app.py`:
```python
parser = OntologyParser(
    mes_path='path/to/your/ontology.yaml',
    twin_path='path/to/another/ontology.yaml'
)
```