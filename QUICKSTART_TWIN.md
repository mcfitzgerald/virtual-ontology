# Virtual Twin Quick Start Guide

## 🚀 Getting Started with Claude Code + Virtual Twin

This guide shows how to use the Virtual Twin system through Claude Code's natural language interface, combining the original virtual ontology SQL capabilities with predictive simulation features.

## Setup (5 minutes)

### 1. Initialize the Database
```bash
# Run once to set up all tables and sample data
python scripts/init_twin_database.py
```

### 2. Start a New Claude Code Session
```
1. Open a new Claude Code session
2. Load the enhanced system prompt:
   "Please review @sys_prompt_twin.md"
3. Claude will now understand both SQL and Twin commands
```

## Core Capabilities

### 🔍 Historical Analysis (SQL)
Original virtual ontology features still work:
```
"What is the average OEE for LINE2?"
"Show me quality trends for the packer last week"
"Which equipment has the most downtime?"
```

### 🔮 Predictive Simulation (Twin)
New twin capabilities for what-if scenarios:
```
"What happens if we reduce micro-stops by 20%?"
"Simulate next week with improved parameters"
"Calculate the financial impact of proposed changes"
```

### 🎯 Recommendations
AI-powered improvement suggestions:
```
"How can we improve OEE?"
"What parameters should we adjust?"
"Give me quick wins for LINE1"
```

## Example Conversations

### Conversation 1: Complete Analysis Flow
```
You: "What is the current performance of our production lines?"
Claude: [Runs SQL query to get current metrics]
        LINE1: OEE 62%, Availability 78%
        LINE2: OEE 71%, Availability 85%
        LINE3: OEE 65%, Availability 80%

You: "Why is LINE2 performing better?"
Claude: [Analyzes differences]
        LINE2 has 38% fewer micro-stops
        Newer equipment (2021 vs 2018)
        Better operator training

You: "What if we reduce micro-stops on LINE1 by 30%?"
Claude: [Runs simulation]
        OEE would improve from 62% to 69%
        Weekly savings: $45,000
        Annual impact: $2.3M

You: "What's the ROI?"
Claude: [Calculates financial impact]
        Investment: $25,000
        Payback: 8 weeks
        NPV: $1.85M
        Recommend: Implement immediately
```

### Conversation 2: Optimization Request
```
You: "Find the best settings to maximize OEE while minimizing energy"
Claude: [Runs multi-objective optimization]
        Found 3 Pareto-optimal solutions:
        
        Option A: Max Performance
        - OEE: 78%, Energy: -15%
        - Best for high-margin products
        
        Option B: Balanced
        - OEE: 75%, Energy: -28%
        - Best for standard operations
        
        Option C: Energy Focus
        - OEE: 72%, Energy: -35%
        - Best for sustainability goals

You: "Implement Option B"
Claude: [Updates parameters]
        ✅ Parameters updated:
        - micro_stop_probability: 0.12
        - performance_factor: 0.88
        - cascade_sensitivity: 0.4
```

## Working Components

### ✅ Fully Functional
- **Database**: 17 tables with 25,000+ records
- **SQL Queries**: Original virtual ontology works
- **Recommendations**: AI suggestions for all scenarios
- **Query Disambiguation**: Natural language understanding
- **Parameter Management**: Validated actionable parameters
- **Cost Calculator**: Financial impact analysis

### ⚠️ Partially Working
- **Simulation Runner**: Core functions work, some methods missing
- **Twin State**: Basic state tracking works
- **Command Interface**: Some commands functional

### 🔧 Optional Components
- **GraphQL API**: Available if needed
- **Visualizations**: Plotly charts can be generated
- **Demo Scenarios**: Pre-built demonstrations

## Command Reference

### Direct Commands (if not using Claude Code)
```bash
# Check status
./twin-command.sh status

# Get recommendations
./twin-command.sh recommend improve_oee

# Run demo
./twin-command.sh demo financial_impact

# Process natural language
./twin-command.sh nlp "What if we reduce downtime by 10%?"
```

### Python API (for advanced users)
```python
from twin.recommendation_engine import RecommendationEngine
from twin.actionable_parameters import ActionableParameters

# Get recommendations
engine = RecommendationEngine()
rec = engine.recommend_for_scenario("improve_oee")

# Set parameters
params = ActionableParameters()
params.set_value("micro_stop_probability", 0.08)
```

## Troubleshooting

### Issue: "No such column: oee"
**Solution**: The mes_data table doesn't have an 'oee' column. Use simulation_data or quality metrics instead:
```sql
SELECT AVG(quality_score) FROM quality_data
SELECT COUNT(*) FROM simulation_data WHERE oee > 0.7
```

### Issue: Command not working
**Solution**: Some methods are not implemented. Use the working features listed above or implement missing methods as needed.

### Issue: API not responding
**Solution**: The original API (api.sh) is for SQL only. Twin operations use Python directly or twin-command.sh.

## Best Practices

### 1. Start Simple
Begin with SQL queries to understand current state, then move to simulations.

### 2. Validate Assumptions
Use historical data to validate simulation predictions.

### 3. Focus on Value
Always translate operational improvements to financial impact.

### 4. Document Patterns
Save successful queries and parameters for reuse.

## Next Steps

### Immediate Actions
1. **Test Basic Queries**: Start with simple SQL to verify connectivity
2. **Try Recommendations**: Ask for improvement suggestions
3. **Run What-If**: Test a simple parameter change scenario

### Learning Path
1. **Week 1**: Master SQL queries and historical analysis
2. **Week 2**: Explore recommendations and parameters
3. **Week 3**: Run simulations and optimizations
4. **Week 4**: Calculate ROI and build business cases

### Advanced Features
- Implement missing simulation methods
- Add multi-objective optimization
- Create custom visualizations
- Build automated optimization loops

## Success Metrics

Track these to measure Virtual Twin value:
- **Query Success Rate**: Target >90%
- **Simulation Accuracy**: Compare predictions to actuals
- **Recommendation Impact**: Measure improvements implemented
- **Time to Insight**: Reduce from hours to minutes
- **ROI Achievement**: Track actual vs predicted savings

## Support

### Documentation
- Original Virtual Ontology: `README.md`
- System Prompt: `sys_prompt_twin.md`
- API Reference: `docs/API_REFERENCE.md`
- Migration Guide: `docs/MIGRATION_GUIDE.md`

### Getting Help
1. Check test results: `python tests/test_twin_integration.py`
2. Review logs: `tail -f twin_commands.log`
3. Inspect database: `sqlite3 data/mes_database.db`

## Summary

The Virtual Twin extends the original virtual ontology with predictive capabilities. While not all features are fully implemented, the core functionality works:

✅ **Natural language → SQL** (Original)
✅ **Natural language → Recommendations** (New)
✅ **Parameter management** (New)
✅ **Financial impact** (New)
⚠️ **Simulations** (Partially working)
⚠️ **Optimizations** (Needs implementation)

Start with what works, and extend as needed. The system is designed to grow with your needs.

---

**Ready to start?** Load `sys_prompt_twin.md` in Claude Code and ask your first question!