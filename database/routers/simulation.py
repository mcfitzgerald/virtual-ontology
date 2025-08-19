"""
Simulation management endpoints

Provides API for running and managing twin simulations
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import select, Session

from database.dependencies import SessionDep, ManagerDep
from database.schemas import (
    SimulationRequest, SimulationResponse, SimulationListResponse,
    KPISummary, ComparisonResponse, RunStatus
)
from database.models import TwinRun, SimulationData
from database.integration import TwinDatabaseIntegration
from database.repositories import (
    TwinRunRepository, SimulationDataRepository, KPIRepository
)


router = APIRouter()


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    manager: ManagerDep
) -> SimulationResponse:
    """
    Run a new simulation with specified parameters
    
    This endpoint:
    1. Creates a new simulation run record
    2. Executes the SimPy simulation
    3. Stores results in MES format
    4. Calculates KPIs
    5. Returns run summary
    """
    
    try:
        # Create integration instance
        integration = TwinDatabaseIntegration(manager)
        
        # Run simulation
        run_id = integration.run_simulation_to_db(
            run_type=request.run_type.value,
            parameters=request.parameters,
            days=request.days,
            parent_run_id=request.parent_run_id
        )
        
        # Get run details
        with Session(manager.engine) as session:
            run = session.get(TwinRun, run_id)
            
            if not run:
                raise HTTPException(
                    status_code=500,
                    detail="Simulation run completed but record not found"
                )
            
            # Parse KPI summary
            kpi_summary = None
            if run.kpi_summary_json:
                import json
                kpi_summary = json.loads(run.kpi_summary_json)
            
            return SimulationResponse(
                run_id=run.run_id,
                status=RunStatus(run.status),
                started_at=run.started_at,
                finished_at=run.finished_at,
                kpi_summary=kpi_summary,
                message=f"Simulation completed successfully in {request.days} days"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(e)}"
        )


@router.get("/", response_model=SimulationListResponse)
async def list_simulations(
    session: SessionDep,
    run_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
) -> SimulationListResponse:
    """
    List simulation runs with optional filtering
    
    Filter by:
    - run_type: baseline, experiment, optimization, recommendation
    - status: pending, running, completed, failed
    """
    
    # Build query
    query = select(TwinRun)
    
    if run_type:
        query = query.where(TwinRun.run_type == run_type)
    if status:
        query = query.where(TwinRun.status == status)
    
    # Order by most recent first
    query = query.order_by(TwinRun.started_at.desc())
    
    # Get total count
    total = len(session.exec(query).all())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    runs = session.exec(query).all()
    
    # Convert to response models
    run_responses = []
    for run in runs:
        kpi_summary = None
        if run.kpi_summary_json:
            import json
            kpi_summary = json.loads(run.kpi_summary_json)
        
        run_responses.append(SimulationResponse(
            run_id=run.run_id,
            status=RunStatus(run.status),
            started_at=run.started_at,
            finished_at=run.finished_at,
            kpi_summary=kpi_summary,
            message=f"Run type: {run.run_type}"
        ))
    
    return SimulationListResponse(
        runs=run_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{run_id}", response_model=SimulationResponse)
async def get_simulation(
    run_id: str,
    session: SessionDep
) -> SimulationResponse:
    """
    Get details of a specific simulation run
    """
    
    run = session.get(TwinRun, run_id)
    
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation run '{run_id}' not found"
        )
    
    kpi_summary = None
    if run.kpi_summary_json:
        import json
        kpi_summary = json.loads(run.kpi_summary_json)
    
    return SimulationResponse(
        run_id=run.run_id,
        status=RunStatus(run.status),
        started_at=run.started_at,
        finished_at=run.finished_at,
        kpi_summary=kpi_summary,
        message=f"Run type: {run.run_type}, Days: {run.simulation_days}"
    )


@router.get("/{run_id}/data")
async def get_simulation_data(
    run_id: str,
    session: SessionDep,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get raw simulation data in MES format
    
    Returns the simulation output data with pagination
    """
    
    # Check if run exists
    run = session.get(TwinRun, run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation run '{run_id}' not found"
        )
    
    # Get simulation data
    query = select(SimulationData).where(
        SimulationData.run_id == run_id
    ).order_by(SimulationData.timestamp)
    
    # Get total count
    total = len(session.exec(query).all())
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    data = session.exec(query).all()
    
    # Convert to dictionaries
    data_dicts = []
    for record in data:
        data_dicts.append({
            "timestamp": record.timestamp,
            "line_id": record.line_id,
            "equipment_id": record.equipment_id,
            "equipment_type": record.equipment_type,
            "machine_status": record.machine_status,
            "good_units_produced": record.good_units_produced,
            "scrap_units_produced": record.scrap_units_produced,
            "oee_score": record.oee_score,
            "availability_score": record.availability_score,
            "performance_score": record.performance_score,
            "quality_score": record.quality_score
        })
    
    return {
        "run_id": run_id,
        "total_records": total,
        "offset": offset,
        "limit": limit,
        "data": data_dicts
    }


@router.get("/{run_id}/kpis", response_model=KPISummary)
async def get_simulation_kpis(
    run_id: str,
    session: SessionDep
) -> KPISummary:
    """
    Get KPI summary for a simulation run
    
    Calculates:
    - Mean OEE, Availability, Performance, Quality
    - Total production and scrap
    - Scrap rate
    """
    
    # Check if run exists
    run = session.get(TwinRun, run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation run '{run_id}' not found"
        )
    
    # Calculate KPIs
    sim_data_repo = SimulationDataRepository(session)
    kpi_data = sim_data_repo.calculate_kpi_snapshot(run_id)
    
    if not kpi_data:
        raise HTTPException(
            status_code=404,
            detail=f"No simulation data found for run '{run_id}'"
        )
    
    return KPISummary(**kpi_data)


@router.post("/compare", response_model=ComparisonResponse)
async def compare_simulations(
    baseline_run_id: str,
    comparison_run_id: str,
    session: SessionDep
) -> ComparisonResponse:
    """
    Compare two simulation runs
    
    Calculates deltas for all KPIs and determines
    if the difference is statistically significant
    """
    
    try:
        kpi_repo = KPIRepository(session)
        comparison = kpi_repo.create_comparison(
            baseline_run_id=baseline_run_id,
            comparison_run_id=comparison_run_id
        )
        
        import json
        analysis = json.loads(comparison.analysis_json)
        
        return ComparisonResponse(
            baseline_run_id=comparison.baseline_run_id,
            comparison_run_id=comparison.comparison_run_id,
            oee_delta=comparison.oee_delta,
            availability_delta=comparison.availability_delta,
            performance_delta=comparison.performance_delta,
            quality_delta=comparison.quality_delta,
            production_delta=comparison.production_delta,
            is_significant=comparison.is_significant,
            analysis=analysis
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@router.delete("/{run_id}")
async def delete_simulation(
    run_id: str,
    session: SessionDep
) -> Dict[str, str]:
    """
    Delete a simulation run and all associated data
    
    This will remove:
    - The run record
    - All simulation data
    - Any KPI snapshots
    """
    
    # Check if run exists
    run = session.get(TwinRun, run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation run '{run_id}' not found"
        )
    
    # Delete simulation data
    sim_data = session.exec(
        select(SimulationData).where(SimulationData.run_id == run_id)
    ).all()
    
    for record in sim_data:
        session.delete(record)
    
    # Delete the run
    session.delete(run)
    session.commit()
    
    return {
        "message": f"Simulation run '{run_id}' and {len(sim_data)} data records deleted"
    }