"""
FastAPI Router for GraphQL
"""

from fastapi import FastAPI, Depends, Request
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from .schema import schema
from .context import custom_context_getter


# Create GraphQL router with WebSocket support
graphql_router = GraphQLRouter(
    schema,
    context_getter=custom_context_getter,
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ],
    graphql_ide="graphiql"  # Enable GraphiQL interface
)


def create_graphql_app() -> FastAPI:
    """Create FastAPI app with GraphQL endpoint"""
    app = FastAPI(
        title="Virtual Twin GraphQL API",
        description="GraphQL API for Virtual Twin with real-time subscriptions",
        version="1.0.0"
    )
    
    # Add GraphQL endpoint
    app.include_router(graphql_router, prefix="/graphql")
    
    # Add health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "Virtual Twin GraphQL"}
    
    return app


# Export for use in main app
__all__ = ["graphql_router", "create_graphql_app"]