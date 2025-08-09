"""
Time Series Visualization for KPI Trends
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sqlite3
import json


def plot_kpi_trends(
    run_ids: List[str],
    kpis: List[str] = ["oee", "availability", "performance", "quality"],
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """
    Create interactive time series plots for KPI trends
    
    Args:
        run_ids: List of simulation run IDs to plot
        kpis: List of KPIs to visualize
        db_path: Path to database
    
    Returns:
        Plotly figure with time series plots
    """
    
    # Create subplots for each KPI
    fig = make_subplots(
        rows=len(kpis),
        cols=1,
        subplot_titles=[kpi.upper() for kpi in kpis],
        shared_xaxes=True,
        vertical_spacing=0.05
    )
    
    colors = px.colors.qualitative.Plotly
    
    for run_idx, run_id in enumerate(run_ids):
        # Get time series data
        data = get_time_series_data(run_id, db_path)
        
        if not data:
            continue
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data)
        
        # Plot each KPI
        for kpi_idx, kpi in enumerate(kpis):
            if kpi in df.columns:
                # Add trace
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df[kpi] * 100 if kpi != "downtime_minutes" else df[kpi],
                        mode='lines',
                        name=f"{run_id} - {kpi.upper()}",
                        line=dict(color=colors[run_idx % len(colors)]),
                        legendgroup=run_id,
                        showlegend=(kpi_idx == 0),  # Only show in first subplot
                        hovertemplate='<b>%{text}</b><br>' +
                                     f'{kpi.upper()}: %{{y:.1f}}{"%" if kpi != "downtime_minutes" else " min"}<br>' +
                                     'Time: %{x}<br>' +
                                     '<extra></extra>',
                        text=[run_id] * len(df)
                    ),
                    row=kpi_idx + 1,
                    col=1
                )
                
                # Add confidence bands if available
                if f"{kpi}_std" in df.columns:
                    std = df[f"{kpi}_std"]
                    mean = df[kpi]
                    
                    # Upper bound
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=(mean + std) * 100 if kpi != "downtime_minutes" else mean + std,
                            mode='lines',
                            line=dict(width=0),
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        row=kpi_idx + 1,
                        col=1
                    )
                    
                    # Lower bound
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=(mean - std) * 100 if kpi != "downtime_minutes" else mean - std,
                            mode='lines',
                            line=dict(width=0),
                            fill='tonexty',
                            fillcolor=f'rgba({",".join(str(c) for c in px.colors.hex_to_rgb(colors[run_idx % len(colors)]))}, 0.2)',
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        row=kpi_idx + 1,
                        col=1
                    )
        
        # Update y-axis labels
        for kpi_idx, kpi in enumerate(kpis):
            y_title = f"{kpi.upper()} %" if kpi != "downtime_minutes" else "Downtime (min)"
            fig.update_yaxes(title_text=y_title, row=kpi_idx + 1, col=1)
    
    # Update layout
    fig.update_layout(
        title="KPI Trends Over Time",
        height=200 * len(kpis) + 100,
        showlegend=True,
        hovermode='x unified',
        template="plotly_white"
    )
    
    # Update x-axis
    fig.update_xaxes(
        title_text="Time",
        row=len(kpis),
        col=1,
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1h", step="hour", stepmode="backward"),
                dict(count=6, label="6h", step="hour", stepmode="backward"),
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(step="all", label="All")
            ])
        )
    )
    
    return fig


def get_time_series_data(
    run_id: str,
    db_path: str
) -> List[Dict[str, Any]]:
    """Get time series data for a run"""
    data = []
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # Check if data is in simulation_data table
        cursor = conn.execute(
            """SELECT * FROM simulation_data 
               WHERE run_id = ? 
               ORDER BY timestamp
               LIMIT 1000""",
            (run_id,)
        )
        
        for row in cursor.fetchall():
            data.append({
                "timestamp": row["timestamp"],
                "oee": row["oee"],
                "availability": row["availability"],
                "performance": row["performance"],
                "quality": row["quality"],
                "downtime_minutes": row["downtime_minutes"]
            })
    
    # If no data, generate mock data for demo
    if not data:
        start_time = datetime.now() - timedelta(days=7)
        for i in range(168):  # One week of hourly data
            timestamp = start_time + timedelta(hours=i)
            data.append({
                "timestamp": timestamp.isoformat(),
                "oee": 0.65 + np.random.normal(0, 0.05),
                "availability": 0.80 + np.random.normal(0, 0.03),
                "performance": 0.85 + np.random.normal(0, 0.04),
                "quality": 0.95 + np.random.normal(0, 0.02),
                "downtime_minutes": max(0, 60 - 60 * (0.80 + np.random.normal(0, 0.03)))
            })
    
    return data


def plot_kpi_comparison(
    run_ids: List[str],
    kpi: str = "oee",
    db_path: str = "data/mes_database.db"
) -> go.Figure:
    """
    Create comparison plot for a single KPI across multiple runs
    """
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for idx, run_id in enumerate(run_ids):
        data = get_time_series_data(run_id, db_path)
        
        if not data:
            continue
        
        df = pd.DataFrame(data)
        
        # Add trace
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[kpi] * 100,
            mode='lines+markers',
            name=run_id,
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=4),
            hovertemplate=f'<b>{run_id}</b><br>' +
                         f'{kpi.upper()}: %{{y:.1f}}%<br>' +
                         'Time: %{x}<br>' +
                         '<extra></extra>'
        ))
    
    # Add annotations for parameter changes
    annotations = []
    with sqlite3.connect(db_path) as conn:
        for run_id in run_ids:
            cursor = conn.execute(
                "SELECT * FROM parameter_history WHERE run_id = ? LIMIT 5",
                (run_id,)
            )
            for row in cursor.fetchall():
                if row:
                    annotations.append(dict(
                        x=row["changed_at"] if "changed_at" in row.keys() else datetime.now().isoformat(),
                        y=0,
                        xref="x",
                        yref="paper",
                        text=f"↑ {row['parameter_name']}",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="gray",
                        ax=0,
                        ay=-30
                    ))
    
    # Update layout
    fig.update_layout(
        title=f"{kpi.upper()} Comparison Across Runs",
        xaxis_title="Time",
        yaxis_title=f"{kpi.upper()} %",
        hovermode='x unified',
        height=500,
        template="plotly_white",
        annotations=annotations[:5]  # Limit annotations
    )
    
    # Add range slider
    fig.update_xaxes(rangeslider_visible=True)
    
    return fig