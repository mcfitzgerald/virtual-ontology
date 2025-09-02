# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# General
- I like using your planning mode and working together to brainstorm and vet approaches
- When doing web searches, start with 2025 forward and if few things or nothing found then lift that constraint

# Code practices for Python
- Comply with PEP 8 (Style Guide), PEP 257 (Docstring Conventions), PEP 484 (Type Hints)
- Use `mypy` and `ruff` to validate compliance
- Use judicious testing (test at module or integration level) and manage with `pytest`
- Use `poetry` for project environment and package management

# Running Python commands
- Always use `~/.local/bin/poetry run` to execute Python commands in this project
- Examples:
  - `~/.local/bin/poetry run pytest` for running tests
  - `~/.local/bin/poetry run python script.py` for running scripts
  - `~/.local/bin/poetry run mypy .` for type checking
  - `~/.local/bin/poetry run ruff check` for linting
- Never use bare `python` or `python3` commands as they won't have the project dependencies

# Code authoring by Claude
- Use context7 mcp tool to fetch documentation and example patterns
- When critical, search web for patterns or inspirations
- Vet 2-3 paths before proceed, and confirm with me if you are unsure
- Structure large coding tasks in phases, creating an implementation plan markdown file. 
- Stop and test between phases and make room for us to discuss
- Backward compatibility is seldom a requirement, don't keep legacy code, don't make "V2s and FIXED" files, move the old to archive if unsure, or stop and ask
- **NEVER** use hardcodes, always use config patterns, ask if you are unsure
- Use `semgrep` and appropriate rules files to scan for misplaced hardcodes
- Maintain a CHANGELOG.md file and remind me to use the custom claude code `/commit` command

# TODOs
- create a housekeeping claude command
- create a doc update claude command