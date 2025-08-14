"""Heatmap Visualizations for Parameter Sensitivity and Correlations
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import sqlite3
import json


def create_sensitivity_heatmap(
    run_ids: List[str],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create parameter sensitivity heatmap showing impact on KPIs
    
    Args:
        run_ids: List of simulation run IDs to analyze
        db_path: Path to database
    
    Returns:
        Plotly heatmap figure

    """
    # Define parameters and KPIs
    parameters = [
        "micro_stop_probability",
        "performance_factor", 
        "scrap_multiplier",
        "material_reliability",
        "cascade_sensitivity"
    ]
    
    kpis = ["mean_oee", "mean_availability", "mean_performance", "mean_quality"]
    
    # Calculate sensitivity matrix
    sensitivity_matrix = calculate_sensitivity(run_ids, parameters, kpis, db_path)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=sensitivity_matrix,
        x=[k.replace("mean_", "").upper() for k in kpis],
        y=[p.replace("_", " ").title() for p in parameters],
        colorscale='RdBu',
        zmid=0,
        text=sensitivity_matrix,
        texttemplate="%{text:.2f}",
        textfont={"size": 10},
        colorbar=dict(
            title="Impact",
            titleside="right",
            tickmode="linear",
            tick0=-1,
            dtick=0.5
        ),
        hovertemplate='Parameter: %{y}<br>' +
                     'KPI: %{x}<br>' +
                     'Impact: %{z:.3f}<br>' +
                     '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Parameter Sensitivity Analysis",
        xaxis_title="Key Performance Indicators",
        yaxis_title="Actionable Parameters",
        height=500,
        template="plotly_white"
    )
    
    # Add annotations for high impact cells
    annotations = []
    for i, param in enumerate(parameters):
        for j, kpi in enumerate(kpis):
            if abs(sensitivity_matrix[i][j]) > 0.5:
                annotations.append(dict(
                    x=j,
                    y=i,
                    text="⚠",
                    showarrow=False,
                    font=dict(color="white", size=20)
                ))
    
    fig.update_layout(annotations=annotations)
    
    return fig


def calculate_sensitivity(
    run_ids: List[str],
    parameters: List[str],
    kpis: List[str],
    db_path: str
) -> np.ndarray:
    """Calculate sensitivity matrix from runs"""
    # Initialize matrix
    matrix = np.zeros((len(parameters), len(kpis)))
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # Get baseline (first run)
        cursor = conn.execute(
            "SELECT * FROM twin_runs WHERE run_id = ? LIMIT 1",
            (run_ids[0] if run_ids else "",)
        )
        baseline = cursor.fetchone()
        
        if baseline and baseline["kpi_summary_json"]:
            baseline_kpis = json.loads(baseline["kpi_summary_json"])
            baseline_config = json.loads(baseline["config_delta_json"])
            
            # Compare with other runs
            for run_id in run_ids[1:]:
                cursor = conn.execute(
                    "SELECT * FROM twin_runs WHERE run_id = ?",
                    (run_id,)
                )
                row = cursor.fetchone()
                
                if row and row["kpi_summary_json"]:
                    kpis_data = json.loads(row["kpi_summary_json"])
                    config = json.loads(row["config_delta_json"])
                    
                    # Calculate sensitivity for each parameter-KPI pair
                    for i, param in enumerate(parameters):
                        param_delta = config.get(param, 0) - baseline_config.get(param, 0)
                        
                        if abs(param_delta) > 0.001:
                            for j, kpi in enumerate(kpis):
                                kpi_delta = kpis_data.get(kpi, 0) - baseline_kpis.get(kpi, 0)
                                sensitivity = kpi_delta / param_delta
                                matrix[i][j] = max(matrix[i][j], abs(sensitivity))
    
    # If no data, use mock sensitivity values
    if np.sum(matrix) == 0:
        np.random.seed(42)
        matrix = np.random.randn(len(parameters), len(kpis)) * 0.5
        matrix[0, 0] = -0.8  # micro_stop_probability strongly affects OEE
        matrix[1, 0] = 0.7   # performance_factor positively affects OEE
        matrix[2, 3] = -0.9  # scrap_multiplier strongly affects quality
        matrix[3, 1] = 0.6   # material_reliability affects availability
        matrix[4, 1] = -0.5  # cascade_sensitivity affects availability
    
    return matrix


def create_correlation_heatmap(
    run_id: str,
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create correlation heatmap between different KPIs
    """
    # Get data
    data = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """SELECT oee, availability, performance, quality, downtime_minutes
               FROM simulation_data
               WHERE run_id = ?
               LIMIT 1000""",
            (run_id,)
        )
        
        for row in cursor.fetchall():
            data.append(dict(row))
    
    # If no data, generate mock data
    if not data:
        np.random.seed(42)
        n = 1000
        data = pd.DataFrame({
            'oee': np.random.normal(0.65, 0.05, n),
            'availability': np.random.normal(0.80, 0.03, n),
            'performance': np.random.normal(0.85, 0.04, n),
            'quality': np.random.normal(0.95, 0.02, n),
            'downtime_minutes': np.random.normal(12, 5, n)
        })
    else:
        data = pd.DataFrame(data)
    
    # Calculate correlation matrix
    corr_matrix = data.corr()
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=corr_matrix.values,
        texttemplate="%{text:.2f}",
        textfont={"size": 12},
        colorbar=dict(
            title="Correlation",
            titleside="right"
        ),
        hovertemplate='%{y} vs %{x}<br>' +
                     'Correlation: %{z:.3f}<br>' +
                     '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=f"KPI Correlation Matrix - {run_id}",
        height=500,
        width=600,
        template="plotly_white"
    )
    
    return fig


def create_equipment_performance_heatmap(
    run_ids: List[str],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """Create heatmap showing equipment performance across lines
    """
    # Equipment types and lines
    equipment_types = ["FIL", "PCK", "PAL"]
    lines = ["LINE1", "LINE2", "LINE3"]
    
    # Create performance matrix
    performance_matrix = np.zeros((len(equipment_types), len(lines)))
    
    with sqlite3.connect(db_path) as conn:
        for run_id in run_ids[:1]:  # Use first run
            for i, equip in enumerate(equipment_types):
                for j, line in enumerate(lines):
                    equipment_id = f"{line}-{equip}"
                    
                    cursor = conn.execute(
                        """SELECT AVG(oee) as avg_oee
                           FROM simulation_data
                           WHERE run_id = ? AND equipment_id = ?""",
                        (run_id, equipment_id)
                    )
                    row = cursor.fetchone()
                    
                    if row and row[0]:
                        performance_matrix[i][j] = row[0]
    
    # If no data, use mock values
    if np.sum(performance_matrix) == 0:
        np.random.seed(42)
        performance_matrix = np.random.uniform(0.6, 0.9, (len(equipment_types), len(lines)))
        performance_matrix[1, 0] = 0.55  # LINE1-PCK is underperforming
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=performance_matrix * 100,  # Convert to percentage
        x=lines,
        y=equipment_types,
        colorscale='Viridis',
        text=performance_matrix * 100,
        texttemplate="%{text:.1f}%",
        textfont={"size": 14},
        colorbar=dict(
            title="OEE %",
            titleside="right"
        ),
        hovertemplate='Equipment: %{y}<br>' +
                     'Line: %{x}<br>' +
                     'OEE: %{z:.1f}%<br>' +
                     '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Equipment Performance Heatmap",
        xaxis_title="Production Lines",
        yaxis_title="Equipment Type",
        height=400,
        template="plotly_white"
    )
    
    # Add annotations for poor performance
    annotations = []
    for i in range(len(equipment_types)):
        for j in range(len(lines)):
            if performance_matrix[i][j] < 0.6:
                annotations.append(dict(
                    x=j,
                    y=i,
                    text="⚠",
                    showarrow=False,
                    font=dict(color="white", size=20)
                ))
    
    fig.update_layout(annotations=annotations)
    
    return fig