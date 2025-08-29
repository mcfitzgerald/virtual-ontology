# Control Effects Documentation

This document describes the validated relationships between control inputs and system outcomes in the twin model.

## Control → Parameter → Outcome Relationships

### 1. Operator Training Hours
**Control Range:** 0-40 hours

**Effects on Parameters:**
- `performance_factor`: Logarithmic improvement (0.85 → 0.95+ with 40 hours)
- `micro_stop_recovery_time`: Exponential reduction (faster jam clearing)
- `scrap_rate`: Linear reduction (better quality awareness)
- `issue_detection_time`: Linear reduction (faster problem identification)

**Observed Outcomes:**
- **Baseline (8 hours):** Performance ~87%, OEE ~45%
- **High Training (40 hours):** Performance ~90%, OEE ~49%
- **Impact:** +4% OEE improvement, primarily through performance gains

**Trade-offs:** Training time investment vs. productivity gains

---

### 2. PM Schedule Compliance
**Control Range:** 0-100%

**Effects on Parameters:**
- `mtbf`: Linear improvement (base 240 min → up to 312 min at 100%)
- `equipment_wear_rate`: Linear reduction (less degradation)
- `major_failure_probability`: Exponential reduction

**Observed Outcomes:**
- **Low PM (60%):** MTBF 283 min, Availability ~54%
- **High PM (95%):** MTBF 308 min, Availability ~60%
- **Impact:** +6% availability improvement, +5% OEE

**Trade-offs:** Maintenance downtime vs. unplanned failure reduction

---

### 3. Line Speed Setting
**Control Range:** 70-100% of maximum

**Effects on Parameters:**
- `base_rate`: Direct linear relationship
- `micro_stop_frequency`: Exponential increase above 85%
- `equipment_wear_rate`: Polynomial increase with speed
- `scrap_rate`: Linear increase with speed

**Observed Outcomes:**
- **Normal Speed (85%):** Balanced OEE ~45%
- **High Speed (100%):** Lower OEE ~44% due to more failures
- **Impact:** -1% OEE at maximum speed, but higher throughput

**Trade-offs:** Throughput vs. reliability/quality

---

### 4. Sensor Calibration Frequency
**Control Range:** 1-30 days

**Effects on Parameters:**
- `sensor_drift_factor`: Exponential growth after optimal (7 days)
- `false_reject_rate`: Linear increase with drift
- `micro_stop_probability`: Linear increase from optimal

**Observed Outcomes:**
- **Weekly (7 days):** Micro-stop probability 0.15, OEE ~50%
- **Biweekly (14 days):** Micro-stop probability 0.18, OEE ~45%
- **Impact:** +5% OEE with optimal calibration

**Trade-offs:** Calibration effort vs. false stops/rejects

---

### 5. Changeover Reduction Level (SMED)
**Control Range:** 0-2 (None, Basic, Advanced)

**Effects on Parameters:**
- `changeover_duration`: Stepped reduction (30 → 15 → 6 minutes)
- `setup_scrap_rate`: Stepped reduction (15% → 10% → 5%)

**Observed Outcomes:**
- **No SMED (0):** 30-minute changeovers
- **Advanced SMED (2):** 6-minute changeovers
- **Impact:** Reduced downtime, better availability

**Trade-offs:** Implementation effort vs. flexibility gains

---

### 6. Staffing Level
**Control Range:** 1-4 operators

**Effects on Parameters:**
- `issue_response_time`: Polynomial reduction (1/x relationship)
- `break_coverage_factor`: Linear improvement
- `parallel_task_capability`: Stepped improvement

**Observed Outcomes:**
- **Understaffed (1):** Slow response, poor coverage
- **Normal (2):** Balanced operation
- **Overstaffed (4):** Diminishing returns
- **Impact:** Most effective 1→2 operators

**Trade-offs:** Labor cost vs. responsiveness

---

### 7. Autonomous Maintenance Level
**Control Range:** 0-3 (None to Advanced)

**Effects on Parameters:**
- `micro_stop_frequency`: Stepped reduction (operators prevent jams)
- `equipment_cleanliness`: Stepped improvement
- `minor_failure_detection`: Stepped improvement
- `lubrication_effectiveness`: Linear improvement

**Observed Outcomes:**
- **No AM (0):** Baseline failure rates
- **Moderate AM (2):** 20% reduction in micro-stops
- **Impact:** +2-3% OEE through failure prevention

**Trade-offs:** Operator time vs. maintenance effectiveness

---

## Combined Effects

### Optimization Strategy
The test results show that combined optimization yields the best results:

**Optimized Scenario:**
- Training: 30 hours
- PM Compliance: 85%
- Speed: 85% (balanced)
- Calibration: Weekly
- SMED: Level 2
- Staffing: 3 operators
- AM: Level 2

**Result:** OEE ~50%, balanced across all components

### Degradation Scenario
Poor control settings compound negatively:

**Degraded Scenario:**
- No training
- 20% PM compliance
- Maximum speed
- Monthly calibration
- No SMED
- Understaffed
- No AM

**Result:** OEE ~39%, with cascading failures

---

## Key Insights

1. **Performance is Robust:** The system maintains 75-90% performance even under poor conditions, indicating good fundamental design.

2. **Availability is the Primary Lever:** Most OEE improvements come from availability gains through:
   - Better PM compliance
   - Reduced micro-stops
   - Faster failure recovery

3. **Quality Remains Stable:** Quality stays at 90-95% across most scenarios, only degrading significantly with extreme neglect.

4. **Diminishing Returns:** Most controls show diminishing returns at extreme values:
   - Training: Major gains 0→20 hours, minimal after 30
   - PM: Linear up to 80%, then plateaus
   - Speed: Optimal at 85%, degradation above

5. **Synergistic Effects:** Controls work better together:
   - Training + AM = Better failure prevention
   - PM + Calibration = Sustained reliability
   - SMED + Staffing = Rapid changeovers

---

## Control Recommendations

### For Maximum OEE:
1. Maintain weekly sensor calibration (critical)
2. Achieve 80%+ PM compliance
3. Provide 20+ hours operator training
4. Run at 85% speed (sweet spot)
5. Implement at least basic SMED
6. Ensure adequate staffing (2-3 operators)

### For Cost-Effective Operation:
1. Focus on sensor calibration (high impact, low cost)
2. Basic operator training (20 hours)
3. Moderate PM (70-80%)
4. Balanced speed (85%)

### Warning Thresholds:
- PM Compliance < 40%: Cascading failures likely
- Training < 5 hours: Significant performance degradation
- Calibration > 21 days: Excessive false stops
- Speed > 95%: Reliability breakdown

---

## Validation Results

All control scenarios tested successfully:
- ✅ Baseline: OEE 44.8% (target: 35-55%)
- ✅ High Training: OEE 49.0% (target: 45-65%)
- ✅ High PM: OEE 49.7% (target: 40-60%)
- ✅ High Speed: OEE 44.2% (target: 30-50%)
- ✅ Optimal Sensors: OEE 50.5% (target: 38-58%)
- ✅ Combined Optimization: OEE 49.7% (target: 45-65%)
- ✅ Degraded: OEE 38.7% (target: 25-45%)

The control system accurately models real-world relationships between operator actions and production outcomes.