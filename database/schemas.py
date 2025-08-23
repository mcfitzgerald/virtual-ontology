"""
Pydantic schemas for API request/response models

These models define the structure of data sent to and from the API,
separate from the SQLModel database models
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


# ============= Enums =============


class RunType(str, Enum):
    """Types of simulation runs"""

    BASELINE = "baseline"
    EXPERIMENT = "experiment"
    OPTIMIZATION = "optimization"
    RECOMMENDATION = "recommendation"


class RunStatus(str, Enum):
    """Status of a simulation run"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PatternType(str, Enum):
    """Types of discovered patterns"""

    CORRELATION = "correlation"
    CAUSATION = "causation"
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"


# ============= Request Models =============


class SimulationRequest(BaseModel):
    """Request to run a simulation"""

    run_type: RunType = RunType.EXPERIMENT
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Simulation parameters")
    days: int = Field(default=1, ge=1, le=30, description="Days to simulate")
    parent_run_id: Optional[str] = Field(None, description="Parent run for lineage")
    notes: Optional[str] = Field(None, description="Notes about this run")


class ExperimentRequest(BaseModel):
    """Request to create and run an experiment"""

    name: str = Field(..., description="Experiment name")
    hypothesis: str = Field(..., description="Experiment hypothesis")
    parameter_changes: Dict[str, Any] = Field(..., description="Parameters to modify")
    days: int = Field(default=1, ge=1, le=30, description="Days per simulation")
    num_runs: int = Field(default=3, ge=1, le=10, description="Number of test runs")


class SQLQueryRequest(BaseModel):
    """Request to execute SQL query"""

    sql: str = Field(..., description="SQL query to execute")
    limit: Optional[int] = Field(1000, ge=1, le=10000, description="Maximum rows to return")


class CleanupRequest(BaseModel):
    """Request to clean database"""

    category: Optional[str] = Field(
        None, description="Category to clean: historical, simulation, optimization, monitoring, metadata, logs"
    )
    tables: Optional[List[str]] = Field(None, description="Specific tables to clean")
    older_than_days: Optional[int] = Field(None, ge=1, description="Remove data older than N days")
    preserve: List[str] = Field(default_factory=list, description="Tables to preserve")


class BackupRequest(BaseModel):
    """Request to create database backup"""

    description: Optional[str] = Field(None, description="Backup description")
    compress: bool = Field(False, description="Compress backup file")


# ============= Response Models =============


class DatabaseStats(BaseModel):
    """Database statistics"""

    database_path: str
    file_size_mb: float
    total_tables: int
    total_records: int
    tables: Dict[str, int]
    ontology_version: str
    manifest_version: str
    categories: Dict[str, Dict[str, Any]]


class TableInfo(BaseModel):
    """Information about a database table"""

    name: str
    record_count: int
    columns: List[str]
    indexes: List[str]
    sample_data: Optional[List[Dict[str, Any]]] = None


class SimulationResponse(BaseModel):
    """Response from simulation run"""

    run_id: str
    status: RunStatus
    started_at: datetime
    finished_at: Optional[datetime]
    kpi_summary: Optional[Dict[str, float]]
    message: str


class ExperimentResponse(BaseModel):
    """Response from experiment creation"""

    experiment_id: str
    name: str
    status: str
    baseline_run_id: str
    test_run_ids: List[str]
    results_summary: Optional[Dict[str, Any]]
    conclusion: Optional[str]


class PatternResponse(BaseModel):
    """Discovered pattern information"""

    pattern_id: int
    pattern_type: PatternType
    pattern_name: str
    description: str
    confidence_score: float
    validated: bool
    discovered_at: datetime
    evidence: Dict[str, Any]


class RecommendationResponse(BaseModel):
    """Parameter recommendation"""

    recommendation_id: int
    recommendation_type: str
    parameter_adjustments: Dict[str, Any]
    expected_improvement: Dict[str, float]
    confidence: float
    applied: bool
    created_at: datetime


class KPISummary(BaseModel):
    """KPI summary data"""

    mean_oee: float
    mean_availability: float
    mean_performance: float
    mean_quality: float
    total_good_units: int
    total_scrap_units: int
    scrap_rate: float
    total_downtime_minutes: Optional[float]


class ComparisonResponse(BaseModel):
    """Comparison between two runs"""

    baseline_run_id: str
    comparison_run_id: str
    oee_delta: float
    availability_delta: float
    performance_delta: float
    quality_delta: float
    production_delta: int
    is_significant: bool
    analysis: Dict[str, Any]


class SQLQueryResponse(BaseModel):
    """Response from SQL query"""

    query: str
    columns: List[str]
    data: List[Dict[str, Any]]
    row_count: int
    limited: bool
    execution_time_ms: float


class BackupResponse(BaseModel):
    """Response from backup operation"""

    backup_path: str
    size_mb: float
    tables_backed_up: int
    records_backed_up: int
    created_at: datetime
    compressed: bool


class OperationResponse(BaseModel):
    """Generic operation response"""

    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# ============= List Response Models =============


class SimulationListResponse(BaseModel):
    """List of simulation runs"""

    runs: List[SimulationResponse]
    total: int
    page: int
    page_size: int


class ExperimentListResponse(BaseModel):
    """List of experiments"""

    experiments: List[ExperimentResponse]
    total: int


class PatternListResponse(BaseModel):
    """List of discovered patterns"""

    patterns: List[PatternResponse]
    total: int


class RecommendationListResponse(BaseModel):
    """List of recommendations"""

    recommendations: List[RecommendationResponse]
    total: int
