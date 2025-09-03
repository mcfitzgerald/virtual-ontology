# Twin Model Documentation Table of Contents

## Overview
This directory contains comprehensive documentation for the Twin Model simulation framework, organized for both human readers and LLM consumption.

## Directory Structure

```
docs/
├── DOCS_TOC.md                          # This file - navigation guide
│
├── llm-ready/                           # LLM-optimized documentation
│   ├── 01-architecture-overview.md      # Ontology-driven architecture with MES integration
│   ├── 02-quickstart-api.md            # Quick start guide with MES examples
│   ├── 03-complete-api-reference.md    # Full API documentation (regenerated)
│   ├── 04-mes-integration-guide.md     # MES scheduling and production guide
│   ├── 05-configuration-reference.md   # Complete configuration reference
│   └── yaml-examples/                   # Example configuration files
│       ├── ontology-filling-line.yaml   # Example ontology definition
│       ├── manifest-equipment.yaml      # Example equipment manifest
│       ├── config-parameters.yaml       # Example tunable parameters
│       ├── mes_parameters.yaml         # MES integration configuration
│       ├── product_manifest.yaml       # Product definitions (30+ products)
│       ├── production_orders.yaml      # Production order examples
│       └── scheduler_config.yaml       # Scheduler optimization settings
│
├── sphinx-source/                        # Sphinx documentation source (RST format)
│   ├── conf.py                          # Sphinx configuration
│   ├── index.rst                        # Main documentation index
│   ├── ontology_guide.rst              # Ontology guide (RST version)
│   ├── api/                             # API documentation stubs
│   └── autoapi/                         # Auto-generated API docs
│
├── templates/                            # Reusable templates
│   └── ontology-template.yaml          # Template for creating new ontologies
│
├── planning/                             # Historical planning documents
│   └── (archived planning docs)
│
└── build/                                # Generated documentation (git-ignored)
    ├── html/                            # HTML documentation
    ├── llms.txt                         # LLM sitemap
    └── llms-full.txt                    # Complete docs in RST format
```

## Documentation Guide

### For LLMs and Quick Reference

Start with **`llm-ready/`** directory:

1. **`01-architecture-overview.md`** (formerly ontology-guide.md)
   - Comprehensive explanation of the ontology-driven architecture
   - Explains the three-file system (ontology, manifest, config)
   - Best practices and troubleshooting

2. **`02-quickstart-api.md`** (formerly api.md)
   - Quick start guide focusing on the three-file pathway
   - Core classes: OntologyModelBuilder, flow primitives
   - Complete working examples

3. **`03-complete-api-reference.md`** (formerly api-full.md)
   - Auto-generated complete API documentation
   - All classes, methods, and parameters
   - Converted from Sphinx output to Markdown

4. **`yaml-examples/`** (formerly examples/)
   - **`ontology-filling-line.yaml`** - Defines equipment types and relationships
   - **`manifest-equipment.yaml`** - Declares actual equipment instances
   - **`config-parameters.yaml`** - Contains tunable simulation parameters

### For Developers

**`sphinx-source/`** contains the source files for generating HTML documentation:
- Run `sphinx-build -b html sphinx-source build` to generate HTML docs
- Contains RST files that integrate with Python docstrings
- Configured with autodoc, napoleon, and autoapi extensions

### For Creating New Configurations

**`templates/`** contains starter templates:
- **`ontology-template.yaml`** - Annotated template for creating new ontologies

## Key Concepts

### The Three-File System

Every Twin Model simulation requires three YAML files:

1. **Ontology** (Structure)
   - Defines what types of equipment CAN exist
   - Specifies relationships and constraints
   - Maps to framework primitives

2. **Manifest** (Instances)
   - Declares what equipment DOES exist
   - Defines topology and connections
   - References ontology types

3. **Config** (Parameters)
   - Contains tunable parameters
   - Separate from structure for easy optimization
   - Includes rates, MTBF/MTTR, quality factors

### Quick Start Path

For LLMs learning the system:
1. Read `llm-ready/01-architecture-overview.md` for concepts and MES integration
2. Review `llm-ready/02-quickstart-api.md` for usage with MES examples
3. Study `llm-ready/04-mes-integration-guide.md` for production scheduling
4. Check `llm-ready/05-configuration-reference.md` for all configuration options
5. Examine `llm-ready/yaml-examples/` for configuration patterns
6. Reference `llm-ready/03-complete-api-reference.md` for API details

### Building Models

```python
from twin_model import OntologyModelBuilder
import simpy

env = simpy.Environment()
builder = OntologyModelBuilder(
    env=env,
    ontology_path="path/to/ontology.yaml",
    manifest_path="path/to/manifest.yaml",
    config_path="path/to/config.yaml"
)
model = builder.build_model()
env.run(until=60)
```

## Documentation Maintenance

### Updating Documentation

1. **Manual Updates**: Edit Markdown files in `llm-ready/` directly
2. **API Updates**: 
   - Modify code docstrings
   - Run `sphinx-build -b html sphinx-source build`
   - Convert with `pandoc -f rst -t markdown build/llms-full.txt -o llm-ready/03-complete-api-reference.md`

### Adding Examples

Place new example files in `llm-ready/yaml-examples/` with descriptive names:
- Use format: `{type}-{description}.yaml`
- Include header comments explaining the example
- Reference from main documentation

## Related Files

- `/README.md` - Project overview
- `/CHANGELOG.md` - Version history
- `/config/` - Active configuration files
- `/manifests/` - Active manifest files
- `/ontology/` - Active ontology files