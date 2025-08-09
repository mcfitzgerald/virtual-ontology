"""
GraphQL Context Management
Provides database sessions and dependencies for resolvers
"""

import strawberry
from typing import Dict, Any, Optional
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from twin.simulation_runner import SimulationRunner
from twin.recommendation_engine import RecommendationEngine
from twin.disambiguation import DisambiguationHelper
from twin.cost_impact_calculator import CostImpactCalculator
from twin.twin_state import TwinStateManager
from twin.sync_health import SyncHealthMonitor


class GraphQLContext:
    """Context object passed to all resolvers"""
    
    def __init__(
        self,
        request: Optional[Request] = None,
        db_path: str = "data/mes_database.db"
    ):
        self.request = request
        self.db_path = db_path
        
        # Initialize twin components
        self.simulation_runner = SimulationRunner()
        self.recommendation_engine = RecommendationEngine()
        self.disambiguation_helper = DisambiguationHelper()
        self.cost_calculator = CostImpactCalculator()
        self.state_manager = TwinStateManager()
        self.sync_monitor = SyncHealthMonitor()
    
    def get_db_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_sync_db_connection(self):
        """Get a sync database connection"""
        # For sync operations, we can use the same SQLite connection
        return self.get_db_connection()


async def get_context(
    request: Request,
    db_path: str = "data/mes_database.db"
) -> GraphQLContext:
    """
    Dependency injection for GraphQL context
    """
    return GraphQLContext(request=request, db_path=db_path)


# Custom context getter for Strawberry
async def custom_context_getter(request: Request) -> Dict[str, Any]:
    """
    Create context dictionary for Strawberry resolvers
    """
    context = await get_context(request)
    return {
        "request": request,
        "context": context,
        "db_path": context.db_path,
        "simulation_runner": context.simulation_runner,
        "recommendation_engine": context.recommendation_engine,
        "cost_calculator": context.cost_calculator,
        "state_manager": context.state_manager,
        "sync_monitor": context.sync_monitor
    }