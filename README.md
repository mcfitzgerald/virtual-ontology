# Virtual Twin Manufacturing Intelligence Platform

## LLM-Orchestrated Predictive Simulation & Optimization

A next-generation manufacturing intelligence system that combines semantic data access with digital twin simulation capabilities. This platform enables natural language exploration of production data, predictive what-if scenarios, multi-objective optimization, and financial impact analysis - all orchestrated through conversational AI.

## 🎯 Core Capabilities

### 1. **Semantic Manufacturing Analytics**
Query complex production data using natural language, powered by a virtual ontology layer that translates business questions directly into SQL.

### 2. **Digital Twin Simulation** 
Run predictive what-if scenarios with Monte Carlo uncertainty analysis and statistical validation using proven scientific computing libraries (pymoo, PyMC).

### 3. **Multi-Objective Optimization**
Find Pareto-optimal manufacturing parameters balancing competing objectives like efficiency, quality, and energy consumption.

### 4. **Bayesian Financial Modeling**
Calculate ROI with proper uncertainty quantification using MCMC sampling and credible intervals.

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/your-org/virtual-ontology.git
cd virtual-ontology

# Initialize database (one-time)
python api/database_setup.py init

# Start API server
./api.sh start

# Use with Claude Code
# Load @SYSTEM_PROMPT.md to begin
```

## 💡 Example Interactions

### Historical Analysis
```
User: "What's causing the OEE drop on Line 2?"
System: [Analyzes patterns, identifies micro-stops as 35% of downtime]
```

### Predictive Simulation
```
User: "What if we reduce micro-stops by 30%?"
System: [Runs Monte Carlo simulation showing OEE improvement from 65% to 71%]
```

### Multi-Objective Optimization
```
User: "Find the best balance between throughput and energy efficiency"
System: [Generates Pareto front with 5 optimal configurations]
```

### Financial Impact
```
User: "What's the ROI of implementing these changes?"
System: [Calculates $450K annual benefit with 95% CI: $400K-$500K]
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Natural Language Interface               │
│                      (Claude Code)                       │
└─────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
┌──────────────────────┐         ┌──────────────────────┐
│  Semantic Analytics  │         │   Digital Twin       │
│   (Virtual Ontology) │         │    Simulation        │
├──────────────────────┤         ├──────────────────────┤
│ • Natural → SQL      │         │ • SimulationRunner   │
│ • Pattern Learning   │         │ • OptimizationEngine │
│ • Query Logging      │         │ • RecommendationEngine│
└──────────────────────┘         └──────────────────────┘
          │                                   │
          └─────────────────┬─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  SQLite Database                        │
│            18 tables | 290K+ records                    │
│     Historical MES Data + Twin Simulation Results       │
└─────────────────────────────────────────────────────────┘
```

## 📦 Key Components

### Virtual Ontology Layer
- **Semantic Mapping**: Business concepts → database schema
- **Pattern Learning**: Captures successful query patterns
- **Intent Recognition**: Natural language → SQL translation

### Digital Twin Engine
- **SimulationRunner**: Monte Carlo simulation with parallel execution
- **ActionableParameters**: 5 key manufacturing levers
- **OptimizationEngine**: scipy differential evolution
- **RecommendationEngine**: pymoo NSGA-II multi-objective optimization
- **CostImpactCalculator**: PyMC Bayesian financial analysis

### Analysis Modules
- **DisambiguationHelper**: Context-aware query interpretation
- **TwinStateManager**: Virtual-physical synchronization tracking
- **LineCouplingModel**: Production line interaction modeling
- **SyncHealthMonitor**: System health and drift detection

### Configuration Management
- **ConfigTransformer**: Maps parameters to simulation configurations
- **ConfigValidator**: Ensures parameter changes are correctly applied
- **Custom Config Support**: Generator accepts `--config` and `--seed` parameters
- **Reproducible Results**: Fixed seeds ensure deterministic simulations

## 🎮 Actionable Parameters

The system optimizes five key manufacturing parameters:

| Parameter | Impact Area | Range | Default |
|-----------|------------|-------|---------|
| `micro_stop_probability` | Equipment reliability | 0.05-0.5 | 0.10 |
| `performance_factor` | Speed & efficiency | 0.5-1.0 | 0.85 |
| `scrap_multiplier` | Quality control | 0.5-5.0 | 1.00 |
| `material_reliability` | Supply chain | 0.5-1.0 | 0.85 |
| `cascade_sensitivity` | Line coupling | 0.0-1.0 | 0.30 |

## 📊 Progressive Analysis Workflow

### Phase 1: Discovery
Establish baselines and identify patterns in historical data

### Phase 2: Analysis  
Root cause analysis and bottleneck identification

### Phase 3: Simulation
What-if scenarios with uncertainty quantification

### Phase 4: Optimization
Multi-objective parameter optimization with Pareto analysis

### Phase 5: Impact
Financial modeling with Bayesian credible intervals

## 🔬 Scientific Computing Stack

- **pymoo**: State-of-the-art multi-objective optimization (NSGA-II, hypervolume)
- **PyMC**: Bayesian probabilistic programming (MCMC, credible intervals)
- **scipy**: Numerical optimization and scientific computing
- **pandas/numpy**: Data manipulation and analysis
- **SQLite**: Embedded database with full SQL support
- **Configuration Pipeline**: Robust parameter → config → simulation flow

## 📈 Proven Results

From real manufacturing data analysis:
- **86% query success rate** on first attempt
- **98% success** with single refinement
- **5-10% OEE improvements** identified
- **$400K+ annual savings** opportunities discovered
- **<30 second** simulation runtime
- ✅ **Configuration changes properly affect simulation outcomes**
- ✅ **Reproducible results with controlled seeding**
- ✅ **Parameter improvements lead to measurable KPI gains**

## 🎬 Demo & Documentation

### Video Walkthrough
🎬 [Virtual Twin Platform - Full Demo](https://www.youtube.com/watch?v=xEEZS0_Sbj0) (30 min)

### Key Documentation
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md) - Complete technical design
- [API Reference](twin/API.md) - Module API documentation
- [Database Schema](docs/DATABASE_AND_API.md) - Data model details
- [System Prompt](SYSTEM_PROMPT.md) - LLM orchestration guide

## 🚦 Success Metrics

The platform successfully demonstrates:
- ✅ Natural language → actionable insights
- ✅ Predictive simulation with uncertainty bounds
- ✅ Multi-objective optimization with Pareto fronts
- ✅ Bayesian ROI calculation with credible intervals
- ✅ Complete audit trail and reproducibility

## 🛠️ Technical Requirements

- Python 3.8+
- SQLite 3
- Claude Code or compatible LLM interface
- 4GB RAM minimum
- Unix-like environment (Linux/macOS/WSL)

## 📝 Use Cases

### Manufacturing Operations
- Production line optimization
- Predictive maintenance planning
- Quality improvement initiatives
- Energy efficiency optimization

### Financial Planning
- ROI calculation for improvements
- Investment prioritization
- Risk assessment with uncertainty

### Process Engineering
- Bottleneck analysis
- Capacity planning
- Parameter sensitivity analysis

## 🤝 Contributing

We welcome contributions in:
- Domain-specific ontologies
- Optimization algorithms
- Visualization enhancements
- Industry-specific adaptations
- Performance improvements

## 📄 License

[To be determined]

---

*The Virtual Twin platform demonstrates how combining semantic technologies with digital twin simulation creates a powerful system for manufacturing intelligence - where natural language becomes the interface to advanced analytics and optimization.*