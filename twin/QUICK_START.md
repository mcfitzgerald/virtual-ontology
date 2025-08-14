# Virtual Twin Quick Start Guide

This guide provides working examples to get you started with the Virtual Twin module quickly.

## Installation & Setup

```bash
# Ensure you're in the virtual-ontology directory
cd /Users/michael/github/virtual-ontology

# Activate the virtual environment
source ~/.venvs/ont/bin/activate

# Start the API server
./api.sh start
```

## Important Notes

⚠️ **KPI Values**: All KPIs (OEE, availability, performance, quality) are returned as **percentages (0-100)**, not fractions (0-1).

⚠️ **SimulationRun Access**: Use `result.kpi_summary` to access KPI values, not `result.kpis` or `result['kpi_summary']`.

## Basic Examples

### 1. Simple What-If Simulation

```python
import sys
sys.path.insert(0, '/Users/michael/github/virtual-ontology')

from twin import SimulationRunner, ActionableParameters

# Initialize runner (set verbose=False for quiet operation)
runner = SimulationRunner(verbose=False)

# Create parameters and modify one
params = ActionableParameters()
params.set_value("micro_stop_probability", 0.05)  # Reduce from 0.1 to 0.05

# Run simulation
result = runner.run_simulation(params, duration_days=7, notes="Testing 50% reduction in micro-stops")

# Access results - KPIs are percentages (0-100)
print(f"Mean OEE: {result.kpi_summary['mean_oee']:.1f}%")
print(f"Downtime: {result.kpi_summary['downtime_percentage']:.1f}%")
print(f"Total Good Units: {result.kpi_summary['total_good_units']:,}")
```

### 2. Create and Compare to Baseline

```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)

# Create baseline with default parameters
baseline = runner.create_baseline(duration_days=7)
print(f"Baseline OEE: {baseline.kpi_summary['mean_oee']:.1f}%")

# Create improved scenario
params = ActionableParameters()
params.set_value("performance_factor", 0.95)  # Improve from 0.85 to 0.95
params.set_value("scrap_multiplier", 0.8)     # Reduce scrap by 20%

improved = runner.run_simulation(params, parent_run_id=baseline.run_id, duration_days=7)

# Calculate improvements
oee_improvement = improved.kpi_summary['mean_oee'] - baseline.kpi_summary['mean_oee']
print(f"OEE Improvement: {oee_improvement:.1f} percentage points")
```

### 3. Multi-Objective Optimization

```python
from twin import RecommendationEngine

engine = RecommendationEngine()

# Get recommendations for a specific scenario
result = engine.recommend_for_scenario("maximize_oee")

# Check if we got valid recommendations
if result and 'recommended_parameters' in result:
    print("Recommended Parameter Changes:")
    for param, value in result['recommended_parameters'].items():
        print(f"  {param}: {value:.3f}")
    
    if 'expected_improvements' in result:
        imp = result['expected_improvements']
        print(f"\nExpected OEE Improvement: {imp.get('oee_improvement', 0)*100:.1f}%")
```

### 4. Monte Carlo Uncertainty Analysis

```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)
params = ActionableParameters()

# Define uncertainty ranges (as deltas from base value)
uncertainty = {
    "micro_stop_probability": (-0.02, 0.02),  # ±2% variation
    "performance_factor": (-0.05, 0.05),      # ±5% variation
}

# Run Monte Carlo simulation
mc_results = runner.run_monte_carlo_simulation(
    parameters=params,
    uncertainty_ranges=uncertainty,
    n_simulations=20,  # Use more for production (50-100)
    duration_days=7
)

# Display results
print(f"Successful runs: {mc_results['n_successful']}/{mc_results['n_successful'] + mc_results['n_failed']}")
print(f"Mean OEE: {mc_results['statistics']['mean_oee_mean']:.1f}%")
print(f"OEE Std Dev: {mc_results['statistics']['mean_oee_std']:.1f}%")
print(f"95% CI: {mc_results['confidence_intervals']['mean_oee']}")
```

### 5. Financial Impact Analysis

```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)

# Run baseline
baseline = runner.create_baseline(duration_days=7)

# Run improved scenario
params = ActionableParameters()
params.set_value("micro_stop_probability", 0.07)  # 30% reduction
improved = runner.run_simulation(params, duration_days=7)

# Calculate financial impact
daily_revenue = 498279.25  # From your production data
oee_improvement = improved.kpi_summary['mean_oee'] - baseline.kpi_summary['mean_oee']

# Calculate revenue impact
weekly_impact = daily_revenue * 7 * (oee_improvement / 100)
annual_impact = weekly_impact * 52

print(f"OEE Improvement: {oee_improvement:.1f} percentage points")
print(f"Weekly Revenue Impact: ${weekly_impact:,.0f}")
print(f"Annual Revenue Impact: ${annual_impact:,.0f}")

# ROI calculation
implementation_cost = 100000  # Example cost
roi = (annual_impact / implementation_cost) * 100
print(f"ROI: {roi:.0f}%")
```

## Common Patterns

### Accessing Simulation Results

```python
# CORRECT - Access kpi_summary as an attribute
oee = result.kpi_summary['mean_oee']

# WRONG - These will cause errors
# oee = result['mean_oee']           # SimulationRun is not subscriptable
# oee = result.kpis['mean_oee']      # No 'kpis' attribute
# oee = result['kpi_summary']['mean_oee']  # SimulationRun is not subscriptable
```

### Understanding KPI Values

```python
# KPIs are returned as percentages (0-100)
print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")  # e.g., 65.3%

# To use as a fraction for calculations
oee_fraction = result.kpi_summary['mean_oee'] / 100  # Convert to 0.653
```

### Parameter Bounds

```python
from twin import ActionableParameters

params = ActionableParameters()

# View all parameters and their bounds
params.describe()

# Each parameter has specific bounds:
# - micro_stop_probability: 0.0 to 1.0
# - performance_factor: 0.5 to 1.0
# - scrap_multiplier: 0.5 to 2.0
# - material_reliability: 0.5 to 1.0
# - cascade_sensitivity: 0.0 to 1.0
```

## Troubleshooting

### Issue: "SimulationRun object is not subscriptable"

**Problem**: Trying to access SimulationRun like a dictionary.

**Solution**: Use attribute access:
```python
# Wrong
oee = result['kpi_summary']['mean_oee']

# Correct
oee = result.kpi_summary['mean_oee']
```

### Issue: OEE values seem wrong (>100% or very high)

**Problem**: Misunderstanding that KPIs are already percentages.

**Solution**: Remember KPIs are 0-100, not 0-1:
```python
# If you see OEE of 65.3, it means 65.3%, not 6530%
oee_percentage = result.kpi_summary['mean_oee']  # This is already 65.3 for 65.3%
```

### Issue: RecommendationEngine returns 0% improvements

**Problem**: The optimization may not be finding better solutions than baseline.

**Solution**: 
1. Check that you're using a scenario that maps to objectives
2. Try different scenarios or parameter ranges
3. Increase population_size and generations for optimization

### Issue: Import errors

**Problem**: Module not in Python path.

**Solution**: Always set the path:
```python
import sys
sys.path.insert(0, '/Users/michael/github/virtual-ontology')
```

Or set environment variable:
```bash
export PYTHONPATH=/Users/michael/github/virtual-ontology:$PYTHONPATH
```

## Next Steps

1. Review the full API documentation in `twin/API.md`
2. Check example scripts in `twin/examples/`
3. Read about advanced features in `twin/README.md`
4. Explore the system prompt in `SYSTEM_PROMPT.md` for Claude Code integration