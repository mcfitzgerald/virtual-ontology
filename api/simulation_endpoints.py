"""
API endpoints for virtual twin simulation functionality
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twin import (
    SimulationRunner,
    ActionableParameters,
    RecommendationEngine,
    DisambiguationHelper,
    TwinStateManager
)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


class ParameterUpdate(BaseModel):
    """Request model for parameter updates"""
    parameter_name: str
    value: float
    
class SimulationRequest(BaseModel):
    """Request model for running a simulation"""
    parameters: Dict[str, float] = Field(default_factory=dict)
    parent_run_id: Optional[str] = None
    duration_days: int = Field(default=7, ge=1, le=30)
    notes: Optional[str] = None
    seed: Optional[int] = None


class OptimizationRequest(BaseModel):
    """Request model for optimization"""
    objectives: List[str] = Field(default=["mean_oee", "downtime_percentage"])
    population_size: int = Field(default=50, ge=10, le=200)
    generations: int = Field(default=20, ge=5, le=100)
    baseline_run_id: Optional[str] = None


class QueryContextRequest(BaseModel):
    """Request model for query disambiguation"""
    query: str


@router.post("/run")
async def run_simulation(request: SimulationRequest):
    """
    Run a virtual twin simulation with specified parameters
    
    Returns simulation run ID and initial status
    """
    try:
        runner = SimulationRunner()
        
        # Create parameter object
        params = ActionableParameters()
        for param_name, value in request.parameters.items():
            params.set_value(param_name, value)
        
        # Run simulation
        run = runner.run_simulation(
            parameters=params,
            parent_run_id=request.parent_run_id,
            seed=request.seed,
            duration_days=request.duration_days,
            notes=request.notes
        )
        
        return {
            "run_id": run.run_id,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "config_delta": run.config_delta,
            "parent_run_id": run.parent_run_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/baseline")
async def create_baseline(
    duration_days: int = Query(default=7, ge=1, le=30),
    seed: int = Query(default=42),
    notes: Optional[str] = None
):
    """
    Create a baseline simulation run with default parameters
    """
    try:
        runner = SimulationRunner()
        
        run = runner.create_baseline(
            seed=seed,
            duration_days=duration_days,
            notes=notes
        )
        
        return {
            "run_id": run.run_id,
            "status": run.status,
            "kpi_summary": run.kpi_summary,
            "data_hash": run.data_hash
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}")
async def get_run_status(run_id: str):
    """
    Get status and results of a simulation run
    """
    try:
        runner = SimulationRunner()
        run = runner._get_run_metadata(run_id)
        
        return {
            "run_id": run.run_id,
            "run_type": run.run_type,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "config_delta": run.config_delta,
            "kpi_summary": run.kpi_summary,
            "parent_run_id": run.parent_run_id,
            "notes": run.notes
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/lineage")
async def get_run_lineage(run_id: str):
    """
    Get complete lineage (ancestors and descendants) of a simulation run
    """
    try:
        runner = SimulationRunner()
        lineage = runner.get_run_lineage(run_id)
        
        return {
            "run_id": run_id,
            "lineage": [
                {
                    "run_id": run.run_id,
                    "run_type": run.run_type,
                    "parent_run_id": run.parent_run_id,
                    "started_at": run.started_at.isoformat(),
                    "status": run.status
                }
                for run in lineage
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_runs(run_ids: List[str]):
    """
    Compare multiple simulation runs
    """
    try:
        runner = SimulationRunner()
        comparison = runner.compare_runs(run_ids)
        
        return comparison
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def run_optimization(request: OptimizationRequest):
    """
    Run multi-objective optimization to find optimal parameters
    """
    try:
        engine = RecommendationEngine()
        
        # Run optimization
        recommendations = engine.multi_objective_optimization(
            objectives=request.objectives,
            population_size=request.population_size,
            n_generations=request.generations
        )
        
        return {
            "pareto_front": recommendations,
            "count": len(recommendations),
            "objectives": request.objectives
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/{scenario}")
async def get_recommendations(
    scenario: str,
    baseline_run_id: Optional[str] = None
):
    """
    Get parameter recommendations for specific scenarios
    
    Scenarios:
    - improve_oee: Maximize overall equipment effectiveness
    - reduce_downtime: Minimize equipment downtime
    - improve_quality: Reduce scrap rate
    - energy_efficiency: Optimize for energy consumption
    """
    try:
        engine = RecommendationEngine()
        
        if scenario == "improve_oee":
            recommendations = engine.recommend_for_oee_improvement()
        elif scenario == "reduce_downtime":
            recommendations = engine.recommend_for_downtime_reduction()
        elif scenario == "improve_quality":
            recommendations = engine.recommend_for_quality_improvement()
        elif scenario == "energy_efficiency":
            recommendations = engine.recommend_for_energy_efficiency()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown scenario: {scenario}"
            )
        
        return {
            "scenario": scenario,
            "recommendations": recommendations,
            "baseline_run_id": baseline_run_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/context")
async def get_query_context(request: QueryContextRequest):
    """
    Get disambiguation context for a natural language query
    
    This helps the LLM understand what the user is asking about
    """
    try:
        helper = DisambiguationHelper()
        context = helper.get_query_context(request.query)
        
        return context
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters")
async def get_parameters():
    """
    Get information about all actionable parameters
    """
    try:
        params = ActionableParameters()
        
        return {
            "parameters": {
                name: {
                    "default": param.default,
                    "current": param.current,
                    "bounds": param.bounds,
                    "unit": param.unit,
                    "description": param.description
                }
                for name, param in params.parameters.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/parameters/{param_name}")
async def update_parameter(param_name: str, update: ParameterUpdate):
    """
    Update a specific parameter value
    """
    try:
        params = ActionableParameters()
        
        if param_name not in params.parameters:
            raise HTTPException(
                status_code=404,
                detail=f"Parameter {param_name} not found"
            )
        
        params.set_value(param_name, update.value)
        
        return {
            "parameter": param_name,
            "new_value": update.value,
            "bounds": params.parameters[param_name].bounds
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{entity_id}")
async def get_twin_state(entity_id: str):
    """
    Get current state of a virtual twin entity
    """
    try:
        state_manager = TwinStateManager()
        state = state_manager.get_state(entity_id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"No state found for entity {entity_id}"
            )
        
        return state
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-health")
async def get_sync_health():
    """
    Get synchronization health status for all entities
    """
    try:
        from twin import SyncHealthMonitor
        
        monitor = SyncHealthMonitor()
        summary = monitor.get_health_summary()
        entities = monitor.get_sync_health()
        
        return {
            "summary": summary,
            "entities": [
                {
                    "entity_id": entity.entity_id,
                    "entity_type": entity.entity_type,
                    "health_status": entity.health_status.value,
                    "last_update": entity.last_update.isoformat(),
                    "sync_interval_minutes": entity.sync_interval_minutes
                }
                for entity in entities
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))