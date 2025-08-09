"""
GraphQL Resolvers for Visualization Generation
"""

import strawberry
from typing import List, Optional, Dict, Any
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .types import PlotResult
from twin.visualization import (
    create_pareto_plot,
    plot_kpi_trends,
    create_sensitivity_heatmap,
    plot_roi_distribution
)


@strawberry.type
class VisualizationQuery:
    @strawberry.field
    async def generate_pareto_plot(
        self,
        run_ids: List[str],
        objectives: List[str],
        info: strawberry.Info
    ) -> PlotResult:
        """Generate Pareto front visualization"""
        # Get run data from database
        runner = info.context["simulation_runner"]
        
        # Generate plot
        fig = create_pareto_plot(run_ids, objectives)
        
        return PlotResult(
            plot_json=fig.to_json(),
            plot_html=fig.to_html(full_html=False, include_plotlyjs='cdn'),
            plot_type="pareto",
            metadata={
                "run_ids": run_ids,
                "objectives": objectives,
                "generated_at": str(datetime.now())
            },
            export_url=None
        )
    
    @strawberry.field
    async def generate_time_series(
        self,
        run_id: str,
        kpis: List[str],
        info: strawberry.Info
    ) -> PlotResult:
        """Generate time series visualization"""
        # Generate plot
        fig = plot_kpi_trends([run_id], kpis)
        
        return PlotResult(
            plot_json=fig.to_json(),
            plot_html=fig.to_html(full_html=False, include_plotlyjs='cdn'),
            plot_type="time_series",
            metadata={
                "run_id": run_id,
                "kpis": kpis,
                "generated_at": str(datetime.now())
            },
            export_url=None
        )
    
    @strawberry.field
    async def generate_sensitivity_heatmap(
        self,
        run_ids: List[str],
        info: strawberry.Info
    ) -> PlotResult:
        """Generate parameter sensitivity heatmap"""
        # Generate plot
        fig = create_sensitivity_heatmap(run_ids)
        
        return PlotResult(
            plot_json=fig.to_json(),
            plot_html=fig.to_html(full_html=False, include_plotlyjs='cdn'),
            plot_type="heatmap",
            metadata={
                "run_ids": run_ids,
                "generated_at": str(datetime.now())
            },
            export_url=None
        )
    
    @strawberry.field
    async def generate_roi_plot(
        self,
        baseline_id: str,
        improved_id: str,
        info: strawberry.Info
    ) -> PlotResult:
        """Generate ROI distribution visualization"""
        calculator = info.context["cost_calculator"]
        
        # Calculate ROI
        roi_summary = calculator.calculate_roi(
            baseline_run_id=baseline_id,
            improved_run_id=improved_id,
            n_simulations=1000
        )
        
        # Generate plot
        fig = plot_roi_distribution(roi_summary)
        
        return PlotResult(
            plot_json=fig.to_json(),
            plot_html=fig.to_html(full_html=False, include_plotlyjs='cdn'),
            plot_type="financial",
            metadata={
                "baseline_id": baseline_id,
                "improved_id": improved_id,
                "roi_summary": roi_summary,
                "generated_at": str(datetime.now())
            },
            export_url=None
        )