"""Financial Visualization for ROI and Cost Impact
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


def plot_roi_distribution(
    roi_summary: Dict[str, Any]
) -> go.Figure:
    """Create ROI distribution visualization with confidence intervals
    
    Args:
        roi_summary: ROI calculation results from CostImpactCalculator
    
    Returns:
        Plotly figure with ROI distributions

    """
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Weekly Savings Distribution",
            "Payback Period Analysis",
            "NPV Distribution",
            "Annual Benefit Confidence"
        ),
        specs=[
            [{"type": "histogram"}, {"type": "scatter"}],
            [{"type": "histogram"}, {"type": "bar"}]
        ]
    )
    
    # Generate sample distributions based on summary statistics
    np.random.seed(42)
    n_samples = 1000
    
    # 1. Weekly Savings Distribution
    weekly_savings = np.random.normal(
        roi_summary["weekly_savings"]["mean"],
        roi_summary["weekly_savings"]["std"],
        n_samples
    )
    
    fig.add_trace(
        go.Histogram(
            x=weekly_savings,
            nbinsx=30,
            name="Weekly Savings",
            marker_color='lightblue',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Add confidence interval lines
    ci_lower = roi_summary["weekly_savings"]["confidence_interval"][0]
    ci_upper = roi_summary["weekly_savings"]["confidence_interval"][1]
    
    fig.add_vline(
        x=roi_summary["weekly_savings"]["mean"],
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: ${roi_summary['weekly_savings']['mean']:,.0f}",
        row=1, col=1
    )
    
    fig.add_vrect(
        x0=ci_lower, x1=ci_upper,
        fillcolor="green", opacity=0.2,
        layer="below", line_width=0,
        row=1, col=1
    )
    
    # 2. Payback Period Scatter
    weeks = list(range(1, 53))
    cumulative_savings = [
        w * roi_summary["weekly_savings"]["mean"] - roi_summary["implementation_cost"]
        for w in weeks
    ]
    
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=cumulative_savings,
            mode='lines+markers',
            name="Cumulative Savings",
            line=dict(color='blue', width=2),
            marker=dict(size=4),
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Add break-even line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Break-even: {roi_summary['payback_weeks']['mean']:.1f} weeks",
        row=1, col=2
    )
    
    # Add implementation cost line
    fig.add_hline(
        y=-roi_summary["implementation_cost"],
        line_dash="dot",
        line_color="orange",
        annotation_text=f"Investment: ${roi_summary['implementation_cost']:,.0f}",
        row=1, col=2
    )
    
    # 3. NPV Distribution
    npv_samples = np.random.normal(
        roi_summary["npv"]["mean"],
        roi_summary["npv"]["std"],
        n_samples
    )
    
    fig.add_trace(
        go.Histogram(
            x=npv_samples,
            nbinsx=30,
            name="NPV",
            marker_color='lightgreen',
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.add_vline(
        x=roi_summary["npv"]["mean"],
        line_dash="dash",
        line_color="green",
        annotation_text=f"Mean NPV: ${roi_summary['npv']['mean']:,.0f}",
        row=2, col=1
    )
    
    fig.add_vline(
        x=0,
        line_dash="solid",
        line_color="red",
        annotation_text=f"P(NPV>0): {roi_summary['npv']['probability_positive']:.1%}",
        row=2, col=1
    )
    
    # 4. Annual Benefit Bar Chart
    annual_data = {
        'Category': ['Expected', 'Lower CI', 'Upper CI'],
        'Amount': [
            roi_summary["annual_benefit"]["mean"],
            roi_summary["annual_benefit"]["confidence_interval"][0],
            roi_summary["annual_benefit"]["confidence_interval"][1]
        ]
    }
    
    colors = ['green', 'orange', 'lightgreen']
    
    fig.add_trace(
        go.Bar(
            x=annual_data['Category'],
            y=annual_data['Amount'],
            marker_color=colors,
            text=[f"${v:,.0f}" for v in annual_data['Amount']],
            textposition='outside',
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Weekly Savings ($)", row=1, col=1)
    fig.update_xaxes(title_text="Weeks", row=1, col=2)
    fig.update_xaxes(title_text="Net Present Value ($)", row=2, col=1)
    fig.update_xaxes(title_text="Scenario", row=2, col=2)
    
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative Value ($)", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(title_text="Annual Benefit ($)", row=2, col=2)
    
    # Update layout
    fig.update_layout(
        title="ROI Analysis with Monte Carlo Confidence Intervals",
        height=800,
        showlegend=False,
        template="plotly_white"
    )
    
    return fig


def plot_sensitivity_tornado(
    parameter_impacts: Dict[str, float],
    baseline_value: float = 100000
) -> go.Figure:
    """Create tornado chart for parameter sensitivity on financial impact
    """
    # Sort parameters by absolute impact
    sorted_params = sorted(
        parameter_impacts.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
    # Prepare data
    parameters = [p[0].replace("_", " ").title() for p in sorted_params]
    low_impact = [baseline_value - abs(p[1]) for p in sorted_params]
    high_impact = [baseline_value + abs(p[1]) for p in sorted_params]
    
    # Create figure
    fig = go.Figure()
    
    # Add bars for low scenario
    fig.add_trace(go.Bar(
        name='Downside',
        y=parameters,
        x=[baseline_value - l for l in low_impact],
        orientation='h',
        marker=dict(color='lightcoral'),
        base=low_impact,
        text=[f"-${abs(baseline_value - l):,.0f}" for l in low_impact],
        textposition='inside',
        hovertemplate='Parameter: %{y}<br>' +
                     'Downside: -$%{text}<br>' +
                     '<extra></extra>'
    ))
    
    # Add bars for high scenario  
    fig.add_trace(go.Bar(
        name='Upside',
        y=parameters,
        x=[h - baseline_value for h in high_impact],
        orientation='h',
        marker=dict(color='lightgreen'),
        base=[baseline_value] * len(parameters),
        text=[f"+${h - baseline_value:,.0f}" for h in high_impact],
        textposition='inside',
        hovertemplate='Parameter: %{y}<br>' +
                     'Upside: +$%{text}<br>' +
                     '<extra></extra>'
    ))
    
    # Add baseline line
    fig.add_vline(
        x=baseline_value,
        line_dash="dash",
        line_color="black",
        annotation_text=f"Baseline: ${baseline_value:,.0f}"
    )
    
    # Update layout
    fig.update_layout(
        title="Parameter Sensitivity: Tornado Chart",
        xaxis_title="Annual Financial Impact ($)",
        yaxis_title="Parameters",
        barmode='overlay',
        height=400 + 30 * len(parameters),
        template="plotly_white",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_roi_waterfall(
    cost_breakdown: Dict[str, float]
) -> go.Figure:
    """Create waterfall chart showing ROI components
    """
    # Prepare data
    categories = list(cost_breakdown.keys())
    values = list(cost_breakdown.values())
    
    # Calculate cumulative for waterfall
    cumulative = []
    running_total = 0
    for v in values:
        cumulative.append(running_total)
        running_total += v
    
    # Determine colors
    colors = ['red' if v < 0 else 'green' for v in values]
    colors[0] = 'blue'  # Initial investment
    colors[-1] = 'gold'  # Net result
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        name="ROI Components",
        orientation="v",
        measure=["absolute"] + ["relative"] * (len(values) - 2) + ["total"],
        x=categories,
        y=values,
        text=[f"${v:,.0f}" for v in values],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "lightgreen"}},
        decreasing={"marker": {"color": "lightcoral"}},
        totals={"marker": {"color": "gold"}}
    ))
    
    # Update layout
    fig.update_layout(
        title="ROI Waterfall Analysis",
        xaxis_title="Components",
        yaxis_title="Value ($)",
        height=500,
        template="plotly_white",
        showlegend=False
    )
    
    return fig


def plot_risk_reward_quadrant(
    scenarios: List[Dict[str, Any]]
) -> go.Figure:
    """Create risk-reward quadrant chart for different scenarios
    """
    # Extract data
    names = [s["name"] for s in scenarios]
    rewards = [s["expected_return"] for s in scenarios]
    risks = [s["risk_score"] for s in scenarios]
    sizes = [s.get("investment", 10000) / 1000 for s in scenarios]  # Scale for marker size
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add quadrant backgrounds
    fig.add_hrect(y0=0, y1=max(rewards) * 1.1, 
                  x0=0, x1=50,
                  fillcolor="lightgreen", opacity=0.2,
                  layer="below", line_width=0)
    
    fig.add_hrect(y0=0, y1=max(rewards) * 1.1,
                  x0=50, x1=100,
                  fillcolor="lightyellow", opacity=0.2,
                  layer="below", line_width=0)
    
    fig.add_hrect(y0=min(rewards) * 1.1, y1=0,
                  x0=0, x1=50,
                  fillcolor="lightblue", opacity=0.2,
                  layer="below", line_width=0)
    
    fig.add_hrect(y0=min(rewards) * 1.1, y1=0,
                  x0=50, x1=100,
                  fillcolor="lightcoral", opacity=0.2,
                  layer="below", line_width=0)
    
    # Add scatter points
    fig.add_trace(go.Scatter(
        x=risks,
        y=rewards,
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=rewards,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Return ($)")
        ),
        text=names,
        textposition="top center",
        hovertemplate='<b>%{text}</b><br>' +
                     'Risk Score: %{x:.1f}<br>' +
                     'Expected Return: $%{y:,.0f}<br>' +
                     '<extra></extra>'
    ))
    
    # Add quadrant labels
    annotations = [
        dict(x=25, y=max(rewards) * 0.9, text="Low Risk<br>High Reward", 
             showarrow=False, font=dict(size=12, color="darkgreen")),
        dict(x=75, y=max(rewards) * 0.9, text="High Risk<br>High Reward",
             showarrow=False, font=dict(size=12, color="orange")),
        dict(x=25, y=min(rewards) * 0.5, text="Low Risk<br>Low Reward",
             showarrow=False, font=dict(size=12, color="blue")),
        dict(x=75, y=min(rewards) * 0.5, text="High Risk<br>Low Reward",
             showarrow=False, font=dict(size=12, color="red"))
    ]
    
    # Update layout
    fig.update_layout(
        title="Risk-Reward Analysis",
        xaxis_title="Risk Score (0-100)",
        yaxis_title="Expected Annual Return ($)",
        height=600,
        template="plotly_white",
        annotations=annotations,
        showlegend=False
    )
    
    # Add reference lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=50, line_dash="dash", line_color="gray")
    
    return fig