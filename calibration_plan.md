# Calibration Plan for Twin Model

## Current vs Target KPIs

| Metric | Current | Target | Gap | Priority |
|--------|---------|--------|-----|----------|
| OEE | 37.3% | 67.9% | -30.6% | HIGH |
| Availability | 84.4% | 100.0% | -15.6% | MEDIUM |
| Performance | 48.6% | 75.1% | -26.5% | HIGH |
| Quality | 90.4% | 91.2% | -0.8% | LOW |
| Downtime | 45.7% | 30.6% | +15.1% | MEDIUM |
| Scrap Rate | 5.3% | 8.9% | -3.6% | LOW |

## Root Cause Analysis

### 1. Performance Gap (-26.5%)
**Issue**: Equipment producing at ~50% of rated capacity
**Likely Causes**:
- Starvation: Source arrival rate too low
- Blocking: Downstream buffers too small
- Cycle time mismatch between equipment

### 2. OEE Gap (-30.6%)
**Issue**: Overall effectiveness too low
**Formula**: OEE = Availability × Performance × Quality
- Current: 84.4% × 48.6% × 90.4% = 37.1%
- Target: 100% × 75.1% × 91.2% = 68.5%
**Main driver**: Performance gap

### 3. Availability Gap (-15.6%)
**Issue**: Historical shows 100% availability (unrealistic?)
**Current Issues**:
- Too many failures (MTBF too low)
- Repair times too long (MTTR too high)

## Calibration Strategy

### Phase 1: Fix Performance (Highest Impact)

#### A. Increase Source Arrival Rates
```yaml
# manifests/equipment_manifest.yaml
LINE1-SRC:
  arrival_rate: 150.0  # Increase from 100 to 150
  arrival_pattern: CONSTANT  # More stable flow
```

#### B. Increase Buffer Capacities
```yaml
# Prevent blocking
LINE1-BUF-1:
  capacity: 300  # Increase from 150
LINE1-BUF-2:
  capacity: 200  # Increase from 100
```

#### C. Balance Equipment Rates
```yaml
# Ensure downstream can handle upstream
LINE1-FIL:
  base_rate: 100  # Increase from 70
LINE1-PCK:
  base_rate: 100  # Match filler
LINE1-PAL:
  base_rate: 100  # Match others
```

### Phase 2: Improve Availability

#### A. Increase MTBF (Less Failures)
```yaml
failure_patterns:
  Filler:
    major_failure:
      mtbf: 120  # Increase from 30-46 minutes
      mttr: 30   # Decrease from 74-90 minutes
```

#### B. Reduce Failure Probabilities
```yaml
micro_stops:
  probability_per_5min: 0.05  # Reduce from 0.15-0.25
```

### Phase 3: Fine-tune Quality

#### A. Adjust Scrap Rates
```yaml
products:
  SKU-1001:
    scrap_rates:
      normal: 0.09  # Increase slightly to match historical
```

## Implementation Steps

1. **Create calibration config file**
   - `manifests/calibration_config.yaml`
   - Override specific parameters for calibration

2. **Run calibration tests**
   ```bash
   python calibrate_twin.py --target archive/misc/data/mes_data_with_kpis.csv
   ```

3. **Use optimization approach**
   - Grid search over parameter ranges
   - Minimize KPI differences
   - Use historical patterns as constraints

## Validation Metrics

1. **KPI Matching**
   - OEE within ±5% of target
   - Individual components within ±10%

2. **Distribution Matching**
   - Downtime reasons match historical
   - Production patterns similar
   - Scrap rate distributions align

3. **Operational Patterns**
   - Shift patterns visible
   - Changeover impacts match
   - Product mix effects similar

## Next Steps

1. Implement calibration script
2. Run parameter sweep
3. Validate against historical data
4. Document optimal parameters
5. Update manifests with calibrated values