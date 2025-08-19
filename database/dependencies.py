"""
FastAPI dependencies for database access

Provides dependency injection for:
- Database sessions
- Database manager
- Repository instances
"""

from typing import Annotated, Generator
from fastapi import Depends, Request
from sqlmodel import Session

from database.manager import TwinDatabaseManager
from database.repositories import (
    TwinRunRepository,
    SimulationDataRepository,
    ExperimentRepository,
    PatternRepository,
    RecommendationRepository,
    KPIRepository
)


def get_db_manager(request: Request) -> TwinDatabaseManager:
    """Get database manager from app state"""
    return request.app.state.db_manager


def get_session(
    manager: Annotated[TwinDatabaseManager, Depends(get_db_manager)]
) -> Generator[Session, None, None]:
    """
    Create a new database session for each request
    
    Yields a SQLModel Session that will be automatically
    closed when the request is complete
    """
    with Session(manager.engine) as session:
        yield session


# Type annotations for dependency injection
SessionDep = Annotated[Session, Depends(get_session)]
ManagerDep = Annotated[TwinDatabaseManager, Depends(get_db_manager)]


# Repository dependencies
def get_twin_run_repo(session: SessionDep) -> TwinRunRepository:
    """Get TwinRun repository instance"""
    return TwinRunRepository(session)


def get_simulation_data_repo(session: SessionDep) -> SimulationDataRepository:
    """Get SimulationData repository instance"""
    return SimulationDataRepository(session)


def get_experiment_repo(session: SessionDep) -> ExperimentRepository:
    """Get Experiment repository instance"""
    return ExperimentRepository(session)


def get_pattern_repo(session: SessionDep) -> PatternRepository:
    """Get Pattern repository instance"""
    return PatternRepository(session)


def get_recommendation_repo(session: SessionDep) -> RecommendationRepository:
    """Get Recommendation repository instance"""
    return RecommendationRepository(session)


def get_kpi_repo(session: SessionDep) -> KPIRepository:
    """Get KPI repository instance"""
    return KPIRepository(session)


# Repository type annotations
TwinRunRepoDep = Annotated[TwinRunRepository, Depends(get_twin_run_repo)]
SimulationDataRepoDep = Annotated[SimulationDataRepository, Depends(get_simulation_data_repo)]
ExperimentRepoDep = Annotated[ExperimentRepository, Depends(get_experiment_repo)]
PatternRepoDep = Annotated[PatternRepository, Depends(get_pattern_repo)]
RecommendationRepoDep = Annotated[RecommendationRepository, Depends(get_recommendation_repo)]
KPIRepoDep = Annotated[KPIRepository, Depends(get_kpi_repo)]