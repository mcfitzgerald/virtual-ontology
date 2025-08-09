"""
Main GraphQL Schema Definition
"""

import strawberry
from datetime import datetime

from .resolvers import Query, Mutation
from .subscriptions import Subscription
from .visualization_resolvers import VisualizationQuery


@strawberry.type
class ExtendedQuery(Query):
    """Extended query with visualization capabilities"""
    
    @strawberry.field
    def visualization(self) -> VisualizationQuery:
        """Access visualization queries"""
        return VisualizationQuery()
    
    @strawberry.field
    def health_check(self) -> str:
        """Simple health check endpoint"""
        return f"Virtual Twin GraphQL API is healthy at {datetime.now().isoformat()}"


# Create the schema
schema = strawberry.Schema(
    query=ExtendedQuery,
    mutation=Mutation,
    subscription=Subscription
)