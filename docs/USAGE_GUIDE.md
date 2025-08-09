# Virtual Twin System - Complete Usage Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Operations](#basic-operations)
3. [Natural Language Interface](#natural-language-interface)
4. [Simulation & Optimization](#simulation--optimization)
5. [GraphQL API Usage](#graphql-api-usage)
6. [Visualization Tools](#visualization-tools)
7. [Advanced Scenarios](#advanced-scenarios)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd virtual-ontology

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_database.py

# Run tests to verify installation
python -m pytest tests/
```

### Quick Start

```python
# Basic twin initialization
from twin.twin_ontology import VirtualTwin

# Create virtual twin instance
twin = VirtualTwin(twin_id="factory-twin-001")

# Initialize with equipment
twin.add_equipment("LINE1-FIL", "Filler", "LINE1")
twin.add_equipment("LINE1-PCK", "Packer", "LINE1")

# Add sensors
twin.add_sensor("SENSOR-001", "OEE", "percentage", "LINE1-FIL")

# Start monitoring
twin.start_sync()
```

## Basic Operations

### 1. Creating a Digital Twin

```python
from twin.twin_ontology import VirtualTwin, EquipmentState
from twin.actionable_parameters import ActionableParameters

# Initialize twin
twin = VirtualTwin(twin_id="my-factory")

# Configure parameters
params = ActionableParameters()
params.set_parameter("micro_stop_probability", 0.05)
params.set_parameter("performance_factor", 0.85)

# Apply configuration
twin.apply_parameters(params)
```

### 2. Running Simulations

```python
from twin.simulation_runner import SimulationRunner, RunType

# Create simulation runner
runner = SimulationRunner(db_path="data/mes_database.db")

# Run baseline simulation
result = runner.run_simulation(
    run_type=RunType.BASELINE,
    duration=100,
    config=params.get_all_parameters()
)

print(f"Baseline OEE: {result['kpi_summary']['mean_oee']:.2%}")
```

### 3. Monitoring Real-Time Data

```python
from twin.sync_monitor import SyncMonitor

# Initialize monitor
monitor = SyncMonitor(twin)

# Start monitoring
monitor.start()

# Get health reports
health_reports = monitor.get_health_reports()
for report in health_reports:
    print(f"{report.equipment_id}: Health={report.health:.2f}")
```

## Natural Language Interface

### Understanding User Intent

The system recognizes 8 intent patterns:

```python
from twin.natural_language_patterns import NaturalLanguageProcessor

nlp = NaturalLanguageProcessor()

# Example queries and their intents
queries = [
    "What is the current OEE?",                    # STATUS
    "Show me trends for the last week",            # TREND
    "Compare LINE1 and LINE2",                     # COMPARISON
    "What if we reduce micro stops by 20%?",       # PREDICTION
    "How can we improve OEE?",                     # OPTIMIZATION
    "Why is quality low?",                         # ROOT_CAUSE
    "What should we do next?",                     # RECOMMENDATION
    "Alert me if OEE drops below 60%"              # ALERT
]

for query in queries:
    intent = nlp.classify_intent(query)
    entities = nlp.extract_entities(query)
    print(f"Query: {query}")
    print(f"Intent: {intent}")
    print(f"Entities: {entities}\n")
```

### Processing Natural Language Requests

```python
from twin.natural_language_patterns import process_user_query

# Process a complex query
query = "How can we improve OEE by 10% while reducing energy costs?"
response = process_user_query(query, twin, runner)

print(response['intent'])           # OPTIMIZATION
print(response['recommendations'])  # List of actionable recommendations
print(response['expected_impact'])  # Quantified improvements
```

## Simulation & Optimization

### Multi-Objective Optimization

```python
from twin.optimization_engine import OptimizationEngine

# Initialize optimizer
optimizer = OptimizationEngine()

# Define objectives and constraints
result = optimizer.optimize(
    objectives=["maximize:oee", "minimize:energy_consumption"],
    constraints=[
        "quality >= 0.95",
        "availability >= 0.75"
    ],
    n_generations=50,
    population_size=100
)

# Get Pareto-optimal solutions
pareto_front = result['pareto_front']
for solution in pareto_front[:5]:  # Top 5 solutions
    print(f"OEE: {solution['oee']:.2%}, Energy: {solution['energy']:.2f} kWh")
```

### Monte Carlo Analysis

```python
# Run Monte Carlo simulation for uncertainty analysis
from twin.simulation_runner import RunType

result = runner.run_simulation(
    run_type=RunType.MONTE_CARLO,
    duration=100,
    n_simulations=1000,
    config=params.get_all_parameters()
)

# Get confidence intervals
ci = result['confidence_intervals']
print(f"OEE: {ci['oee']['mean']:.2%} ± {ci['oee']['std']:.2%}")
print(f"95% CI: [{ci['oee']['lower']:.2%}, {ci['oee']['upper']:.2%}]")
```

### Financial Impact Calculation

```python
from twin.cost_impact_calculator import CostImpactCalculator

calculator = CostImpactCalculator(runner)

# Calculate ROI for improvements
roi_summary = calculator.calculate_roi(
    baseline_run_id="baseline-001",
    improved_run_id="optimized-001",
    n_simulations=10000
)

print(f"Implementation Cost: ${roi_summary['implementation_cost']:,}")
print(f"Weekly Savings: ${roi_summary['weekly_savings']['mean']:,}")
print(f"Payback Period: {roi_summary['payback_weeks']['mean']:.1f} weeks")
print(f"NPV: ${roi_summary['npv']['mean']:,}")
print(f"Probability of Positive NPV: {roi_summary['npv']['probability_positive']:.1%}")
```

## GraphQL API Usage

### Starting the API Server

```bash
# Start FastAPI with GraphQL endpoint
uvicorn api.main:app --reload --port 8000

# GraphiQL IDE available at http://localhost:8000/graphql
```

### Query Examples

#### Get Current Status
```graphql
query CurrentStatus {
  healthCheck
  getSyncHealth {
    equipmentId
    health
    lastUpdate
    alerts
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
    kpiSummary {
      meanOee
      meanAvailability
      meanPerformance
      meanQuality
    }
    optimizationResult {
      paretoFront
      bestConfigurations
    }
  }
}
```

#### Update Parameters
```graphql
mutation UpdateConfig {
  updateParameters(changes: {
    micro_stop_probability: 0.03,
    performance_factor: 0.90
  }) {
    parameterName
    oldValue
    newValue
    impactEstimate
  }
}
```

### Real-Time Subscriptions

```python
import asyncio
from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport

async def subscribe_to_progress():
    transport = WebsocketsTransport(url='ws://localhost:8000/graphql')
    
    async with Client(transport=transport) as session:
        subscription = gql('''
            subscription SimulationProgress($runId: String!) {
              simulationProgress(runId: $runId) {
                runId
                status
                progressPercentage
                currentStep
                kpiSnapshot {
                  oee
                  availability
                }
              }
            }
        ''')
        
        async for result in session.subscribe(
            subscription, 
            variable_values={"runId": "opt-run-123"}
        ):
            print(f"Progress: {result['simulationProgress']['progressPercentage']}%")
```

## Visualization Tools

### Creating Interactive Charts

#### Pareto Front Visualization
```python
from twin.visualization import create_pareto_plot

# Generate Pareto front plot
fig = create_pareto_plot(
    run_ids=["opt-001", "opt-002", "opt-003"],
    objectives=["oee", "energy"]
)

# Display in browser
fig.show()

# Save to file
fig.write_html("pareto_analysis.html")
fig.write_image("pareto_analysis.png")
```

#### Time Series Analysis
```python
from twin.visualization import plot_kpi_trends

# Create KPI trend visualization
fig = plot_kpi_trends(
    run_ids=["baseline", "scenario1", "scenario2"],
    kpis=["oee", "availability", "performance", "quality"]
)

# Add annotations for important events
fig.add_annotation(
    x="2024-01-15 10:00",
    y=0.65,
    text="Parameter change applied",
    showarrow=True
)

fig.show()
```

#### Sensitivity Heatmap
```python
from twin.visualization import create_sensitivity_heatmap

# Analyze parameter sensitivity
fig = create_sensitivity_heatmap(
    run_ids=["baseline", "test1", "test2", "test3"]
)

# Identify high-impact parameters
fig.show()
```

#### Financial Analysis
```python
from twin.visualization import plot_roi_distribution

# Visualize ROI with confidence intervals
fig = plot_roi_distribution(roi_summary)

# Export for presentation
fig.write_html("roi_analysis.html", include_plotlyjs='cdn')
```

### Embedding Visualizations

```html
<!-- Embed in web application -->
<div id="pareto-chart"></div>
<script>
  fetch('/api/graphql', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      query: `
        query {
          visualization {
            generateParetoPlot(
              runIds: ["opt-001"],
              objectives: ["oee", "energy"]
            ) {
              plotJson
            }
          }
        }
      `
    })
  })
  .then(res => res.json())
  .then(data => {
    const plotData = JSON.parse(data.data.visualization.generateParetoPlot.plotJson);
    Plotly.newPlot('pareto-chart', plotData.data, plotData.layout);
  });
</script>
```

## Advanced Scenarios

### Scenario 1: Complete Optimization Workflow

```python
# 1. Establish baseline
baseline = runner.run_simulation(
    run_type=RunType.BASELINE,
    duration=168  # One week
)

# 2. Run optimization
optimizer = OptimizationEngine()
optimization_result = optimizer.optimize(
    objectives=["maximize:oee", "minimize:energy_consumption"],
    constraints=["quality >= 0.95"],
    baseline_id=baseline['run_id']
)

# 3. Select best configuration
best_config = optimization_result['best_configuration']

# 4. Validate with Monte Carlo
validation = runner.run_simulation(
    run_type=RunType.MONTE_CARLO,
    config=best_config,
    n_simulations=1000
)

# 5. Calculate financial impact
roi = calculator.calculate_roi(
    baseline_run_id=baseline['run_id'],
    improved_run_id=validation['run_id']
)

# 6. Generate recommendation
from twin.recommendation_engine import RecommendationEngine
recommender = RecommendationEngine()
recommendation = recommender.generate_recommendation(
    scenario="optimization_complete",
    data={
        'baseline': baseline,
        'optimized': validation,
        'roi': roi
    }
)

print(recommendation['summary'])
print(recommendation['action_items'])
```

### Scenario 2: Real-Time Monitoring with Alerts

```python
import asyncio
from twin.sync_monitor import SyncMonitor

async def monitor_with_alerts():
    monitor = SyncMonitor(twin)
    
    # Define alert conditions
    alerts = [
        {"metric": "oee", "threshold": 0.6, "condition": "below"},
        {"metric": "quality", "threshold": 0.95, "condition": "below"},
        {"metric": "energy", "threshold": 1000, "condition": "above"}
    ]
    
    # Monitor continuously
    while True:
        health_reports = monitor.get_health_reports()
        
        for report in health_reports:
            for alert in alerts:
                value = report.metrics.get(alert['metric'])
                
                if alert['condition'] == 'below' and value < alert['threshold']:
                    print(f"🚨 ALERT: {alert['metric']} is {value:.2f} (below {alert['threshold']})")
                    # Trigger automated response
                    await trigger_response(alert['metric'], value)
                
                elif alert['condition'] == 'above' and value > alert['threshold']:
                    print(f"🚨 ALERT: {alert['metric']} is {value:.2f} (above {alert['threshold']})")
                    await trigger_response(alert['metric'], value)
        
        await asyncio.sleep(60)  # Check every minute

async def trigger_response(metric, value):
    # Automated response logic
    if metric == "oee" and value < 0.6:
        # Run root cause analysis
        nlp = NaturalLanguageProcessor()
        response = nlp.process_query(f"Why is OEE at {value:.2%}?", twin)
        print(f"Root cause: {response['analysis']}")
        
        # Generate recommendations
        recommender = RecommendationEngine()
        actions = recommender.quick_wins(metric, value)
        print(f"Recommended actions: {actions}")
```

### Scenario 3: Comparative Analysis

```python
def compare_scenarios(scenarios):
    """Compare multiple what-if scenarios"""
    
    results = []
    
    for scenario in scenarios:
        # Run simulation for each scenario
        result = runner.run_simulation(
            run_type=RunType.SCENARIO,
            duration=168,
            config=scenario['config'],
            scenario_name=scenario['name']
        )
        
        # Calculate financial impact
        roi = calculator.calculate_roi(
            baseline_run_id="baseline-001",
            improved_run_id=result['run_id']
        )
        
        results.append({
            'name': scenario['name'],
            'kpis': result['kpi_summary'],
            'roi': roi,
            'config': scenario['config']
        })
    
    # Generate comparison visualization
    from twin.visualization import create_comparison_dashboard
    fig = create_comparison_dashboard(results)
    fig.show()
    
    # Rank scenarios
    ranked = sorted(results, 
                   key=lambda x: x['roi']['npv']['mean'], 
                   reverse=True)
    
    print("\nScenario Rankings by NPV:")
    for i, scenario in enumerate(ranked, 1):
        print(f"{i}. {scenario['name']}: NPV=${scenario['roi']['npv']['mean']:,.0f}")
    
    return ranked

# Define scenarios to compare
scenarios = [
    {
        'name': 'Reduce Micro Stops',
        'config': {'micro_stop_probability': 0.02}
    },
    {
        'name': 'Improve Performance',
        'config': {'performance_factor': 0.95}
    },
    {
        'name': 'Combined Improvement',
        'config': {
            'micro_stop_probability': 0.03,
            'performance_factor': 0.90
        }
    }
]

best_scenario = compare_scenarios(scenarios)
```

### Scenario 4: Automated Optimization Loop

```python
async def automated_optimization_loop():
    """Continuously optimize based on real-time data"""
    
    while True:
        # 1. Collect recent performance data
        recent_kpis = twin.get_recent_kpis(hours=24)
        
        # 2. Check if optimization is needed
        if recent_kpis['mean_oee'] < 0.65:
            print("Performance below target, initiating optimization...")
            
            # 3. Run quick optimization
            optimizer = OptimizationEngine()
            result = optimizer.quick_optimize(
                current_kpis=recent_kpis,
                target_oee=0.70,
                max_time=60  # 60 second time limit
            )
            
            # 4. Validate improvement
            if result['expected_improvement'] > 0.05:
                print(f"Found improvement: +{result['expected_improvement']:.1%} OEE")
                
                # 5. Apply changes gradually
                params = ActionableParameters()
                for param, value in result['new_config'].items():
                    current = params.get_parameter(param)
                    # Apply 50% of change initially
                    new_value = current + 0.5 * (value - current)
                    params.set_parameter(param, new_value)
                
                twin.apply_parameters(params)
                print("Configuration updated (50% change applied)")
                
                # 6. Monitor for 1 hour
                await asyncio.sleep(3600)
                
                # 7. Check results
                new_kpis = twin.get_recent_kpis(hours=1)
                if new_kpis['mean_oee'] > recent_kpis['mean_oee']:
                    print("Improvement confirmed, applying full change")
                    for param, value in result['new_config'].items():
                        params.set_parameter(param, value)
                    twin.apply_parameters(params)
                else:
                    print("No improvement detected, reverting changes")
                    twin.revert_parameters()
        
        # Wait before next optimization check
        await asyncio.sleep(3600)  # Check hourly
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues
```python
# Check database exists
import os
if not os.path.exists("data/mes_database.db"):
    print("Database not found. Initializing...")
    from scripts.init_database import initialize_database
    initialize_database()
```

#### 2. Simulation Performance
```python
# Profile simulation performance
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run simulation
result = runner.run_simulation(run_type=RunType.BASELINE)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 time-consuming functions
```

#### 3. Memory Management
```python
# Clear old simulation data
from twin.utils import cleanup_old_runs

# Remove runs older than 30 days
cleanup_old_runs(days=30)

# Compact database
import sqlite3
conn = sqlite3.connect("data/mes_database.db")
conn.execute("VACUUM")
conn.close()
```

#### 4. GraphQL Debugging
```python
# Enable GraphQL introspection and debugging
from api.graphql.schema import schema

# Get schema structure
introspection = schema.introspect()
print(json.dumps(introspection, indent=2))

# Test query execution
test_query = """
query TestQuery {
  healthCheck
}
"""

result = asyncio.run(schema.execute(test_query))
if result.errors:
    for error in result.errors:
        print(f"Error: {error}")
```

### Performance Optimization Tips

1. **Batch Operations**
```python
# Bad: Individual operations
for i in range(100):
    runner.run_simulation(...)

# Good: Batch processing
runner.run_batch_simulations(configs=[...], parallel=True)
```

2. **Caching Results**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_kpis(run_id):
    return runner.get_kpi_summary(run_id)
```

3. **Async Operations**
```python
# Use async for I/O operations
async def process_multiple_queries(queries):
    tasks = [process_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

### Logging and Debugging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twin.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('virtual_twin')

# Use in code
logger.info(f"Starting simulation: {run_id}")
logger.warning(f"Parameter out of range: {param}={value}")
logger.error(f"Simulation failed: {error}")
```

## Best Practices

### 1. Parameter Management
- Always validate parameters before applying
- Use gradual changes for production systems
- Keep audit trail of all changes

### 2. Simulation Guidelines
- Run baseline before optimization
- Use Monte Carlo for uncertainty
- Validate results with historical data

### 3. API Usage
- Use GraphQL fragments for reusable queries
- Implement proper error handling
- Rate limit API calls in production

### 4. Visualization
- Choose appropriate chart types
- Include confidence intervals
- Export for offline viewing

### 5. Production Deployment
- Use environment variables for configuration
- Implement health checks
- Set up monitoring and alerting
- Regular database maintenance

## Support and Resources

### Documentation
- API Reference: `/docs/API_REFERENCE.md`
- GraphQL Schema: `/api/graphql/schema.graphql`
- ISO 23247 Compliance: `/docs/TWIN_PROOF.md`

### Examples
- Demo Scenarios: `/twin/demo_scenarios.py`
- Test Cases: `/tests/`
- Notebooks: `/notebooks/` (if available)

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Share use cases and best practices
- Wiki: Additional guides and tutorials

---

*For additional help, consult the project documentation or raise an issue in the repository.*