# Twin Model Optimization Guide

## Overview

This guide provides a comprehensive approach to optimizing production line performance using the Twin Model simulation framework. Based on the Theory of Constraints (TOC) and empirical industry data, it outlines a progressive path from poor baseline performance (45-50% OEE) to world-class operations (75-80% OEE).

## Theory of Constraints (TOC) Implementation

### The Five Focusing Steps

Based on Eliyahu Goldratt's methodology, optimization follows these steps:

1. **Identify the Constraint**
   - Look for equipment with highest utilization
   - Check for persistent input buffer starvation
   - Monitor output buffer blocking frequency
   - In most lines: The filler is the constraint

2. **Exploit the Constraint**
   - Ensure it never starves (maintain input buffer)
   - Ensure it never blocks (clear output quickly)
   - Minimize micro-stops and changeovers
   - Run at maximum quality rate

3. **Subordinate Everything Else**
   - All other equipment serves the constraint
   - Upstream: Generate faster than constraint consumes
   - Downstream: Process faster than constraint produces
   - Implement V-curve speed design

4. **Elevate the Constraint**
   - Increase constraint capacity if needed
   - Improve maintenance (reduce MTTR)
   - Enhance performance factor
   - Consider equipment upgrades

5. **Repeat the Process**
   - Constraint may shift after improvements
   - Continuously monitor and optimize
   - Document improvements for learning

### Constraint Identification Techniques

```python
# In your simulation analysis:
def identify_constraint(metrics):
    """Find the bottleneck in the production line."""
    constraints = []
    for equip_id, equip_metrics in metrics.items():
        if "FIL" in equip_id:  # Fillers are often constraints
            constraints.append({
                'equipment': equip_id,
                'utilization': equip_metrics.get('utilization', 0),
                'starved_time': equip_metrics.get('starved_time', 0),
                'blocked_time': equip_metrics.get('blocked_time', 0)
            })
    # Sort by utilization (highest = constraint)
    return sorted(constraints, key=lambda x: x['utilization'], reverse=True)[0]
```

## Progressive OEE Improvement Path

### Stage 1: Baseline Configuration (45-50% OEE)

**Current State**: Poor performance, no optimization

```yaml
# config/baseline_parameters.yaml
defaults:
  equipment:
    # Poor batch processing
    batch_size: 10.0
    processing_interval: 0.1
    
    # Poor reliability
    mtbf: 65.0
    mttr: 35.0
    
    # Poor performance
    performance_factor: 0.46
    quality_rate: 0.93
    
    # No accumulation
    internal_capacity: 100.0
```

**Metrics**:
- Availability: 65% (MTBF 65 / (MTBF 65 + MTTR 35))
- Performance: 46%
- Quality: 93%
- **OEE: 27.8%** (0.65 × 0.46 × 0.93)

### Stage 2: Add Accumulation (55-60% OEE)

**Quick Win**: Add buffers to decouple equipment

```yaml
# config/stage2_accumulation.yaml
defaults:
  equipment:
    # Increase internal buffers
    internal_capacity: 1000.0  # Was 100.0
    
    # Add pre/post constraint buffers
    buffer_before_constraint: 500.0  # 5 minutes production
    buffer_after_constraint: 300.0   # 3 minutes production
```

**Impact**:
- Reduces blocking/starvation
- Smooths flow variations
- **OEE: 55-60%** improvement

### Stage 3: Improve Maintenance (65-70% OEE)

**Focus**: Reduce downtime through better maintenance

```yaml
# config/stage3_maintenance.yaml
defaults:
  equipment:
    # Improved maintenance response
    mtbf: 120.0  # Was 65.0 (better preventive maintenance)
    mttr: 15.0   # Was 35.0 (faster repairs)
    
    # Reduced micro-stops
    micro_stop_rate: 3.0  # Was 5.0 per hour
    micro_stop_duration: 15.0  # Was 30.0 seconds
```

**Metrics**:
- Availability: 89% (MTBF 120 / (MTBF 120 + MTTR 15))
- Performance: 60% (reduced micro-stops)
- Quality: 93%
- **OEE: 65-70%**

### Stage 4: Optimize Performance (70-75% OEE)

**Focus**: Improve speed and reduce losses

```yaml
# config/stage4_performance.yaml
defaults:
  equipment:
    # Fix batch processing bottleneck
    batch_size: 100.0  # Was 10.0 (10x improvement)
    processing_interval: 0.1
    
    # Improve performance factor
    performance_factor: 0.75  # Was 0.46
    
    # Implement V-curve speeds
    # (See V-curve configuration below)
```

**Metrics**:
- Availability: 89%
- Performance: 75%
- Quality: 93%
- **OEE: 70-75%**

### Stage 5: World-Class Operations (75-80% OEE)

**Focus**: Quality improvements and advanced optimization

```yaml
# config/stage5_worldclass.yaml
defaults:
  equipment:
    # Excellence in all areas
    mtbf: 180.0
    mttr: 10.0
    
    performance_factor: 0.85
    quality_rate: 0.98  # Was 0.93
    
    # Minimal micro-stops
    micro_stop_rate: 1.0
    micro_stop_duration: 10.0
```

**Metrics**:
- Availability: 95% (MTBF 180 / (MTBF 180 + MTTR 10))
- Performance: 85%
- Quality: 98%
- **OEE: 79%** (World-class)

## Parameter Tuning Guidelines

### Critical Parameters Impact Matrix

| Parameter | Impact on OEE | Effort to Improve | Priority |
|-----------|--------------|-------------------|----------|
| batch_size | Very High | Low | 1 |
| processing_interval | Very High | Low | 1 |
| mttr | High | Medium | 2 |
| performance_factor | High | Medium | 2 |
| quality_rate | Medium | High | 3 |
| mtbf | Medium | High | 4 |
| micro_stops | Low | Low | 5 |

### V-Curve Configuration

Implement speed differentials based on constraint:

```yaml
# For 100 units/min constraint (LINE 1)
equipment_parameters:
  LINE1-SOURCE:
    generation_rate: 120.0    # +20% push
  LINE1-FIL:
    nominal_rate: 100.0       # Constraint
  LINE1-PCK:
    nominal_rate: 110.0       # +10% pull
  LINE1-PAL:
    nominal_rate: 130.0       # +30% pull
  LINE1-SINK:
    collection_rate: 130.0    # Match fastest
```

### Changeover Optimization

Minimize changeover impact through sequencing:

```yaml
changeover_matrix:
  # Group similar products
  same_family: 5         # Minutes
  different_family: 15
  allergen_change: 45
  
campaign_parameters:
  min_campaign_size: 50  # Units
  group_by_family: true
  group_by_allergen: true
```

## Bottleneck Exploitation Strategies

### 1. Protect the Constraint
- Maintain 5-minute buffer before constraint
- Never let constraint starve for material
- Use quality checks before constraint (not after)

### 2. Optimize Constraint Operations
- Minimize changeovers at constraint
- Run longest campaigns at constraint
- Perform maintenance during planned downtime

### 3. Offload Non-Essential Work
- Move quality checks upstream when possible
- Perform rework offline
- Use parallel processing where feasible

## Monitoring and Metrics

### Key Performance Indicators (KPIs)

```python
# Essential metrics to track
kpis = {
    'oee': {
        'target': 0.75,
        'components': ['availability', 'performance', 'quality']
    },
    'constraint_utilization': {
        'target': 0.95,
        'measure': 'productive_time / available_time'
    },
    'throughput': {
        'target': 'nominal_rate * oee',
        'units': 'units/minute'
    },
    'first_pass_yield': {
        'target': 0.98,
        'measure': 'good_units / total_units'
    }
}
```

### Continuous Improvement Process

1. **Baseline Measurement**
   - Run simulation for 14 days
   - Document current OEE components
   - Identify primary losses

2. **Implement Changes**
   - Apply one improvement at a time
   - Run simulation to measure impact
   - Document results

3. **Validate Improvements**
   - Compare before/after metrics
   - Calculate ROI
   - Update standard configurations

4. **Standardize Success**
   - Update default parameters
   - Document best practices
   - Train on new procedures

## Implementation Checklist

### Phase 1: Quick Wins (Week 1)
- [ ] Fix batch_size to 100 units
- [ ] Adjust processing_interval if needed
- [ ] Implement V-curve speeds
- [ ] Add basic accumulation buffers

### Phase 2: Reliability (Week 2)
- [ ] Reduce MTTR through training
- [ ] Implement preventive maintenance (increase MTBF)
- [ ] Reduce micro-stop frequency
- [ ] Optimize changeover procedures

### Phase 3: Performance (Week 3)
- [ ] Increase performance factors
- [ ] Optimize production scheduling
- [ ] Implement campaign batching
- [ ] Fine-tune buffer sizes

### Phase 4: Quality (Week 4)
- [ ] Improve quality rates
- [ ] Implement quality-at-source
- [ ] Reduce rework and scrap
- [ ] Optimize inspection points

## Expected Results

Following this optimization guide, expect:

| Stage | OEE Range | Production (14 days) | Improvement |
|-------|-----------|---------------------|-------------|
| Baseline | 45-50% | 2.5-3M units | - |
| + Accumulation | 55-60% | 3-3.5M units | +20% |
| + Maintenance | 65-70% | 3.5-4M units | +40% |
| + Performance | 70-75% | 4-4.5M units | +60% |
| World-Class | 75-80% | 4.5-5M units | +80% |

## References

- [Theory of Constraints](reference/theory_notes.md) - Detailed TOC implementation
- [Implementation Plan](../IMPLEMENTATION_PLAN.md) - Step-by-step roadmap
- [Configuration Reference](llm-ready/05-configuration-reference.md) - Parameter details
- Goldratt, E.M. (1984). "The Goal: A Process of Ongoing Improvement"

## Next Steps

1. Start with Stage 1 baseline measurement
2. Implement quick wins (batch_size, V-curve)
3. Progress through stages systematically
4. Document improvements for future reference
5. Share results for continuous learning

---

*For technical implementation details, see the [Implementation Plan](../IMPLEMENTATION_PLAN.md)*