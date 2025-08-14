# Virtual Twin Patterns Reference
<!-- Quick reference for error-free script generation -->

## 🔴 CRITICAL: Always Start With This

```python
# REQUIRED: Environment setup (choose one)
# Option A: Activate virtual environment first in bash
# source ~/.venvs/ont/bin/activate

# Option B: Add to Python path in script
import sys
sys.path.insert(0, '/Users/michael/github/virtual-ontology')

# REQUIRED: Core imports
from typing import Dict, List, Optional, Tuple, Any
from twin import SimulationRunner, ActionableParameters
```

## ⚠️ TOP 3 GOTCHAS (Prevent 90% of Errors)

### 1. KPI Access Pattern
```python
# ❌ WRONG - These cause AttributeError
oee = result['kpi_summary']['mean_oee']  # SimulationRun not subscriptable
oee = result.kpis['mean_oee']            # No 'kpis' attribute

# ✅ CORRECT - Use attribute access
oee = result.kpi_summary['mean_oee']     # Returns 65.3 (percentage)
```

### 2. KPI Values Are Percentages
```python
# ❌ WRONG - Treating as fraction
impact = oee * revenue  # If oee=65.3, this multiplies by 65.3!

# ✅ CORRECT - Convert to fraction when needed
oee_fraction = result.kpi_summary['mean_oee'] / 100  # 0.653
impact = oee_fraction * revenue
```

### 3. Verbose Control
```python
# ✅ ALWAYS set verbose=False for cleaner output
runner = SimulationRunner(verbose=False)
```

## 📋 Core Patterns (Copy & Paste Ready)

### Pattern 1: Simple What-If Simulation
```python
import sys
sys.path.insert(0, '/Users/michael/github/virtual-ontology')
from twin import SimulationRunner, ActionableParameters

# Setup
runner = SimulationRunner(verbose=False)
params = ActionableParameters()

# Modify ONE parameter (see bounds below)
params.set_value("micro_stop_probability", 0.05)  # Reduce from 0.1 to 0.05

# Run simulation
result = runner.run_simulation(
    parameters=params,
    duration_days=7,
    notes="Testing 50% reduction in micro-stops"
)

# Access results (KPIs are percentages 0-100)
print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")
print(f"Downtime: {result.kpi_summary['downtime_percentage']:.1f}%")
```

### Pattern 2: Baseline Comparison
```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)

# Create baseline
baseline = runner.create_baseline(duration_days=7)
baseline_oee = baseline.kpi_summary['mean_oee']

# Run improved scenario
params = ActionableParameters()
params.set_value("performance_factor", 0.95)
params.set_value("scrap_multiplier", 0.8)

improved = runner.run_simulation(params, duration_days=7)
improved_oee = improved.kpi_summary['mean_oee']

# Calculate improvement (both are percentages)
improvement = improved_oee - baseline_oee
print(f"OEE Improvement: {improvement:.1f} percentage points")
```

### Pattern 3: AI Recommendations (Easiest)
```python
from twin import RecommendationEngine

engine = RecommendationEngine()

# Get AI-optimized recommendations
result = engine.recommend_for_scenario("maximize_oee")

if result and 'recommended_parameters' in result:
    for param, value in result['recommended_parameters'].items():
        print(f"{param}: {value:.3f}")
    
    if 'expected_improvements' in result:
        imp = result['expected_improvements']
        # Note: improvements are fractions (0.1 = 10% improvement)
        print(f"Expected OEE Improvement: {imp.get('oee_improvement', 0)*100:.1f}%")
```

### Pattern 4: Monte Carlo Uncertainty
```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)
params = ActionableParameters()

# Define uncertainty as DELTAS from base value
uncertainty = {
    "micro_stop_probability": (-0.02, 0.02),  # ±0.02 absolute
    "performance_factor": (-0.05, 0.05),      # ±0.05 absolute
}

# Run Monte Carlo (use 50-100 for production)
mc_results = runner.run_monte_carlo_simulation(
    parameters=params,
    uncertainty_ranges=uncertainty,
    n_simulations=20,
    duration_days=7
)

# Access aggregated results
print(f"Mean OEE: {mc_results['statistics']['mean_oee_mean']:.1f}%")
print(f"95% CI: {mc_results['confidence_intervals']['mean_oee']}")
```

### Pattern 5: Financial Impact
```python
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)

# Get baseline and improved
baseline = runner.create_baseline(duration_days=7)
params = ActionableParameters()
params.set_value("micro_stop_probability", 0.07)  # 30% reduction
improved = runner.run_simulation(params, duration_days=7)

# Calculate financial impact
daily_revenue = 498279.25  # Query from database first
oee_improvement = improved.kpi_summary['mean_oee'] - baseline.kpi_summary['mean_oee']

# Both OEEs are percentages, so divide by 100 for fraction
weekly_impact = daily_revenue * 7 * (oee_improvement / 100)
annual_impact = weekly_impact * 52

print(f"OEE: +{oee_improvement:.1f} points → ${annual_impact:,.0f}/year")
```

## 📊 Parameter Bounds Reference

| Parameter | Min | Max | Default | Meaning |
|-----------|-----|-----|---------|---------|
| `micro_stop_probability` | 0.0 | 1.0 | 0.10 | Lower = fewer stops |
| `performance_factor` | 0.5 | 1.0 | 0.85 | Higher = faster |
| `scrap_multiplier` | 0.5 | 2.0 | 1.00 | <1 = less scrap |
| `material_reliability` | 0.5 | 1.0 | 0.85 | Higher = better materials |
| `cascade_sensitivity` | 0.0 | 1.0 | 0.30 | Lower = less coupling |

## 🔍 Type Hints Quick Reference

```python
# Function signatures with proper types
def run_simulation(
    parameters: ActionableParameters,
    duration_days: int = 7,  # 1-30
    seed: Optional[int] = None,  # 0-10000
    parent_run_id: Optional[str] = None,
    notes: Optional[str] = None
) -> SimulationRun: ...

# Common return types
result: SimulationRun
result.kpi_summary: Dict[str, float]  # {'mean_oee': 65.3, ...}
result.run_id: str  # "sim-20240815-120000-abc123"

# RecommendationEngine returns
recommendation: Dict[str, Any] = {
    'recommended_parameters': Dict[str, float],
    'expected_improvements': Dict[str, float],  # Fractions!
    'confidence': float,
    'feasible': bool
}
```

## 🚨 Error Prevention Checklist

Before running any twin script:

- [ ] Environment activated or PYTHONPATH set?
- [ ] Using `verbose=False` for SimulationRunner?
- [ ] Accessing KPIs with `result.kpi_summary['key']`?
- [ ] Remember KPIs are percentages (0-100)?
- [ ] Parameters within bounds (see table)?
- [ ] Duration between 1-30 days?

## 📚 When You Need More

- **Full API**: See `twin/API.md`
- **Examples**: See `twin/QUICK_START.md`
- **Troubleshooting**: See `twin/docs/EXAMPLES.md`
- **Type definitions**: Check module docstrings

## 🎯 Decision Tree

```
User wants to...
├── Test specific change → Pattern 1 (Simple Simulation)
├── Compare scenarios → Pattern 2 (Baseline Comparison)
├── Get AI recommendations → Pattern 3 (RecommendationEngine)
├── Include uncertainty → Pattern 4 (Monte Carlo)
└── Calculate ROI → Pattern 5 (Financial Impact)
```

---
*Last updated: 2024-08-15 | Version: 1.0*