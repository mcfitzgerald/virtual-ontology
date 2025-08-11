#!/usr/bin/env python3
"""
Virtual Twin Network Visualization Test
Creates an interactive network graph of the manufacturing system
"""

import networkx as nx
from pyvis.network import Network
import sqlite3
import pandas as pd
import json
from pathlib import Path

def get_equipment_data(conn):
    """Query equipment and their performance metrics"""
    query = """
    SELECT DISTINCT 
        equipment_id,
        equipment_type,
        line_id,
        AVG(oee_score) as avg_oee,
        AVG(availability_score) as avg_availability,
        AVG(performance_score) as avg_performance,
        AVG(quality_score) as avg_quality,
        COUNT(CASE WHEN machine_status = 'Running' THEN 1 END) * 100.0 / COUNT(*) as uptime_pct
    FROM mes_data
    WHERE equipment_id IS NOT NULL
    GROUP BY equipment_id, equipment_type, line_id
    ORDER BY line_id, equipment_id
    """
    return pd.read_sql_query(query, conn)

def get_line_data(conn):
    """Query production lines"""
    query = """
    SELECT DISTINCT 
        line_id,
        COUNT(DISTINCT equipment_id) as equipment_count,
        AVG(oee_score) as avg_oee,
        AVG(good_units_produced) as avg_throughput
    FROM mes_data
    WHERE line_id IS NOT NULL
    GROUP BY line_id
    """
    return pd.read_sql_query(query, conn)

def get_relationships(equipment_df):
    """Infer upstream/downstream relationships based on equipment types"""
    relationships = []
    
    # Group by line
    for line_id in equipment_df['line_id'].unique():
        line_equipment = equipment_df[equipment_df['line_id'] == line_id].copy()
        
        # Sort by typical flow order: Filler -> Packer -> Palletizer
        type_order = {'Filler': 1, 'Packer': 2, 'Palletizer': 3}
        line_equipment['order'] = line_equipment['equipment_type'].map(type_order).fillna(4)
        line_equipment = line_equipment.sort_values('order')
        
        # Create edges based on flow
        equip_list = line_equipment['equipment_id'].tolist()
        for i in range(len(equip_list) - 1):
            relationships.append((equip_list[i], equip_list[i+1]))
    
    return relationships

def get_performance_color(oee_score):
    """Get color based on OEE performance"""
    if oee_score >= 85:
        return '#28a745'  # Green - World class
    elif oee_score >= 60:
        return '#ffc107'  # Yellow - Typical
    elif oee_score >= 40:
        return '#fd7e14'  # Orange - Low
    else:
        return '#dc3545'  # Red - Unacceptable

def build_network_graph(conn):
    """Build the network graph from database data"""
    # Get data
    equipment_df = get_equipment_data(conn)
    line_df = get_line_data(conn)
    relationships = get_relationships(equipment_df)
    
    # Create networkx graph
    G = nx.DiGraph()
    
    # Add line nodes (larger, at the top of hierarchy)
    for _, line in line_df.iterrows():
        node_id = f"LINE_{line['line_id']}"
        G.add_node(
            node_id,
            label=f"Line {line['line_id']}",
            title=f"Line {line['line_id']}<br>"
                  f"OEE: {line['avg_oee']:.1f}%<br>"
                  f"Equipment: {int(line['equipment_count'])}<br>"
                  f"Avg Throughput: {line['avg_throughput']:.0f} units/hr",
            color='#4169E1',  # Royal blue for lines
            size=40,
            level=0,  # Top level in hierarchy
            shape='box',
            font={'color': 'white', 'size': 14}
        )
    
    # Add equipment nodes
    equipment_colors = {
        'Filler': '#28a745',     # Green
        'Packer': '#fd7e14',     # Orange  
        'Palletizer': '#6f42c1'  # Purple
    }
    
    for _, equip in equipment_df.iterrows():
        node_id = equip['equipment_id']
        oee = equip['avg_oee'] if pd.notna(equip['avg_oee']) else 0
        
        # Base color on equipment type, adjust opacity by performance
        base_color = equipment_colors.get(equip['equipment_type'], '#6c757d')
        
        # Size based on OEE (better performance = larger node)
        node_size = 20 + (oee / 100) * 20
        
        G.add_node(
            node_id,
            label=f"{equip['equipment_id']}",
            title=f"<b>{equip['equipment_id']}</b><br>"
                  f"Type: {equip['equipment_type']}<br>"
                  f"Line: {equip['line_id']}<br>"
                  f"<br><b>Performance Metrics:</b><br>"
                  f"OEE: {oee:.1f}%<br>"
                  f"Availability: {equip['avg_availability']:.1f}%<br>"
                  f"Performance: {equip['avg_performance']:.1f}%<br>"
                  f"Quality: {equip['avg_quality']:.1f}%<br>"
                  f"Uptime: {equip['uptime_pct']:.1f}%",
            color=base_color,
            size=node_size,
            level=2,  # Equipment level
            borderWidth=3,
            borderWidthSelected=5,
            shape='dot'
        )
        
        # Add edge from line to equipment
        line_node = f"LINE_{equip['line_id']}"
        G.add_edge(line_node, node_id, color='#cccccc', width=1)
    
    # Add equipment-to-equipment relationships (material flow)
    for source, target in relationships:
        if source in G.nodes() and target in G.nodes():
            G.add_edge(
                source, target,
                color='#2196F3',
                width=3,
                arrows='to',
                smooth={'type': 'curvedCW', 'roundness': 0.2}
            )
    
    return G

def create_pyvis_network(G):
    """Convert networkx graph to pyvis network with custom settings"""
    net = Network(
        height="900px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#f8f9fa",
        font_color="#212529"
    )
    
    # Add graph data
    net.from_nx(G)
    
    # Configure physics for better layout
    net.set_options("""
    var options = {
        "nodes": {
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "font": {
                "size": 12,
                "strokeWidth": 2,
                "strokeColor": "#ffffff"
            }
        },
        "edges": {
            "smooth": {
                "type": "curvedCW",
                "roundness": 0.2
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.8
                }
            },
            "color": {
                "inherit": false
            },
            "font": {
                "size": 10
            }
        },
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "UD",
                "sortMethod": "directed",
                "levelSeparation": 200,
                "nodeSpacing": 150
            }
        },
        "physics": {
            "enabled": true,
            "hierarchicalRepulsion": {
                "centralGravity": 0.5,
                "springLength": 150,
                "springConstant": 0.01,
                "nodeDistance": 200
            },
            "solver": "hierarchicalRepulsion"
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "hideEdgesOnDrag": false,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """)
    
    return net

def add_simulation_data(G, conn):
    """Add simulation run data if available"""
    try:
        # Check if twin_runs table exists
        check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='twin_runs'"
        tables = pd.read_sql_query(check_query, conn)
        
        if 'twin_runs' not in tables['name'].values:
            print("No simulation data available (twin_runs table not found)")
            return
            
        query = """
        SELECT 
            run_id,
            run_type,
            started_at
        FROM twin_runs
        WHERE status = 'completed'
        ORDER BY started_at DESC
        LIMIT 1
        """
        result = pd.read_sql_query(query, conn)
        
        if not result.empty:
            latest_run = result.iloc[0]
            
            # Add simulation info node
            G.add_node(
                'SIMULATION_INFO',
                label='Latest Simulation',
                title=f"<b>Simulation Info</b><br>"
                      f"Run ID: {latest_run['run_id'][:8]}...<br>"
                      f"Type: {latest_run['run_type']}<br>"
                      f"Time: {latest_run['started_at']}<br>",
                color='#17a2b8',
                size=30,
                shape='database',
                level=-1
            )
    except Exception as e:
        print(f"Note: Could not load simulation data: {e}")

def main():
    """Main execution function"""
    db_path = Path("data/mes_database.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    print("Connecting to database...")
    conn = sqlite3.connect(db_path)
    
    try:
        print("Building network graph from manufacturing data...")
        G = build_network_graph(conn)
        
        print("Adding simulation data if available...")
        add_simulation_data(G, conn)
        
        print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        print("Creating interactive visualization...")
        net = create_pyvis_network(G)
        
        # Save the network
        output_file = "virtual_twin_network.html"
        net.save_graph(output_file)
        
        print(f"\n✅ Network visualization saved to: {output_file}")
        print(f"   Open this file in a web browser to view the interactive graph")
        print(f"\nGraph Statistics:")
        print(f"  - Production Lines: {len([n for n in G.nodes() if n.startswith('LINE_')])}")
        print(f"  - Equipment Nodes: {len([n for n in G.nodes() if not n.startswith('LINE_') and n != 'SIMULATION_INFO'])}")
        print(f"  - Material Flow Edges: {len([e for e in G.edges() if not e[0].startswith('LINE_')])}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()