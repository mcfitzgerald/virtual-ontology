"""
GraphQL Type Definitions for Virtual Twin
"""

import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


@strawberry.enum
class RunType(Enum):
    BASELINE = "baseline"
    SIMULATION = "simulation"
    RECOMMENDATION = "recommendation"


@strawberry.enum
class SyncHealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DELAYED = "DELAYED"
    STALE = "STALE"


@strawberry.type
class KPISummary:
    mean_oee: float
    mean_availability: float
    mean_performance: float
    mean_quality: float
    downtime_percentage: float
    scrap_rate: float


@strawberry.type
class TwinRun:
    run_id: str
    run_type: RunType
    seed: int
    generator_version: str
    parent_run_id: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    config_delta: Dict[str, Any]
    data_hash: str
    output_path: str
    kpi_summary: Optional[KPISummary]
    notes: Optional[str]
    status: str


@strawberry.type
class SimulationDataPoint:
    id: int
    run_id: str
    timestamp: datetime
    line_id: str
    equipment_id: str
    product_id: str
    oee: float
    availability: float
    performance: float
    quality: float
    runtime_minutes: float
    downtime_minutes: float
    units_produced: int
    units_scrapped: int
    energy_kwh: float


@strawberry.type
class ParameterUpdate:
    parameter_name: str
    old_value: float
    new_value: float
    impact_estimate: Optional[float]


@strawberry.type
class Recommendation:
    recommendation_id: str
    scenario: str
    parameters: Dict[str, float]
    expected_oee: float
    confidence_level: float
    implementation_cost: float
    payback_weeks: float


@strawberry.type
class ComparisonResult:
    baseline_run: TwinRun
    improved_run: TwinRun
    kpi_deltas: KPISummary
    percentage_improvements: Dict[str, float]
    financial_impact: Optional["ROIResult"]


@strawberry.type
class ROIResult:
    implementation_cost: float
    weekly_savings_mean: float
    weekly_savings_std: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    payback_weeks_mean: float
    npv_mean: float
    npv_probability_positive: float
    annual_benefit_mean: float


@strawberry.type
class SyncHealthReport:
    entity_id: str
    entity_type: str
    health_status: SyncHealthStatus
    last_update: datetime
    sync_interval_minutes: int
    data_freshness_seconds: float


@strawberry.type
class PlotResult:
    plot_json: str  # Plotly JSON format
    plot_html: str  # Standalone HTML
    plot_type: str  # pareto, time_series, heatmap, financial
    metadata: Dict[str, Any]
    export_url: Optional[str]


@strawberry.type
class SimulationProgress:
    run_id: str
    status: str
    progress_percentage: float
    current_step: str
    estimated_completion: Optional[datetime]
    messages: List[str]


@strawberry.input
class SimulationParameters:
    micro_stop_probability: Optional[float] = None
    performance_factor: Optional[float] = None
    scrap_multiplier: Optional[float] = None
    material_reliability: Optional[float] = None
    cascade_sensitivity: Optional[float] = None
    duration_days: int = 7
    seed: Optional[int] = None


@strawberry.input
class ROICalculationInput:
    baseline_run_id: str
    improved_run_id: str
    n_simulations: int = 10000
    time_horizon_weeks: int = 52
    include_uncertainty: bool = True