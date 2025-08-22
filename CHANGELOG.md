# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Build
- **build(deps)**: Migrate to Poetry for dependency management (12ac40c)
  - Reduced dependencies from 298 to 96 packages (68% reduction)
  - Added pyproject.toml with organized dependency groups (prod/dev/docs)
  - Created POETRY_GUIDE.md with complete usage documentation
  - Improved dependency resolution and reproducible builds with poetry.lock

### Added
- POETRY_GUIDE.md - Complete Poetry usage documentation
- pyproject.toml - Poetry configuration with clean dependency organization
- poetry.lock - Lock file for reproducible builds
- requirements-full-backup.txt - Backup of all 298 previous packages

### Changed
- Updated CLAUDE.md to specify Poetry for package management
- Dependency management switched from pip/venv to Poetry

## [Previous Commits]

### Recent Changes
- Enhancements to twin model (5389da8)
- Working SimPy implementation (f704265)
- Database updates (3cff603)
- Major overhaul of system architecture (2610cc4)