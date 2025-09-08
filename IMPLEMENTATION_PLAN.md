# Virtual Ontology - Implementation Plan for Realistic Production Simulation

## Executive Summary

This plan addresses the critical gap between current simulation output (326K units/14 days, 3.9% of target) and realistic production targets based on industry research. The root cause is the batch processing constraint (`batch_size=10, processing_interval=0.1`) limiting throughput to ~16 units/min versus configured rates of 440-500 units/min.

**Goal**: Achieve realistic baseline of 3-4M units/14 days (35-45% of 8.4M target) at 55-60% OEE, with clear optimization path to 75-80% OEE.

## Current State Analysis

### Problems Identified
1. **Unrealistic nominal rates**: 440-500 units/min (exceeds most real-world lines)
2. **Batch processing bottleneck**: Only processes 10 units every 0.1 minutes
3. **Missing V-curve design**: No speed differentials between equipment
4. **No accumulation strategy**: Simple containers, no buffer management
5. **Poor baseline OEE**: 27-36% with no clear improvement path

### Architecture Assessment
✅ **Core architecture is sound**:
- Container-based flow model correct
- Batch processing properly implemented
- State tracking comprehensive
- Failure modeling realistic

⚠️ **Enhancements needed**:
- V-curve speed relationships
- Accumulation buffer strategy
- Constraint tracking (TOC)
- Changeover implementation
- Production order management

## Implementation Phases

### Phase 1: Configuration Corrections (Immediate)
**Objective**: Fix critical bottlenecks without code changes

#### Task 1.1: Fix Batch Processing Constraint
**File**: `config/calibrated_parameters.yaml`

Option A (Preferred - increase batch size):
```yaml
defaults:
  equipment:
    batch_size: 100.0        # Was 10.0 (10x increase)
    processing_interval: 0.1  # Keep same
```

Option B (Alternative - decrease interval):
```yaml
defaults:
  equipment:
    batch_size: 10.0         # Keep same
    processing_interval: 0.01  # Was 0.1 (10x faster)
```

**Impact**: Enables 100 units/min base throughput vs current 10 units/min

#### Task 1.2: Adjust Nominal Rates to Industry Standards
**File**: `config/calibrated_parameters.yaml`

Based on research (Sidel white paper, industry data):
```yaml
equipment_parameters:
  # LINE 1 - Small scale (100 units/min)
  LINE1-FIL:
    nominal_rate: 100.0  # Was 480.0
    performance_factor: 0.65  # Adjusted for poor performance
    
  # LINE 2 - Standard (150 units/min)  
  LINE2-FIL:
    nominal_rate: 150.0  # Was 450.0
    performance_factor: 0.70
    
  # LINE 3 - High speed (200 units/min)
  LINE3-FIL:
    nominal_rate: 200.0  # Was 440.0
    performance_factor: 0.75
```

#### Task 1.3: Implement V-Curve Speed Design
**File**: `config/calibrated_parameters.yaml`

Apply 10-30% speed differentials per V-curve principle:
```yaml
equipment_parameters:
  # LINE 1 V-Curve
  LINE1-SOURCE:
    generation_rate: 120.0   # +20% of filler (push)
  LINE1-FIL:
    nominal_rate: 100.0      # Constraint (bottleneck)
  LINE1-PCK:
    nominal_rate: 110.0      # +10% of filler
  LINE1-PAL:
    nominal_rate: 130.0      # +30% of filler (pull)
  LINE1-SINK:
    collection_rate: 130.0   # Match fastest downstream
```

Repeat for LINE2 and LINE3 with same ratios.

#### Task 1.4: Adjust Failure Parameters
**File**: `config/calibrated_parameters.yaml`

Align with industry standards:
```yaml
defaults:
  equipment:
    mtbf: 150.0         # Was 65.0 (more realistic)
    mttr: 15.0          # Was 35.0 (faster repair)
    micro_stop_rate: 5.0     # Was 2.0 (per hour)
    micro_stop_duration: 20.0  # Was 30.0 (seconds)
```

### Phase 2: Code Enhancements (Priority)
**Objective**: Add missing capabilities without breaking existing code

#### Task 2.1: Create Accumulation Buffer Primitive
**New File**: `twin_model/primitives/accumulation_buffer.py`

```python
class AccumulationBuffer(simpy.Container):
    """Buffer with time-based capacity and FIFO tracking."""
    
    def __init__(self, env, capacity_minutes, flow_rate):
        capacity = capacity_minutes * flow_rate
        super().__init__(env, capacity, init=0)
        self.capacity_minutes = capacity_minutes
        self.flow_rate = flow_rate
        self.utilization_history = []
```

#### Task 2.2: Add V-Curve Controller
**New File**: `twin_model/optimization/vcurve_controller.py`

```python
class VCurveController:
    """Manages speed relationships based on constraint."""
    
    def apply_vcurve(self, equipment_dict, constraint_id):
        """Apply V-curve speed differentials."""
        # Upstream: +10-20% of constraint
        # Downstream: +10-30% of constraint
```

#### Task 2.3: Add Constraint Tracker
**New File**: `twin_model/monitoring/constraint_tracker.py`

```python
class ConstraintTracker:
    """Implements Theory of Constraints tracking."""
    
    def identify_constraint(self, equipment_metrics):
        """Find current bottleneck based on utilization."""
        
    def apply_focusing_steps(self, constraint_id):
        """Implement Goldratt's Five Focusing Steps."""
```

#### Task 2.4: Enhance Changeover Support
**Update**: `twin_model/primitives/equipment_flow.py`

Add changeover matrix and timing:
```python
def calculate_changeover_time(self, from_product, to_product):
    """Calculate changeover duration from matrix."""
    
def perform_changeover(self, new_product):
    """Execute changeover with setup scrap."""
```

### Phase 3: Production Management (Enhancement)
**Objective**: Enable realistic production scenarios

#### Task 3.1: Create Production Orders Configuration
**New File**: `config/production_orders.yaml`

```yaml
orders:
  - order_id: "ORD-2025-001"
    product: "SKU-1001"
    quantity: 50000
    line: "LINE1"
    due_date: "2025-01-15"
    priority: 8
    
  - order_id: "ORD-2025-002"
    product: "SKU-2001"
    quantity: 75000
    line: "LINE2"
    due_date: "2025-01-16"
    priority: 6
```

#### Task 3.2: Add Changeover Matrix
**New File**: `config/changeover_matrix.yaml`

```yaml
changeover_times:  # in minutes
  SKU-1001:
    SKU-1002: 15   # Same family
    SKU-2001: 30   # Different family
    SKU-3001: 45   # Allergen cleaning
    
setup_scrap:  # units lost during changeover
  default: 100
  allergen_change: 500
```

#### Task 3.3: Create Campaign Optimizer
**New File**: `twin_model/scheduling/campaign_optimizer.py`

```python
class CampaignOptimizer:
    """Groups orders to minimize changeovers."""
    
    def optimize_sequence(self, orders, changeover_matrix):
        """Find optimal production sequence."""
```

### Phase 4: Validation & Testing
**Objective**: Verify improvements achieve targets

#### Task 4.1: Update Validation Script
**Update**: `validate_phase3.py`

- Add OEE component tracking (A, P, Q)
- Add constraint identification
- Add buffer utilization metrics
- Compare baseline vs optimized scenarios

#### Task 4.2: Create OEE Improvement Scenarios
**New File**: `test_optimization_scenarios.py`

Test progressive improvements:
1. Baseline: 45-50% OEE (no accumulation)
2. Quick wins: 55-60% OEE (add accumulation)
3. Maintenance: 65-70% OEE (reduce MTTR)
4. Performance: 70-75% OEE (reduce micro-stops)
5. Excellence: 75-80% OEE (optimize all factors)

#### Task 4.3: Create Comparative Report
**New File**: `reports/baseline_vs_optimized.md`

Document improvements:
- Production volume increase
- OEE component changes
- Constraint shifts
- ROI calculations

### Phase 5: Documentation & Reporting
**Objective**: Document changes and provide usage guidance

#### Task 5.1: Update README
Add sections on:
- Realistic production rates
- V-curve configuration
- Accumulation strategy
- TOC implementation

#### Task 5.2: Create Optimization Guide
**New File**: `docs/optimization_guide.md`

Document:
- How to identify constraints
- Improvement strategies
- Parameter tuning guidelines
- Best practices

#### Task 5.3: Update CHANGELOG
Document all changes with rationale and impact.

## Implementation Priority Order

### Week 1: Critical Fixes
1. ✅ Create `reference/theory_notes.md` (COMPLETED)
2. Fix batch processing constraint (Task 1.1)
3. Adjust nominal rates (Task 1.2)
4. Implement V-curve speeds (Task 1.3)
5. Run validation to confirm ~3M units baseline

### Week 2: Core Enhancements
1. Create accumulation buffer (Task 2.1)
2. Add V-curve controller (Task 2.2)
3. Add constraint tracker (Task 2.3)
4. Test with accumulation for 60% OEE

### Week 3: Production Features
1. Create production orders (Task 3.1)
2. Add changeover matrix (Task 3.2)
3. Implement changeover logic (Task 2.4)
4. Test order-based production

### Week 4: Optimization & Documentation
1. Create optimization scenarios (Task 4.2)
2. Document improvements (Task 5.1-5.3)
3. Create final comparative report
4. Package for deployment

## Success Metrics

### Immediate Goals (Week 1)
- [ ] Achieve 2-3M units/14 days (25-35% of target)
- [ ] Baseline OEE: 45-50%
- [ ] Proper V-curve speed relationships
- [ ] Realistic equipment rates (100-200 units/min)

### Short-term Goals (Week 2-3)
- [ ] Achieve 3-4M units/14 days (35-45% of target)
- [ ] Improved OEE: 55-60%
- [ ] Functional accumulation buffers
- [ ] Constraint identification working

### Long-term Goals (Week 4+)
- [ ] Demonstrate path to 6M+ units/14 days
- [ ] Optimized OEE: 70-75%
- [ ] Full production order management
- [ ] Campaign optimization
- [ ] Complete documentation

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: All changes are additive or configuration-only. No breaking changes to core architecture.

### Risk 2: Performance Impact
**Mitigation**: Monitor simulation run time. Batch processing already limits throughput, so improvements should actually reduce computational load.

### Risk 3: Validation Failures
**Mitigation**: Test each change incrementally. Keep old configuration as backup.

## Dependencies

### Required Files
- ✅ `reference/theory_notes.md` (CREATED)
- `config/calibrated_parameters.yaml` (EXISTS - needs update)
- `manifests/equipment_manifest.yaml` (EXISTS - may need update)
- `validate_phase3.py` (EXISTS - needs enhancement)

### Python Dependencies
- SimPy (already installed)
- PyYAML (already installed)
- No new dependencies required

## Next Steps

1. **Review and approve this plan**
2. **Create backup of current configuration**
3. **Implement Phase 1 configuration changes**
4. **Run validation to confirm improvements**
5. **Proceed with Phase 2 code enhancements**

## Notes for Next Session

When starting the next session:
1. Load this implementation plan
2. Check current simulation output (should be ~326K units)
3. Apply Phase 1 fixes
4. Verify output increases to 2-3M units
5. Proceed with remaining phases

## References

- `reference/theory_notes.md` - Theoretical foundation and empirical data
- `reference/White_Paper_Line_Regulation_and_Accumulation.pdf` - Sidel industry data
- `PROJECT_STATUS_HANDOVER.md` - Current system state
- `CHANGELOG.md` - Previous fixes and improvements

---

*Document created: 2025-09-08*
*Author: Virtual Ontology Team*
*Status: Ready for implementation*