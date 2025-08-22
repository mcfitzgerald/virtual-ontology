# Poetry Environment Guide

## Migration Summary
Successfully migrated from pip venv (298 packages) → Poetry (96 packages)
- **68% reduction** in dependencies
- Cleaner dependency resolution
- Reproducible builds with poetry.lock

## Quick Setup
```bash
# Ensure Poetry is in PATH
export PATH="/Users/michael/.local/bin:$PATH"

# Add to your shell profile (~/.zshrc or ~/.bashrc):
export PATH="/Users/michael/.local/bin:$PATH"
alias prun='poetry run'
alias ptest='poetry run pytest'
alias pshell='poetry shell'
alias pmypy='poetry run mypy'
alias pruff='poetry run ruff'
```

## Common Commands

### Environment Management
```bash
poetry install              # Install all dependencies from lock file
poetry update              # Update dependencies to latest compatible versions
poetry env info            # Show environment information
poetry shell               # Activate virtual environment
```

### Dependency Management
```bash
poetry add <package>                    # Add production dependency
poetry add --group dev <package>        # Add dev dependency
poetry add --group docs <package>       # Add docs dependency
poetry remove <package>                 # Remove dependency
poetry show                            # List all installed packages
poetry show --tree                     # Show dependency tree
```

### Running Code
```bash
poetry run python <script.py>           # Run a Python script
poetry run python -m twin_model         # Run a module
poetry run pytest                       # Run tests
poetry run mypy .                       # Type checking
poetry run ruff check .                 # Linting
```

### Project Specific Commands
```bash
# Run the API server
poetry run uvicorn database.app:app --reload

# Run simulations
poetry run python generate_30day_baseline.py

# Run tests
poetry run pytest twin_model/tests/

# Type checking
poetry run mypy twin_model/

# Linting
poetry run ruff check .
poetry run ruff format .
```

## Dependencies Structure

### Production Dependencies (17 packages)
- **Core**: numpy, pandas, simpy, scipy
- **Web/API**: fastapi, uvicorn, sqlmodel, pydantic
- **Visualization**: matplotlib, dash, dash-cytoscape, networkx, pyvis
- **Utilities**: click, pyyaml, dill, requests

### Development Dependencies
- pytest, mypy, ruff, ipython, ipdb

### Documentation Dependencies
- sphinx, sphinx-rtd-theme

## Troubleshooting

### If Poetry command not found:
```bash
export PATH="/Users/michael/.local/bin:$PATH"
```

### To recreate environment from scratch:
```bash
poetry env remove python
poetry install
```

### To export requirements.txt (for compatibility):
```bash
poetry export -f requirements.txt --output requirements.txt
```

## Notes
- Poetry uses the existing venv at `/Users/michael/.venvs/ont`
- The `pyproject.toml` file contains all dependency specifications
- The `poetry.lock` file ensures reproducible installs
- Configuration is set to create virtual environments in project (`.venv`)