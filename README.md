# Virtual Twin Manufacturing Intelligence Platform

## LLM-Orchestrated Predictive Simulation & Optimization

A next-generation manufacturing virtual twin that combines semantic data access with digital twin simulation capabilities. This platform enables natural language exploration of production data, predictive what-if scenarios, multi-objective optimization, and financial impact analysis - all orchestrated through conversational AI.

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
│ • Pattern Learning   │         │ • Virtual Sensors    │
│ • Query Logging      │         │ • OptimizationEngine │
└──────────────────────┘         └──────────────────────┘
          │                                   │
          └─────────────────┬─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  SQLite Database                        │
│     MES Data + Twin Results + Virtual Observations      │
│              Raw Facts → Derived Insights               │
└─────────────────────────────────────────────────────────┘
```

### Layered Ontology Design

The Virtual Twin ontology extends (not replaces) the base MES ontology:

```
Virtual Twin Layer (Extensions)
    ↓ extends/observes
Base MES Ontology (Foundation)
    ↓ describes
Physical Manufacturing Data
```

## 📦 Key Components

### Virtual Ontology Layer
- **Semantic Mapping**: Business concepts → database schema
- **Pattern Learning**: Captures successful query patterns
- **Intent Recognition**: Natural language → SQL translation
- **Layered Architecture**: Twin extends base MES without replacement

### Virtual Sensor Layer
Six sensor types derive observations from production data (not synthetic generation):
- **PowerMeterSensor**: Energy consumption from production patterns
- **ThroughputSensor**: Production rate vs target efficiency
- **DefectRateSensor**: Quality through scrap patterns
- **BottleneckDetector**: Production bottlenecks from OEE
- **LineCouplingMonitor**: Equipment coupling and cascade effects
- **DowntimePatternSensor**: Downtime patterns and trends

### Digital Twin Engine
- **SimulationRunner**: Monte Carlo simulation with virtual sensor integration
- **ActionableParameters**: 5 key manufacturing levers (scaling from baseline)
- **OptimizationEngine**: scipy differential evolution
- **RecommendationEngine**: pymoo NSGA-II multi-objective optimization
- **CostImpactCalculator**: PyMC Bayesian financial analysis

### Analysis Modules
- **TwinStateManager**: Virtual-physical synchronization tracking
- **LineCouplingModel**: Production line interaction modeling
- **SyncHealthMonitor**: System health and drift detection

### Configuration Management
- **Dual Config Architecture**: Separated generator.yaml and system.yaml for clarity
- **ConfigLoader**: Enhanced to handle multiple config files with module-specific access
- **ConfigTransformer**: Maps parameters to simulation configurations
- **ConfigValidator**: Ensures parameter changes are correctly applied
- **Integrated Generator**: Data generator now part of twin module
- **Virtual Sensor Config**: Confidence levels configurable in system.yaml
- **Reproducible Results**: Fixed seeds ensure deterministic simulations

## 🎮 Actionable Parameters (Scaling Approach)

The system optimizes five key manufacturing parameters using a scaling approach where 1.0 = baseline production:

| Parameter | Impact Area | Range | Default | Description |
|-----------|------------|-------|---------|-------------|
| `micro_stop_probability` | Equipment reliability | 0.3-1.5 | 1.0 | Maintenance effectiveness (lower is better) |
| `performance_factor` | Speed & efficiency | 0.7-1.3 | 1.0 | Operational excellence multiplier |
| `scrap_multiplier` | Quality control | 0.5-1.5 | 1.0 | Quality control effectiveness (lower is better) |
| `material_reliability` | Supply chain | 0.5-1.2 | 1.0 | Supply chain reliability multiplier |
| `cascade_sensitivity` | Line coupling | 0.5-2.0 | 1.0 | Line decoupling effectiveness (lower is better) |

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
- **Virtual Sensors**: Derive observations from production data patterns
- **Configuration Pipeline**: Robust parameter → config → simulation → observation flow


## 🎬 Demo & Documentation

### Video Walkthrough
🎬 [Virtual Twin Platform - Full Demo]() (30 min)

### Key Documentation
- [System Architecture](SYSTEM_ARCHITECTURE.md) - Complete technical design
- [Twin Modeler](twin/README.md) - Twin Module documentation
- [Database Schema](DATABASE_AND_API.md) - Data model details
- [System Prompt](SYSTEM_PROMPT.md) - LLM orchestration guide

## 🚦 Success Metrics

The platform successfully demonstrates:
- ✅ Natural language → actionable insights
- ✅ Predictive simulation with uncertainty bounds
- ✅ Virtual sensors deriving observations from production data
- ✅ Multi-objective optimization with Pareto fronts
- ✅ Bayesian ROI calculation with credible intervals
- ✅ Complete audit trail and reproducibility
- ✅ Energy derived from patterns, not stored as raw data

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