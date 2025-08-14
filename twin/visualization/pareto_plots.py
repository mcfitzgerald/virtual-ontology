"""Pareto Front Visualization for Multi-objective Optimization
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import List, Dict, Any, Optional
import sqlite3
import json


def create_pareto_plot(
    run_ids: List[str],
    objectives: List[str] = ["oee", "energy"],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create interactive Pareto front visualization
    
    Args:
        run_ids: List of simulation run IDs to compare
        objectives: List of objectives to plot (default: OEE vs Energy)
        db_path: Path to database
    
    Returns:
        Plotly figure object

    """
    # Get data from database
    data_points = []
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        for run_id in run_ids:
            cursor = conn.execute(
                "SELECT * FROM twin_runs WHERE run_id = ?",
                (run_id,)
            )
            row = cursor.fetchone()
            
            if row and row["kpi_summary_json"]:
                kpis = json.loads(row["kpi_summary_json"])
                config = json.loads(row["config_delta_json"])
                
                # Extract objectives
                oee = kpis.get("mean_oee", 0)
                # Simulate energy based on performance factor
                energy = 100 - (config.get("performance_factor", 0.85) * 100)
                
                data_points.append({
                    "run_id": run_id,
                    "oee": oee * 100,  # Convert to percentage
                    "energy": energy,
                    "config": config,
                    "is_pareto": False  # Will be determined
                })
    
    # Identify Pareto front
    if data_points:
        data_points = identify_pareto_front(data_points)
    
    # Create plot
    fig = go.Figure()
    
    # Add non-Pareto points
    non_pareto = [p for p in data_points if not p["is_pareto"]]
    if non_pareto:
        fig.add_trace(go.Scatter(
            x=[p["oee"] for p in non_pareto],
            y=[p["energy"] for p in non_pareto],
            mode='markers',
            name='Dominated Solutions',
            marker=dict(
                size=10,
                color='lightblue',
                line=dict(width=1, color='darkblue')
            ),
            text=[f"Run: {p['run_id']}" for p in non_pareto],
            hovertemplate='<b>%{text}</b><br>' +
                         'OEE: %{x:.1f}%<br>' +
                         'Energy: %{y:.1f}%<br>' +
                         '<extra></extra>'
        ))
    
    # Add Pareto front points
    pareto = [p for p in data_points if p["is_pareto"]]
    if pareto:
        # Sort by first objective for line connection
        pareto.sort(key=lambda x: x["oee"])
        
        fig.add_trace(go.Scatter(
            x=[p["oee"] for p in pareto],
            y=[p["energy"] for p in pareto],
            mode='markers+lines',
            name='Pareto Front',
            marker=dict(
                size=15,
                color='red',
                symbol='star',
                line=dict(width=2, color='darkred')
            ),
            line=dict(color='red', width=2, dash='dash'),
            text=[f"Run: {p['run_id']}" for p in pareto],
            hovertemplate='<b>%{text}</b><br>' +
                         'OEE: %{x:.1f}%<br>' +
                         'Energy: %{y:.1f}%<br>' +
                         '<b>Pareto Optimal</b><br>' +
                         '<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title="Multi-objective Optimization: Pareto Front",
        xaxis_title="Overall Equipment Effectiveness (OEE) %",
        yaxis_title="Energy Consumption %",
        hovermode='closest',
        showlegend=True,
        height=600,
        template="plotly_white",
        annotations=[
            dict(
                text="Higher OEE →",
                xref="paper", yref="paper",
                x=0.95, y=0.05,
                showarrow=False,
                font=dict(size=12, color="gray")
            ),
            dict(
                text="← Lower Energy",
                xref="paper", yref="paper",
                x=0.05, y=0.95,
                showarrow=False,
                font=dict(size=12, color="gray")
            )
        ]
    )
    
    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig


def identify_pareto_front(points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify Pareto optimal points (non-dominated solutions)
    Assumes maximizing OEE and minimizing energy
    """
    for i, point_i in enumerate(points):
        is_dominated = False
        
        for j, point_j in enumerate(points):
            if i == j:
                continue
            
            # Check if point_j dominates point_i
            # For OEE: higher is better
            # For energy: lower is better
            if (point_j["oee"] >= point_i["oee"] and 
                point_j["energy"] <= point_i["energy"] and
                (point_j["oee"] > point_i["oee"] or 
                 point_j["energy"] < point_i["energy"])):
                is_dominated = True
                break
        
        point_i["is_pareto"] = not is_dominated
    
    return points


def create_pareto_3d(
    run_ids: List[str],
    objectives: List[str] = ["oee", "energy", "quality"],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create 3D Pareto front visualization for three objectives
    """
    # Get data
    data_points = []
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        for run_id in run_ids:
            cursor = conn.execute(
                "SELECT * FROM twin_runs WHERE run_id = ?",
                (run_id,)
            )
            row = cursor.fetchone()
            
            if row and row["kpi_summary_json"]:
                kpis = json.loads(row["kpi_summary_json"])
                config = json.loads(row["config_delta_json"])
                
                data_points.append({
                    "run_id": run_id,
                    "oee": kpis.get("mean_oee", 0) * 100,
                    "energy": 100 - (config.get("performance_factor", 0.85) * 100),
                    "quality": kpis.get("mean_quality", 0) * 100,
                    "config": config
                })
    
    # Create 3D scatter plot
    fig = go.Figure(data=[go.Scatter3d(
        x=[p["oee"] for p in data_points],
        y=[p["energy"] for p in data_points],
        z=[p["quality"] for p in data_points],
        mode='markers',
        marker=dict(
            size=8,
            color=[p["oee"] for p in data_points],  # Color by OEE
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="OEE %")
        ),
        text=[f"Run: {p['run_id']}" for p in data_points],
        hovertemplate='<b>%{text}</b><br>' +
                     'OEE: %{x:.1f}%<br>' +
                     'Energy: %{y:.1f}%<br>' +
                     'Quality: %{z:.1f}%<br>' +
                     '<extra></extra>'
    )])
    
    # Update layout
    fig.update_layout(
        title="3D Pareto Front: OEE vs Energy vs Quality",
        scene=dict(
            xaxis_title="OEE %",
            yaxis_title="Energy %",
            zaxis_title="Quality %",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        height=700
    )
    
    return fig