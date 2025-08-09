"""
GraphQL API for Virtual Twin
Provides type-safe querying and real-time subscriptions
"""

from .schema import schema
from .router import graphql_router

__all__ = ["schema", "graphql_router"]