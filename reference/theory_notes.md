# Production Line Theory and Empirical Research Notes

## Executive Summary

This document consolidates theoretical foundations and empirical data for realistic production line simulation, based on industry research, academic theory, and real-world operational data. The findings inform the Virtual Ontology simulation framework's parameter calibration and design decisions.

## 1. Real-World Production Line Speeds

### 1.1 Industry Standards by Sector

#### Food & Beverage
- **Standard lines**: 100-200 containers/minute (6,000-12,000/hour)
- **High-speed rotary fillers**: Up to 800+ containers/minute (48,000/hour)
- **Wine bottling**: Maximum 180 bottles/minute
- **Water bottling (semi-automatic)**: ~4 bottles/minute (240/hour)
- **Water bottling (industrial)**: ~20 bottles/minute (1,200/hour)

*Source: Liquid Packaging Solution industry reports, 2024*

#### Pharmaceutical
- **Maximum stable container labeling**: 300 containers/minute
- **Practical inline speed**: Limited to 300 CPM due to validation requirements
- **Regulatory constraint**: Quality control systems cannot exceed 300 CPM effectively

*Source: Manufacturing Chemist, "Speed is of the essence. Or is it?", 2024*

#### Cosmetics
- **Tube filling**: 30-350 tubes/minute depending on viscosity
- **Standard bottle filling**: 100-200 containers/minute

*Source: Tube Filling Machine Market Report, GM Insights, 2024*

### 1.2 Sidel White Paper Findings

From "Line Regulation and Accumulation" (Sidel/Zenith Global, 2019):

#### Production Line Example (10,000 units/hour = 166 units/minute)
- Depalletizer: 11,000 units/hour (183 units/min)
- **Filler: 10,000 units/hour (166 units/min)** ← Bottleneck
- Labeller: 11,000 units/hour (183 units/min)
- Packer: 12,000 units/hour (200 units/min)
- Palletizer: 13,000 units/hour (216 units/min)

#### Key Performance Metrics
- Individual equipment efficiency: **92-97%** (DIN 8743 standard)
- Line performance without accumulation: **85.8%**
- Line performance with accumulation: **97%**
- Industry typical OEE: **60%**

## 2. Theory of Constraints (TOC)

### 2.1 Goldratt's Fundamental Principles

From "The Goal" (Eliyahu M. Goldratt, 1984):

> "An hour lost at a bottleneck is an hour lost out of the entire system. An hour saved at a non-bottleneck is worthless. Bottlenecks govern both throughput and inventory."

### 2.2 The Five Focusing Steps

1. **Identify** the system's constraint (bottleneck)
2. **Exploit** the constraint (maximize its utilization)
3. **Subordinate** everything else to the constraint
4. **Elevate** the constraint (increase capacity)
5. **Repeat** if the constraint has moved

*Source: Theory of Constraints Institute, 2024*

### 2.3 Application to Production Lines

- The filler is typically the constraint in bottling lines
- All upstream equipment should maintain buffer to prevent filler starvation
- All downstream equipment should have excess capacity to prevent filler blocking
- Focus improvement efforts on the constraint for maximum impact

*Source: Goldratt UK, "Unlocking Efficiency", 2024*

## 3. V-Curve Design Principle

### 3.1 Speed Differential Strategy

The V-curve creates:
- **Push scenario**: Upstream equipment runs 10-30% faster than constraint
- **Pull scenario**: Downstream equipment runs 10-30% faster than constraint
- **Result**: Constraint protection from starvation and blocking

### 3.2 Typical Speed Ratios

Based on Sidel white paper analysis:
- Depalletizer: 110% of filler speed
- Filler: 100% (baseline/constraint)
- Labeller: 110% of filler speed
- Packer: 120% of filler speed
- Palletizer: 130% of filler speed

## 4. Batch Processing Reality

### 4.1 Processing Cycle Components

Each fill cycle includes:
- Indexing time (container positioning)
- Fill head dive time (nozzle movement)
- Actual fill time (product transfer)
- Retraction time (nozzle withdrawal)

*Source: Liquid Packaging Solution, "Figuring out Bottles Per Minute", 2024*

### 4.2 Implications for Simulation

- Batch size and processing interval create hard throughput limits
- Maximum throughput = (batch_size / processing_interval) × performance_factor
- Equipment cannot process faster than its cycle time allows
- Buffers essential for decoupling batch operations

## 5. Accumulation and Buffer Strategy

### 5.1 Types of Accumulation

#### Static Accumulation
- First-in-last-out (FILO) basis
- No batch traceability maintained
- Smaller footprint
- Not preferred for modern lines

#### Dynamic Accumulation
- First-in-first-out (FIFO) basis
- Maintains batch traceability
- Larger footprint
- Preferred for food, pharmaceutical, cosmetics

### 5.2 Buffer Sizing Guidelines

From Sidel white paper:
- Pre-constraint buffer: 3-5 minutes of production
- Post-constraint buffer: 2-3 minutes of production
- Inter-equipment buffers: 1-2 minutes of production

### 5.3 Performance Impact

Without accumulation:
- 5 machines at 97% individual efficiency = 85.8% line efficiency
- Lost opportunity: 1,120 units/hour on 10,000 unit/hour line
- Annual loss (€1.2/unit): €7.74 million

With accumulation:
- Same machines maintain 97% line efficiency
- ROI typically achieved within 12-18 months

## 6. OEE Calculation and Standards

### 6.1 OEE Formula

**OEE = Availability × Performance × Quality**

Where:
- **Availability** = Run Time / Planned Production Time
- **Performance** = (Ideal Cycle Time × Total Count) / Run Time
- **Quality** = Good Count / Total Count

### 6.2 Industry Benchmarks

- World-class OEE: **85%** or higher
- Industry typical: **60%**
- Poor performance: **40%** or lower

### 6.3 Loss Categories (Six Big Losses)

1. **Availability Losses**
   - Equipment failures
   - Setup and adjustments

2. **Performance Losses**
   - Idling and minor stoppages
   - Reduced speed

3. **Quality Losses**
   - Process defects
   - Reduced yield

## 7. Discrete Event Simulation Best Practices

### 7.1 SimPy Implementation Considerations

From recent SimPy research (2024):
- Model equipment states: running, stopped, starved, blocked
- Include stochastic failure patterns (MTBF/MTTR)
- Implement proper buffer behavior
- Track material conservation

### 7.2 Key Simulation Metrics

Essential metrics to track:
- Throughput (units/time)
- Equipment utilization (%)
- Buffer levels over time
- Blocking/starvation frequency
- OEE components (A, P, Q)

## 8. Market Context (2024)

### 8.1 Industry Growth

- Filling machines market: USD 7.33B (2024) → USD 10.74B (2031)
- CAGR: 4.90%
- Drivers: Automation, efficiency demands, regulatory compliance

*Source: Verified Market Research, 2024*

### 8.2 Technology Trends

- Integration with APS (Advanced Planning & Scheduling) systems
- Digital twin implementation using discrete event simulation
- Real-time OEE monitoring and optimization
- AI-driven constraint identification

*Source: PlanetTogether APS Trends, 2024*

## 9. Recommendations for Simulation Parameters

### 9.1 Realistic Baseline Configuration

Based on empirical data, recommend:
- **Line 1**: 100 units/min (small-scale operation)
- **Line 2**: 150 units/min (standard operation)
- **Line 3**: 200 units/min (high-speed operation)

### 9.2 Equipment Parameters

**Availability**:
- MTBF: 120-180 minutes (realistic for modern equipment)
- MTTR: 10-30 minutes (with trained maintenance)
- Target availability: 85-90%

**Performance**:
- Micro-stops: 5-10 per hour, 10-30 seconds each
- Speed losses: 10-15% below ideal cycle time
- Target performance: 75-85%

**Quality**:
- Defect rates: 2-6% (product dependent)
- Rework potential: 20-30% of defects
- Target quality: 94-98%

### 9.3 Batch Processing Settings

To achieve realistic throughput:
- **Option A**: batch_size=100, processing_interval=0.1 min
- **Option B**: batch_size=10, processing_interval=0.01 min
- Both yield ~100 units/min base capacity

## 10. Implementation Phases

### Phase 1: Baseline Establishment (45-50% OEE)
- No accumulation
- Poor maintenance (high MTTR)
- Frequent micro-stops
- Represents "problem state"

### Phase 2: Quick Wins (55-60% OEE)
- Add basic accumulation
- Improve maintenance response
- Represents "current state" for many facilities

### Phase 3: Systematic Improvement (65-70% OEE)
- Optimize buffer sizes
- Reduce micro-stops
- Improve changeover procedures
- Represents "industry typical"

### Phase 4: Excellence (75-80% OEE)
- Advanced scheduling
- Predictive maintenance
- Quality at source
- Represents "best practice"

## References

1. Sidel/Zenith Global (2019). "Line Regulation and Accumulation White Paper". Retrieved from provided PDF.

2. Goldratt, E.M. (1984). "The Goal: A Process of Ongoing Improvement". North River Press.

3. Theory of Constraints Institute (2024). "Theory of Constraints of Eliyahu M. Goldratt". https://www.tocinstitute.org/theory-of-constraints.html

4. Liquid Packaging Solution (2024). "Filling Machines: Figuring Out Your Bottles Per Minute Need". https://www.liquidpackagingsolution.com/

5. Manufacturing Chemist (2024). "Speed is of the essence. Or is it?". https://www.manufacturingchemist.com/

6. DIN 8743. "Packaging machines and packaging lines - Key figures for characterizing reliability and availability".

7. Verified Market Research (2024). "Filling Machines Market Size, Share, Scope, Trends & Forecast".

8. PlanetTogether (2024). "Goldratt's Theory of Constraints & APS". https://www.planettogether.com/

9. GM Insights (2024). "Tube Filling Machine Market Share, 2034 Statistics Report".

10. Goldratt UK (2024). "Unlocking Efficiency: Applying Theory of Constraints in Manufacturing".

11. Various SimPy documentation and research papers (2024). https://simpy.readthedocs.io/

## Document Information

- Created: 2025-09-08
- Author: Virtual Ontology Team
- Purpose: Theoretical foundation and empirical data for production line simulation
- Version: 1.0