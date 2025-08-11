# MOO and MC Implementation Plan for Virtual Twin

## Overview
This document outlines the areas in the Twin module that need enhancement for Multi-Objective Optimization (MOO) using pymoo and robust Monte Carlo (MC) analysis using recommended statistical libraries.

## 1. Multi-Objective Optimization (MOO) Areas

### Primary: `recommendation_engine.py`
**Current State:**
- Custom NSGA-II implementation (lines 57-129)
- Basic non-dominated sorting without proven correctness
- No visualization of Pareto fronts
- Limited constraint handling
- Missing hypervolume metrics
- Uses approximation instead of actual simulation (line 195)

**Required Enhancements:**
- Replace custom NSGA-II with pymoo implementation
- Add Pareto front visualization
- Implement proper constraint handling
- Add performance indicators (hypervolume, IGD)
- Connect to actual simulation runner

### Secondary: `optimization_engine.py`
**Current State:**
- scipy differential evolution (single/weighted multi-objective)
- Not true multi-objective (uses weighted sum)

**Role After Enhancement:**
- Keep for single-objective problems
- Complement pymoo for specific use cases
- Fast feasibility checks

## 2. Monte Carlo (MC) Analysis Areas

### Primary: `cost_impact_calculator.py`
**Current Implementation (lines 54-195):**
- Basic MC simulation with `np.random`
- Simple uncertainty addition (lines 92-94)
- Limited distribution types
- Basic confidence intervals using percentiles

**Gaps to Address:**
- No proper statistical distributions (should use scipy.stats)
- Missing error propagation
- No sensitivity analysis
- Limited uncertainty quantification
- No correlation between parameters

**Required Enhancements:**
- Implement scipy.stats distributions (normal, lognormal, beta, triangular)
- Add uncertainties library for error propagation
- Implement proper confidence intervals using t-distribution
- Add bootstrap confidence intervals
- Include kernel density estimates
- Report percentiles (P5, P50, P95)

### Secondary: `simulation_runner.py`
**Current State:**
- Mentions MC support (line 113) but not implemented

**Required Enhancements:**
- Add MC wrapper for parameter uncertainty in simulations
- Implement batch simulation with different seeds
- Add uncertainty propagation through simulation pipeline

### Tertiary: `recommendation_engine.py`
**Current State:**
- No confidence intervals for Pareto solutions

**Required Enhancements:**
- MC validation of optimization results
- Confidence bounds on Pareto front
- Robustness analysis of solutions

## 3. Specific Implementation Details

### pymoo Integration (recommendation_engine.py)

```python
# Replace lines 57-129 with:
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.operators.sampling.lhs import LHS
from pymoo.optimize import minimize
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD

class ManufacturingOptimization(Problem):
    """Multi-objective problem for pymoo"""
    def __init__(self, simulation_runner):
        super().__init__(
            n_var=5,  # 5 actionable parameters
            n_obj=3,  # OEE, Cost, Energy
            n_constr=2,  # Quality >= 95%, Throughput >= baseline * 0.9
            xl=[0.05, 0.50, 1.0, 0.50, 0.0],  # Lower bounds
            xu=[0.50, 1.00, 5.0, 1.00, 1.0]   # Upper bounds
        )
        self.runner = simulation_runner
    
    def _evaluate(self, x, out, *args, **kwargs):
        # Run actual simulations
        # Calculate objectives and constraints
        pass
```

### Robust MC Implementation (cost_impact_calculator.py)

```python
# Enhance lines 86-195 with:
import scipy.stats as stats
from scipy.stats import norm, lognorm, beta, triang
import uncertainties as unc
from uncertainties import unumpy

def calculate_probabilistic_roi(self, n_simulations=10000):
    """
    Monte Carlo ROI with proper uncertainty quantification
    """
    # Define distributions for uncertain parameters
    oee_improvement = stats.norm(loc=0.15, scale=0.03)  # 15% ± 3%
    implementation_cost = stats.lognorm(s=0.2, loc=25000, scale=5000)
    weekly_savings = stats.beta(a=2, b=5, loc=30000, scale=20000)
    
    # Run MC simulation with proper statistics
    # Calculate confidence intervals using t-distribution
    # Add bootstrap for robustness
    pass
```

## 4. Required Libraries

### For MOO:
```bash
pip install pymoo  # Multi-objective optimization
```

### For MC:
```bash
pip install scipy  # Already available, use scipy.stats
pip install uncertainties  # Error propagation
pip install SALib  # Optional: Sensitivity analysis
```

## 5. Implementation Priority

### High Priority (Week 1)
1. **pymoo NSGA-II in recommendation_engine.py**
   - Replace custom implementation
   - Add basic Pareto visualization
   - Connect to actual simulation

2. **scipy.stats in cost_impact_calculator.py**
   - Implement proper distributions
   - Add confidence intervals with t-distribution
   - Include percentile reporting

### Medium Priority (Week 2)
1. **uncertainties library in cost_impact_calculator.py**
   - Error propagation
   - Correlated uncertainties
   
2. **MC wrapper in simulation_runner.py**
   - Batch simulations with uncertainty
   - Parameter sensitivity

### Low Priority (Week 3)
1. **SALib integration**
   - Sobol sensitivity indices
   - Morris screening
   
2. **Advanced features**
   - Correlation modeling
   - Robust optimization
   - Progressive hedging

## 6. Testing Strategy

### MOO Testing:
- Validate against known test problems (ZDT, DTLZ)
- Compare with original implementation
- Verify Pareto dominance
- Check constraint satisfaction

### MC Testing:
- Validate distributions with K-S tests
- Check convergence with different n_simulations
- Verify confidence interval coverage
- Compare with analytical solutions where possible

## 7. Success Criteria

### MOO Success:
- ✅ Pareto front generation in <30 seconds
- ✅ Hypervolume indicator calculation
- ✅ Constraint satisfaction >95%
- ✅ Reproducible results with same seed

### MC Success:
- ✅ Confidence intervals with proper coverage (95%)
- ✅ Convergence with n=10,000 simulations
- ✅ Results formatted as "Value ± Uncertainty (CI: lower-upper)"
- ✅ Sensitivity analysis identifying key parameters

## 8. Example Outputs

### MOO Output:
```
Pareto Front Solutions:
1. OEE: 82%, Energy: 1200 kWh, Cost: $45K
2. OEE: 78%, Energy: 900 kWh, Cost: $38K
3. OEE: 75%, Energy: 750 kWh, Cost: $35K
Hypervolume: 0.743
```

### MC Output:
```
ROI Analysis (10,000 simulations):
Weekly Savings: $45,000 ± $5,000 (95% CI: $38,000-$52,000)
Payback Period: 3.2 ± 0.5 weeks (P5: 2.4, P50: 3.1, P95: 4.3)
3-Year NPV: $2.31M ± $0.28M (95% CI: $1.85M-$2.78M)
Probability of Positive NPV: 98.7%
```

## 9. File Impact Summary

| File | MOO Changes | MC Changes | Priority |
|------|------------|------------|----------|
| `recommendation_engine.py` | Major: pymoo integration | Minor: confidence bounds | High |
| `cost_impact_calculator.py` | None | Major: scipy.stats, uncertainties | High |
| `simulation_runner.py` | None | Medium: MC wrapper | Medium |
| `optimization_engine.py` | Minor: keep as-is | None | Low |
| `twin/__init__.py` | Update imports | Update imports | High |

## 10. Next Steps

1. Install required libraries (pymoo, uncertainties)
2. Create feature branch for MOO/MC enhancements
3. Implement pymoo in recommendation_engine.py
4. Enhance MC in cost_impact_calculator.py
5. Add comprehensive tests
6. Update documentation
7. Validate against success metrics