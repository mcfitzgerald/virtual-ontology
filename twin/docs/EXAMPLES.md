# Virtual Twin Usage Examples

## Overview

This document provides example conversations and usage patterns for the Virtual Twin Manufacturing Intelligence System. These examples demonstrate how Claude Code orchestrates the system through natural language interactions.

## Core Interaction Patterns

### 🔍 Historical Analysis (SQL Queries)
Natural language questions that translate to SQL queries against historical data:
- "What is the average OEE for LINE2?"
- "Show me quality trends for the packer last week"
- "Which equipment has the most downtime?"
- "What's the energy consumption trend?"

### 🔮 Predictive Simulation (What-If Scenarios)
Questions that trigger simulations with adjusted parameters:
- "What happens if we reduce micro-stops by 20%?"
- "Simulate next week with improved performance factor"
- "Calculate the impact of reducing scrap by half"
- "What if we improve material reliability to 95%?"

### 🎯 Optimization & Recommendations
Requests for multi-objective optimization and improvement suggestions:
- "How can we improve OEE?"
- "Find the best balance between energy and throughput"
- "What parameters should we adjust for LINE1?"
- "Give me quick wins for reducing downtime"

### 💰 Financial Analysis
ROI and cost impact calculations:
- "What's the ROI of the proposed changes?"
- "Calculate weekly savings from this improvement"
- "What's the payback period?"
- "Show me the financial impact over 12 months"

## Example Conversations

### Conversation 1: Complete Analysis Flow

```
You: "What is the current performance of our production lines?"

Claude: [Executes SQL query via query-log.sh]
        Based on the MES data analysis:
        - LINE1: OEE 62.3%, Availability 78%, Performance 85%
        - LINE2: OEE 71.2%, Availability 85%, Performance 89%
        - LINE3: OEE 65.4%, Availability 80%, Performance 86%

You: "Why is LINE2 performing better?"

Claude: [Analyzes equipment and operational differences]
        LINE2 shows superior performance due to:
        - 38% fewer micro-stops than LINE1
        - Newer equipment (installed 2021 vs 2018)
        - Lower cascade sensitivity (0.3 vs 0.6)
        - Better material reliability scores

You: "What if we reduce micro-stops on LINE1 by 30%?"

Claude: [Runs SimulationRunner with adjusted parameters]
        Simulation results for LINE1 with 30% micro-stop reduction:
        - OEE improvement: 62.3% → 69.1% (+6.8 points)
        - Availability increase: 78% → 84%
        - Weekly production gain: +2,800 units
        - Estimated weekly savings: $45,000

You: "What's the ROI?"

Claude: [Uses CostImpactCalculator for financial analysis]
        Financial Analysis:
        - Implementation cost: $25,000 (training + minor upgrades)
        - Weekly benefit: $45,000
        - Payback period: 8 days
        - 12-month NPV: $2.31M
        - Confidence interval (95%): $1.85M - $2.78M
        ✅ Strongly recommend implementation
```

### Conversation 2: Multi-Objective Optimization

```
You: "Find the best settings to maximize OEE while minimizing energy consumption"

Claude: [Runs RecommendationEngine with NSGA-II algorithm]
        Running multi-objective optimization...
        Found 3 Pareto-optimal solutions:
        
        Option A: Maximum Performance
        - OEE: 78.2% | Energy: +15% from baseline
        - Parameters: micro_stop_prob=0.08, performance=0.95
        - Best for: High-margin products, rush orders
        
        Option B: Balanced Approach
        - OEE: 75.1% | Energy: -8% from baseline  
        - Parameters: micro_stop_prob=0.12, performance=0.88
        - Best for: Standard production runs
        
        Option C: Energy Focus
        - OEE: 72.3% | Energy: -22% from baseline
        - Parameters: micro_stop_prob=0.15, performance=0.82
        - Best for: Sustainability targets, off-peak production

You: "Implement Option B and track the results"

Claude: [Updates TwinStateManager and creates tracking]
        ✅ Configuration updated:
        - micro_stop_probability: 0.12
        - performance_factor: 0.88
        - cascade_sensitivity: 0.4
        - Configuration saved: cfg-20250811-093045-7a8b9c
        - Baseline snapshot: twin_runs.run_id = 'baseline-20250811'
        - Tracking enabled in parameter_history table
```

### Conversation 3: Root Cause Analysis

```
You: "Why did OEE drop on LINE3 yesterday?"

Claude: [Combines SQL analysis with DisambiguationHelper]
        Analyzing LINE3 performance for yesterday...
        
        OEE dropped from 65.4% to 58.2% (-7.2 points)
        
        Root cause analysis:
        1. Primary factor: Availability dropped to 71% (-9 points)
           - 3 extended micro-stops between 14:00-16:00
           - Equipment: LINE3-PCK (Packer)
           
        2. Contributing factors:
           - Material reliability issue (batch #B2024-187)
           - Cascade effect to downstream palletizer
           - 18% increase in scrap rate during affected period
        
        3. Recommended actions:
           - Inspect LINE3-PCK for mechanical issues
           - Review material quality for batch #B2024-187
           - Adjust cascade_sensitivity parameter from 0.6 to 0.4

You: "Simulate the impact of your recommendations"

Claude: [Runs simulation with recommended changes]
        Simulation with recommended adjustments:
        - OEE recovery: 58.2% → 66.8% (+8.6 points)
        - Exceeds original baseline by 1.4 points
        - Estimated daily savings: $12,000
        - Implementation time: 2-4 hours
```

## Usage Patterns by Intent

### Pattern Recognition
The LLM recognizes user intent through keywords and context:

| User Says | System Uses | Why |
|-----------|-------------|-----|
| "What's current..." | query-log.sh → SQL | Historical data query |
| "What if..." | SimulationRunner | Predictive simulation |
| "Find the best..." | OptimizationEngine | Single objective optimization |
| "Balance X and Y" | RecommendationEngine | Multi-objective optimization |
| "Calculate ROI..." | CostImpactCalculator | Financial analysis |
| "Why is X..." | DisambiguationHelper + SQL | Root cause analysis |
| "How can we improve..." | RecommendationEngine | Improvement suggestions |

## Best Practices

### 1. Start with Understanding
Always begin by querying current state before running simulations:
```
Good: "What's current OEE?" → "What if we improve it by 10%?"
Poor: "Improve OEE by 10%" (without context)
```

### 2. Validate Assumptions
Use historical data to validate simulation predictions:
```
"Compare last month's actual vs simulated performance"
"How accurate were previous predictions?"
```

### 3. Quantify Financial Impact
Always translate operational improvements to business value:
```
"What's the ROI of this change?"
"Calculate annual savings"
"What's the payback period?"
```

### 4. Consider Multiple Objectives
Real-world optimization often involves trade-offs:
```
"Balance throughput and quality"
"Optimize for both OEE and energy efficiency"
"Minimize downtime while controlling costs"
```

### 5. Document Successful Patterns
Save effective parameter combinations:
```
"Save this configuration as 'high-margin-product-settings'"
"Store these parameters for night shift operations"
```

## Advanced Examples

### Comparative Analysis
```
You: "Compare this week's performance against last week and simulate improvements"

Claude: [Multi-step analysis]
        1. Historical comparison (via SQL)
        2. Identify degradation patterns
        3. Run baseline simulation
        4. Generate recommendations
        5. Simulate recommended changes
        6. Calculate ROI
```

### Scenario Planning
```
You: "Create three scenarios for next quarter: aggressive, moderate, and conservative"

Claude: [Creates multiple simulation runs]
        - Aggressive: High investment, maximum optimization
        - Moderate: Balanced approach, proven changes
        - Conservative: Minimal changes, risk-averse
        [Provides detailed comparison table with KPIs and financial projections]
```

### Constraint-Based Optimization
```
You: "Maximize throughput with constraints: quality > 95%, energy < current, no new equipment"

Claude: [Runs constrained optimization]
        Found feasible solution within constraints:
        - Throughput: +12%
        - Quality maintained at 95.2%
        - Energy reduced by 3%
        - Uses only parameter adjustments
```

## Natural Language Flexibility

The system understands various phrasings for the same intent:

### Asking for OEE
- "What's the OEE?"
- "Show me overall equipment effectiveness"
- "How efficient are we running?"
- "What's our productivity score?"

### Requesting Optimization
- "Optimize parameters"
- "Find the best settings"
- "How can we improve?"
- "What should we change?"

### Financial Queries
- "What's the ROI?"
- "Calculate the business case"
- "Show me the money"
- "Is it worth it?"

## Error Handling Examples

### Ambiguous Queries
```
You: "Improve performance"

Claude: I need more context to help you effectively. Could you specify:
        - Which line or equipment? (LINE1, LINE2, LINE3, or all)
        - Which metric? (OEE, quality, throughput, energy)
        - Target improvement? (percentage or specific value)
        - Any constraints? (budget, time, quality limits)
```

### Data Availability
```
You: "Show sensor data from last month"

Claude: The sensor_data table is currently empty. However, I can provide:
        - Historical MES data for the period
        - Calculated metrics from production data
        - Simulated sensor readings if needed
```

### Invalid Parameters
```
You: "Set micro_stop_probability to 2.0"

Claude: Invalid parameter value. micro_stop_probability must be between 0.05 and 0.5.
        A value of 2.0 (200%) is not physically meaningful.
        Did you mean 0.2 (20% probability)?
```

## Integration with Other Systems

### Export for Reporting
```
You: "Export this week's KPIs for the management report"

Claude: [Generates formatted output]
        - CSV export created: kpis_week_32_2025.csv
        - Summary statistics calculated
        - Trend analysis included
        - Ready for dashboard integration
```

### Configuration Templates
```
You: "Save current settings as 'night_shift_optimal'"

Claude: Configuration saved to database:
        - Config ID: cfg-20250811-night-shift-optimal
        - Parameters preserved in simulation_configs table
        - Can be recalled with: "Load night_shift_optimal settings"
```

## Summary

These examples demonstrate the Virtual Twin system's capability to:
1. Understand natural language queries
2. Execute appropriate technical operations
3. Provide business-meaningful results
4. Support decision-making with data
5. Learn from patterns and improve recommendations

The key is the seamless translation between business questions and technical operations, all orchestrated by Claude Code as the intelligent interface.