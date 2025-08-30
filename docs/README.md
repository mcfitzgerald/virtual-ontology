# Documentation Index

## 📚 Documentation Structure

### 🤖 API Documentation (Auto-Generated)

#### Sphinx HTML Documentation
Located in `docs/build/html/`:
- **[index.html](build/html/index.html)** - Full API reference with search capability
- Auto-generated from source code with type hints and docstrings
- Includes module hierarchy, class relationships, and method signatures
- **To regenerate**: `sphinx-build -M html docs/source docs/build -c docs/source`

#### LLM-Optimized Documentation
Located in `docs/llm_output/`:
- **[twin_model_api.md](llm_output/twin_model_api.md)** - Markdown-formatted API documentation for LLM consumption
- **[llms.txt](llm_output/llms.txt)** - Plain text version with header (identical content)
- Consolidated, structured documentation optimized for AI context windows
- **To regenerate**: `python docs/generate_llm_docs.py`

### 📖 Manual Documentation

#### Architecture Documentation
Located in `docs/architecture/`:
- **[TWIN_ARCHITECTURE.md](architecture/TWIN_ARCHITECTURE.md)** - Complete system overview, design philosophy, and component relationships
- **[ONTOLOGY_GUIDE.md](architecture/ONTOLOGY_GUIDE.md)** - TBox/RBox structure, manifest system, and extension guidelines

#### User Guides
Located in `docs/guides/`:
- **[SYSTEM_USAGE_GUIDE.md](guides/SYSTEM_USAGE_GUIDE.md)** - How to use the twin model system
- **[CONTROL_SYSTEM_GUIDE.md](guides/CONTROL_SYSTEM_GUIDE.md)** - Two-layer control architecture and optimization strategies
- **[TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)** - Common issues and debugging techniques

#### Reference Documentation
Located in `docs/reference/`:
- **[PRIMITIVE_REFERENCE.md](reference/PRIMITIVE_REFERENCE.md)** - Detailed specifications for all primitive types
- **[SIMULATION_PATTERNS.md](reference/SIMULATION_PATTERNS.md)** - Common patterns for failure modeling, scheduling, and optimization

#### Development Documentation
Located in `docs/development/`:
- **[CONTROL_EFFECTS_DOCUMENTATION.md](development/CONTROL_EFFECTS_DOCUMENTATION.md)** - Control effects validation and relationships
- **[test_plan.md](development/test_plan.md)** - Test coverage and validation plans

## 🚀 Quick Start

### For Different Use Cases:

1. **Want to run a simulation?** Start with **[HOW_TO_RUN.md](HOW_TO_RUN.md)** 
2. **New to the system?** Read [SYSTEM_USAGE_GUIDE.md](guides/SYSTEM_USAGE_GUIDE.md)
3. **Need API reference?** Browse [HTML Documentation](build/html/index.html) or use [LLM Docs](llm_output/twin_model_api.md)
4. **Understanding architecture?** See [TWIN_ARCHITECTURE.md](architecture/TWIN_ARCHITECTURE.md)
5. **Configuring controls?** Check [CONTROL_SYSTEM_GUIDE.md](guides/CONTROL_SYSTEM_GUIDE.md)
6. **Having issues?** Review [TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)

## 🛠️ Documentation Tools

### Viewing Documentation
- **HTML Docs**: Open `docs/build/html/index.html` in a browser
- **Markdown Docs**: View directly in GitHub or any markdown viewer
- **For LLMs**: Use `docs/llm_output/twin_model_api.md` as context

### Regenerating Documentation
```bash
# Regenerate Sphinx HTML documentation
sphinx-build -M html docs/source docs/build -c docs/source

# Regenerate LLM-optimized documentation
python docs/generate_llm_docs.py
```

## 📖 Documentation Status

All documentation is current as of **August 30, 2024** and reflects:
- ✅ Current primitive architecture with direct equipment connections (NO BUFFERS)
- ✅ Production order system with scheduler integration
- ✅ Changeover modeling with SMED effects
- ✅ Two-layer control system
- ✅ Realistic failure patterns and KPI calculations
- ✅ Full API documentation with type hints
- ✅ LLM-optimized documentation format