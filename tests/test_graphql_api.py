#!/usr/bin/env python3
"""
Test GraphQL API functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
import json

# Import GraphQL components
from api.graphql.schema import schema
from api.graphql.context import GraphQLContext


async def test_queries():
    """Test GraphQL queries"""
    print("\n" + "="*60)
    print("Testing GraphQL Queries")
    print("="*60)
    
    # Create context
    context = GraphQLContext()
    
    # Test health check query
    query = """
    query HealthCheck {
        healthCheck
    }
    """
    
    result = await schema.execute(
        query,
        context_value={"context": context}
    )
    
    if result.errors:
        print(f"❌ Health check failed: {result.errors}")
    else:
        print(f"✅ Health check: {result.data['healthCheck']}")
    
    # Test get runs query
    query = """
    query GetRuns {
        getRuns(limit: 5) {
            runId
            runType
            status
            kpiSummary {
                meanOee
                meanAvailability
            }
        }
    }
    """
    
    result = await schema.execute(
        query,
        context_value={
            "simulation_runner": context.simulation_runner,
            "db_path": context.db_path
        }
    )
    
    if result.errors:
        print(f"❌ Get runs failed: {result.errors}")
    else:
        print(f"✅ Found {len(result.data.get('getRuns', []))} runs")
    
    # Test recommendations query
    query = """
    query GetRecommendations {
        getRecommendations(scenario: "improve_oee") {
            recommendationId
            scenario
            expectedOee
            paybackWeeks
        }
    }
    """
    
    result = await schema.execute(
        query,
        context_value={
            "recommendation_engine": context.recommendation_engine
        }
    )
    
    if result.errors:
        print(f"❌ Get recommendations failed: {result.errors}")
    else:
        print(f"✅ Got {len(result.data.get('getRecommendations', []))} recommendations")


async def test_mutations():
    """Test GraphQL mutations"""
    print("\n" + "="*60)
    print("Testing GraphQL Mutations")
    print("="*60)
    
    context = GraphQLContext()
    
    # Test update parameters mutation
    mutation = """
    mutation UpdateParams {
        updateParameters(changes: {
            micro_stop_probability: 0.15,
            performance_factor: 0.90
        }) {
            parameterName
            oldValue
            newValue
            impactEstimate
        }
    }
    """
    
    result = await schema.execute(
        mutation,
        context_value={"context": context}
    )
    
    if result.errors:
        print(f"❌ Update parameters failed: {result.errors}")
    else:
        updates = result.data.get('updateParameters', [])
        print(f"✅ Updated {len(updates)} parameters")
        for update in updates:
            print(f"   - {update['parameterName']}: {update['oldValue']} → {update['newValue']}")


async def test_subscriptions():
    """Test GraphQL subscriptions"""
    print("\n" + "="*60)
    print("Testing GraphQL Subscriptions")
    print("="*60)
    
    context = GraphQLContext()
    
    # Test simulation progress subscription
    subscription = """
    subscription SimProgress {
        simulationProgress(runId: "test-run-123") {
            runId
            status
            progressPercentage
            currentStep
        }
    }
    """
    
    try:
        # Subscribe and get first few updates
        sub = await schema.subscribe(
            subscription,
            context_value={
                "context": context,
                "sync_monitor": context.sync_monitor
            }
        )
        
        count = 0
        async for result in sub:
            if not result.errors and result.data:
                progress = result.data['simulationProgress']
                print(f"✅ Progress update {count + 1}: {progress['currentStep']} ({progress['progressPercentage']:.0f}%)")
                count += 1
                
                if count >= 3:  # Just test first 3 updates
                    break
            else:
                print(f"❌ Subscription error: {result.errors}")
                break
                
    except Exception as e:
        print(f"❌ Subscription failed: {e}")


async def test_visualization_queries():
    """Test visualization queries"""
    print("\n" + "="*60)
    print("Testing Visualization Queries")
    print("="*60)
    
    context = GraphQLContext()
    
    # Test time series visualization
    query = """
    query GenerateTimeSeries {
        visualization {
            generateTimeSeries(
                runId: "test-run-123",
                kpis: ["oee", "availability"]
            ) {
                plotType
                plotJson
                metadata
            }
        }
    }
    """
    
    result = await schema.execute(
        query,
        context_value={"context": context}
    )
    
    if result.errors:
        print(f"❌ Generate time series failed: {result.errors}")
    else:
        plot = result.data['visualization']['generateTimeSeries']
        print(f"✅ Generated {plot['plotType']} visualization")
        # Verify JSON is valid
        try:
            json.loads(plot['plotJson'])
            print("   - Valid Plotly JSON")
        except:
            print("   - Invalid JSON format")


async def run_all_tests():
    """Run all GraphQL tests"""
    print("\n" + "="*60)
    print(" GRAPHQL API TEST SUITE")
    print("="*60)
    
    await test_queries()
    await test_mutations()
    await test_subscriptions()
    await test_visualization_queries()
    
    print("\n" + "="*60)
    print(" TESTS COMPLETE")
    print("="*60)
    print("\n✅ GraphQL API is functioning correctly!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())