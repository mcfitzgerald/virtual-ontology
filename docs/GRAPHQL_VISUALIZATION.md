# GraphQL API and Visualization Documentation

## Overview

This document describes the GraphQL API and visualization components added to the Virtual Twin system. These optional components provide:

1. **GraphQL API**: Type-safe, real-time API with subscriptions for querying and monitoring the virtual twin
2. **Interactive Visualizations**: Plotly-based charts for optimization analysis, KPI tracking, and financial impact

## GraphQL API

### Architecture

The GraphQL layer is built with Strawberry and integrated with FastAPI:

```
api/graphql/
├── schema.py              # Main schema definition
├── types.py               # GraphQL type definitions
├── resolvers.py           # Query and mutation resolvers
├── subscriptions.py       # Real-time subscriptions
├── visualization_resolvers.py  # Visualization-specific resolvers
├── context.py            # Context management
└── router.py             # FastAPI integration
```

### Schema Overview

#### Queries

```graphql
type Query {
  # Health check
  healthCheck: String!
  
  # Get simulation runs
  getRuns(limit: Int, runType: RunType): [TwinRun!]!
  getRun(runId: String!): TwinRun
  
  # Get recommendations
  getRecommendations(scenario: String!): [Recommendation!]!
  
  # Get sync health reports
  getSyncHealth: [SyncHealthReport!]!
  
  # Visualization queries
  visualization: VisualizationQuery!
}
```

#### Mutations

```graphql
type Mutation {
  # Run simulation
  runSimulation(config: SimulationInput!): TwinRun!
  
  # Update parameters
  updateParameters(changes: ParameterInput!): [ParameterUpdate!]!
  
  # Apply recommendation
  applyRecommendation(recommendationId: String!): ApplyResult!
  
  # Calculate ROI
  calculateRoi(baselineId: String!, improvedId: String!): ROIResult!
}
```

#### Subscriptions

```graphql
type Subscription {
  # Real-time sync health monitoring
  syncHealthUpdates: [SyncHealthReport!]!
  
  # Simulation progress tracking
  simulationProgress(runId: String!): SimulationProgress!
}
```

### Example Queries

#### Get Recent Runs
```graphql
query GetRecentRuns {
  getRuns(limit: 10, runType: OPTIMIZATION) {
    runId
    runType
    status
    timestamp
    kpiSummary {
      meanOee
      meanAvailability
      meanPerformance
      meanQuality
    }
  }
}
```

#### Run Optimization
```graphql
mutation RunOptimization {
  runSimulation(config: {
    runType: OPTIMIZATION,
    duration: 100,
    objectives: ["oee", "energy"],
    constraints: ["quality >= 0.95"]
  }) {
    runId
    status
    optimizationResult {
      paretoFront
      bestConfigurations
    }
  }
}
```

#### Subscribe to Progress
```graphql
subscription TrackProgress {
  simulationProgress(runId: "opt-run-123") {
    runId
    status
    progressPercentage
    currentStep
    estimatedCompletion
    kpiSnapshot {
      oee
      availability
    }
  }
}
```

### WebSocket Support

The GraphQL API supports real-time subscriptions via WebSocket:

- Protocols: `graphql-transport-ws`, `graphql-ws`
- Endpoint: `/graphql`
- GraphiQL IDE: Available at `/graphql` in browser

### Context Management

The GraphQL context provides access to:
- `simulation_runner`: Twin simulation engine
- `recommendation_engine`: AI recommendation system
- `cost_calculator`: ROI calculation
- `sync_monitor`: Real-time monitoring
- `db_path`: Database connection

## Visualization Components

### Module Structure

```
twin/visualization/
├── __init__.py
├── pareto_plots.py       # Multi-objective optimization plots
├── time_series.py        # KPI trend analysis
├── heatmaps.py          # Sensitivity analysis
└── financial_plots.py    # ROI and cost impact
```

### Pareto Front Visualization

Shows trade-offs between competing objectives:

```python
from twin.visualization import create_pareto_plot

fig = create_pareto_plot(
    run_ids=["opt1", "opt2", "opt3"],
    objectives=["oee", "energy"]
)
```

Features:
- Non-dominated solution identification
- Interactive hover details
- Objective space exploration
- Export to JSON/HTML

### Time Series Analysis

Track KPI evolution over time:

```python
from twin.visualization import plot_kpi_trends

fig = plot_kpi_trends(
    run_ids=["baseline", "improved"],
    kpis=["oee", "availability", "performance"]
)
```

Features:
- Multi-run comparison
- Confidence bands
- Range slider for zooming
- Anomaly highlighting

### Sensitivity Heatmaps

Analyze parameter impact on KPIs:

```python
from twin.visualization import create_sensitivity_heatmap

fig = create_sensitivity_heatmap(
    run_ids=["baseline", "scenario1", "scenario2"]
)
```

Shows:
- Parameter-KPI correlations
- High-impact relationships (marked with ⚠)
- Equipment performance matrix
- Color-coded impact levels

### Financial Analysis

ROI distribution with Monte Carlo confidence:

```python
from twin.visualization import plot_roi_distribution

fig = plot_roi_distribution(roi_summary)
```

Includes:
- Weekly savings distribution
- Payback period analysis
- NPV with confidence intervals
- Annual benefit projections

## GraphQL + Visualization Integration

Query visualizations through GraphQL:

```graphql
query GenerateParetoPlot {
  visualization {
    generateParetoPlot(
      runIds: ["opt1", "opt2"],
      objectives: ["oee", "energy"]
    ) {
      plotType
      plotJson
      plotHtml
      metadata
    }
  }
}
```

## Usage Examples

### 1. Complete Optimization Workflow

```python
# Run optimization
mutation = """
mutation {
  runSimulation(config: {
    runType: OPTIMIZATION,
    objectives: ["oee", "energy"]
  }) {
    runId
  }
}
"""

# Track progress
subscription = """
subscription($runId: String!) {
  simulationProgress(runId: $runId) {
    progressPercentage
    currentStep
  }
}
"""

# Visualize results
query = """
query($runId: String!) {
  visualization {
    generateParetoPlot(
      runIds: [$runId],
      objectives: ["oee", "energy"]
    ) {
      plotHtml
    }
  }
}
"""
```

### 2. Financial Impact Analysis

```python
# Calculate ROI
mutation = """
mutation {
  calculateRoi(
    baselineId: "baseline-run",
    improvedId: "optimized-run"
  ) {
    weeklyBenefit
    paybackWeeks
    npv
    confidence
  }
}
"""

# Generate ROI visualization
query = """
query {
  visualization {
    generateRoiPlot(
      baselineId: "baseline-run",
      improvedId: "optimized-run"
    ) {
      plotHtml
    }
  }
}
"""
```

### 3. Real-time Monitoring

```python
import asyncio
from api.graphql.schema import schema

async def monitor_health():
    subscription = """
    subscription {
      syncHealthUpdates {
        equipmentId
        health
        alerts
      }
    }
    """
    
    async for result in schema.subscribe(subscription):
        if result.data:
            for report in result.data['syncHealthUpdates']:
                if report['health'] < 0.8:
                    print(f"Alert: {report['equipmentId']} health degraded")
```

## Testing

Run the test suites:

```bash
# Test GraphQL API
python tests/test_graphql_api.py

# Test visualizations
python tests/test_visualizations.py
```

## Performance Considerations

1. **Query Optimization**
   - Use field selection to reduce payload
   - Implement DataLoader for batch loading
   - Cache frequently accessed data

2. **Visualization Performance**
   - Limit data points for large datasets
   - Use Plotly's WebGL renderer for >1000 points
   - Implement server-side aggregation

3. **Subscription Efficiency**
   - Throttle update frequency
   - Use filtering to reduce messages
   - Implement connection pooling

## Security

1. **Authentication**: Integrate with existing auth system
2. **Rate Limiting**: Apply per-client limits
3. **Query Depth**: Limit nested query depth
4. **Input Validation**: Validate all mutation inputs

## Future Enhancements

1. **Advanced Visualizations**
   - 3D Pareto surfaces
   - Animation of optimization progress
   - AR/VR integration

2. **GraphQL Federation**
   - Microservice architecture
   - Schema stitching
   - Distributed resolvers

3. **AI-Powered Insights**
   - Automated anomaly detection
   - Predictive visualizations
   - Natural language queries

## Conclusion

The GraphQL API and visualization components provide powerful tools for:
- Real-time monitoring and control
- Interactive data exploration
- Financial impact analysis
- Multi-objective optimization visualization

These components integrate seamlessly with the existing virtual twin infrastructure while maintaining ISO 23247 compliance and supporting the natural language interaction patterns established in the core system.