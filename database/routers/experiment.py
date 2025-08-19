"""
Experiment and discovery endpoints

Provides API for running experiments, discovering patterns,
and generating recommendations
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from sqlmodel import select, Session

from database.dependencies import SessionDep, ManagerDep
from database.schemas import (
    ExperimentRequest, ExperimentResponse, ExperimentListResponse,
    PatternResponse, PatternListResponse,
    RecommendationResponse, RecommendationListResponse
)
from database.models import Experiment, DiscoveredPattern, ParameterRecommendation, TwinRun
from database.integration import TwinDatabaseIntegration
from database.repositories import (
    ExperimentRepository, PatternRepository, RecommendationRepository
)
from database.schemas import SimulationResponse, RunStatus
import json


router = APIRouter()


# ============= Experiments =============

@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    request: ExperimentRequest,
    manager: ManagerDep
) -> ExperimentResponse:
    """
    Create and run a new experiment
    
    This will:
    1. Create or use a baseline run
    2. Run multiple test simulations with parameter changes
    3. Analyze results
    4. Generate conclusions
    """
    
    try:
        integration = TwinDatabaseIntegration(manager)
        
        experiment_id = integration.run_experiment(
            name=request.name,
            hypothesis=request.hypothesis,
            parameter_changes=request.parameter_changes,
            days=request.days,
            num_runs=request.num_runs
        )
        
        # Get experiment details
        with Session(manager.engine) as session:
            experiment = session.get(Experiment, experiment_id)
            
            if not experiment:
                raise HTTPException(
                    status_code=500,
                    detail="Experiment completed but record not found"
                )
            
            test_runs = json.loads(experiment.test_runs_json)
            results_summary = None
            if experiment.results_summary_json:
                results_summary = json.loads(experiment.results_summary_json)
            
            return ExperimentResponse(
                experiment_id=experiment.experiment_id,
                name=experiment.experiment_name,
                status=experiment.status,
                baseline_run_id=experiment.baseline_run_id,
                test_run_ids=test_runs,
                results_summary=results_summary,
                conclusion=experiment.conclusion
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Experiment failed: {str(e)}"
        )


@router.get("/", response_model=ExperimentListResponse)
async def list_experiments(
    session: SessionDep,
    status: str = None
) -> ExperimentListResponse:
    """
    List all experiments with optional status filter
    """
    
    query = select(Experiment)
    if status:
        query = query.where(Experiment.status == status)
    query = query.order_by(Experiment.created_at.desc())
    
    experiments = session.exec(query).all()
    
    responses = []
    for exp in experiments:
        test_runs = json.loads(exp.test_runs_json)
        results_summary = None
        if exp.results_summary_json:
            results_summary = json.loads(exp.results_summary_json)
        
        responses.append(ExperimentResponse(
            experiment_id=exp.experiment_id,
            name=exp.experiment_name,
            status=exp.status,
            baseline_run_id=exp.baseline_run_id,
            test_run_ids=test_runs,
            results_summary=results_summary,
            conclusion=exp.conclusion
        ))
    
    return ExperimentListResponse(
        experiments=responses,
        total=len(responses)
    )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    session: SessionDep
) -> ExperimentResponse:
    """
    Get details of a specific experiment
    """
    
    experiment = session.get(Experiment, experiment_id)
    
    if not experiment:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment '{experiment_id}' not found"
        )
    
    test_runs = json.loads(experiment.test_runs_json)
    results_summary = None
    if experiment.results_summary_json:
        results_summary = json.loads(experiment.results_summary_json)
    
    return ExperimentResponse(
        experiment_id=experiment.experiment_id,
        name=experiment.experiment_name,
        status=experiment.status,
        baseline_run_id=experiment.baseline_run_id,
        test_run_ids=test_runs,
        results_summary=results_summary,
        conclusion=experiment.conclusion
    )


# ============= Patterns =============

@router.get("/patterns", response_model=PatternListResponse)
async def list_patterns(
    session: SessionDep,
    min_confidence: float = 0.0,
    validated_only: bool = False
) -> PatternListResponse:
    """
    List discovered patterns with optional filtering
    """
    
    query = select(DiscoveredPattern)
    
    if min_confidence > 0:
        query = query.where(DiscoveredPattern.confidence_score >= min_confidence)
    if validated_only:
        query = query.where(DiscoveredPattern.validated == True)
    
    query = query.order_by(DiscoveredPattern.confidence_score.desc())
    
    patterns = session.exec(query).all()
    
    responses = []
    for pattern in patterns:
        evidence = json.loads(pattern.evidence_json)
        
        responses.append(PatternResponse(
            pattern_id=pattern.pattern_id,
            pattern_type=pattern.pattern_type,
            pattern_name=pattern.pattern_name,
            description=pattern.description,
            confidence_score=pattern.confidence_score,
            validated=pattern.validated,
            discovered_at=pattern.discovered_at,
            evidence=evidence
        ))
    
    return PatternListResponse(
        patterns=responses,
        total=len(responses)
    )


@router.post("/patterns/discover")
async def discover_patterns(
    manager: ManagerDep,
    min_confidence: float = 0.7
) -> PatternListResponse:
    """
    Discover new patterns from completed experiments
    """
    
    try:
        integration = TwinDatabaseIntegration(manager)
        patterns = integration.discover_patterns(min_confidence=min_confidence)
        
        responses = []
        for pattern in patterns:
            evidence = json.loads(pattern.evidence_json)
            
            responses.append(PatternResponse(
                pattern_id=pattern.pattern_id,
                pattern_type=pattern.pattern_type,
                pattern_name=pattern.pattern_name,
                description=pattern.description,
                confidence_score=pattern.confidence_score,
                validated=pattern.validated,
                discovered_at=pattern.discovered_at,
                evidence=evidence
            ))
        
        return PatternListResponse(
            patterns=responses,
            total=len(responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pattern discovery failed: {str(e)}"
        )


@router.post("/patterns/{pattern_id}/validate")
async def validate_pattern(
    pattern_id: int,
    validation_run_ids: List[str],
    session: SessionDep
) -> Dict[str, str]:
    """
    Mark a pattern as validated with supporting runs
    """
    
    pattern = session.get(DiscoveredPattern, pattern_id)
    if not pattern:
        raise HTTPException(
            status_code=404,
            detail=f"Pattern {pattern_id} not found"
        )
    
    pattern_repo = PatternRepository(session)
    pattern_repo.validate_pattern(pattern_id, validation_run_ids)
    
    return {
        "message": f"Pattern {pattern_id} validated with {len(validation_run_ids)} runs"
    }


# ============= Recommendations =============

@router.get("/recommendations", response_model=RecommendationListResponse)
async def list_recommendations(
    session: SessionDep,
    applied_only: bool = False,
    min_confidence: float = 0.0
) -> RecommendationListResponse:
    """
    List parameter recommendations
    """
    
    query = select(ParameterRecommendation)
    
    if applied_only:
        query = query.where(ParameterRecommendation.applied == True)
    if min_confidence > 0:
        query = query.where(ParameterRecommendation.confidence >= min_confidence)
    
    query = query.order_by(ParameterRecommendation.confidence.desc())
    
    recommendations = session.exec(query).all()
    
    responses = []
    for rec in recommendations:
        adjustments = json.loads(rec.parameter_adjustments_json)
        expected = json.loads(rec.expected_improvement_json)
        
        responses.append(RecommendationResponse(
            recommendation_id=rec.recommendation_id,
            recommendation_type=rec.recommendation_type,
            parameter_adjustments=adjustments,
            expected_improvement=expected,
            confidence=rec.confidence,
            applied=rec.applied,
            created_at=rec.created_at
        ))
    
    return RecommendationListResponse(
        recommendations=responses,
        total=len(responses)
    )


@router.post("/recommendations/generate")
async def generate_recommendations(
    manager: ManagerDep
) -> RecommendationListResponse:
    """
    Generate new recommendations from discovered patterns
    """
    
    try:
        integration = TwinDatabaseIntegration(manager)
        recommendations = integration.generate_recommendations()
        
        responses = []
        for rec in recommendations:
            adjustments = json.loads(rec.parameter_adjustments_json)
            expected = json.loads(rec.expected_improvement_json)
            
            responses.append(RecommendationResponse(
                recommendation_id=rec.recommendation_id,
                recommendation_type=rec.recommendation_type,
                parameter_adjustments=adjustments,
                expected_improvement=expected,
                confidence=rec.confidence,
                applied=rec.applied,
                created_at=rec.created_at
            ))
        
        return RecommendationListResponse(
            recommendations=responses,
            total=len(responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {str(e)}"
        )


@router.post("/recommendations/{recommendation_id}/apply")
async def apply_recommendation(
    recommendation_id: int,
    session: SessionDep,
    manager: ManagerDep
) -> SimulationResponse:
    """
    Apply a recommendation by running a simulation with recommended parameters
    """
    
    recommendation = session.get(ParameterRecommendation, recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation {recommendation_id} not found"
        )
    
    if recommendation.applied:
        raise HTTPException(
            status_code=400,
            detail="Recommendation has already been applied"
        )
    
    # Get parameter adjustments
    adjustments = json.loads(recommendation.parameter_adjustments_json)
    
    # Run simulation with recommended parameters
    integration = TwinDatabaseIntegration(manager)
    run_id = integration.run_simulation_to_db(
        run_type="recommendation",
        parameters=adjustments,
        days=7  # Default to 7 days
    )
    
    # Calculate actual improvement
    # (This would compare against baseline - simplified here)
    actual_improvement = {"oee": 0, "production": 0}  # Placeholder
    
    # Mark recommendation as applied
    rec_repo = RecommendationRepository(session)
    rec_repo.apply_recommendation(
        recommendation_id,
        run_id,
        actual_improvement
    )
    
    # Get run details for response
    with Session(manager.engine) as session:
        run = session.get(TwinRun, run_id)
        kpi_summary = None
        if run.kpi_summary_json:
            kpi_summary = json.loads(run.kpi_summary_json)
        
        return SimulationResponse(
            run_id=run.run_id,
            status=RunStatus(run.status),
            started_at=run.started_at,
            finished_at=run.finished_at,
            kpi_summary=kpi_summary,
            message=f"Recommendation {recommendation_id} applied successfully"
        )