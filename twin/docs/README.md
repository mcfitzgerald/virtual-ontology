# Virtual Twin Documentation

This directory contains the Sphinx documentation for the Virtual Twin module.

## Building the Documentation

### Prerequisites

Ensure you have the required packages installed:
```bash
pip install sphinx sphinx-autoapi sphinx-rtd-theme sphinx-autodoc-typehints pandoc
```

### Build Commands

From this directory (`twin/docs/`), run:

```bash
# Build HTML documentation
make html

# Clean build artifacts
make clean

# Build and clean in one command
make clean html
```

The built documentation will be available at `build/html/index.html`.

### Documentation Structure

- `source/` - Source RST files for documentation
  - `conf.py` - Sphinx configuration
  - `index.rst` - Main documentation index
  - `api/` - API reference documentation
  - `guides/` - User guides and tutorials
    - `quickstart.rst` - Quick start guide
    - `configuration.rst` - Configuration guide
    - `examples.rst` - Comprehensive examples
    - `migration.rst` - Migration guide
- `build/` - Built documentation (generated)
- `Makefile` - Build automation

### Key Features

- **AutoAPI Integration**: Automatically generates API documentation from docstrings
- **Interactive Examples**: Comprehensive code examples for all major features
- **Cross-references**: Full intersphinx support for Python, NumPy, Pandas, etc.
- **Theme**: Uses the popular Read the Docs theme for familiar navigation

### Viewing the Documentation

After building, you can view the documentation by:
```bash
# macOS
open build/html/index.html

# Linux
xdg-open build/html/index.html

# Or start a local server
python -m http.server 8000 --directory build/html
```

Then navigate to http://localhost:8000 in your browser.