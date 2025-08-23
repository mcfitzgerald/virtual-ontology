# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Configuration centralization system in `config/` directory
- Comprehensive logging system with `twin_model/logging_config.py`
- Test suites for critical events, OEE calculations, and logging performance
- Debugging guide documentation (`twin_model/docs/debugging_guide.md`)
- Synthetic historical data generation script
- Hardcode analysis reports and semgrep rules for code quality

### Changed
- Major refactoring of `twin_model/config.py` to use centralized configuration
- Enhanced equipment manifests with improved structure and parameters
- Updated production manifests with better schema organization
- Improved database integration and repository patterns
- Enhanced MES transducer with better error handling and logging
- Refactored equipment primitives with improved cascade modeling
- Fixed custom command syntax in `.claude/commands/commit.md`

### Removed
- POETRY_GUIDE.md (consolidated into project documentation)
- SYSTEM_DOCUMENTATION.md (outdated documentation)
- TWIN_MODEL_LOGGING_AND_FIXES.md (integrated into main docs)
- requirements.txt and requirements-full-backup.txt (replaced by Poetry)

### Fixed
- Equipment cascade failure modeling in primitives
- Database connection handling and transaction management
- Logging configuration for better debugging
- Command syntax error in commit automation script

## [Previous Commits]

### Recent Changes
- Enhancements to twin model (5389da8)
- Working SimPy implementation (f704265)
- Database updates (3cff603)
- Major overhaul of system architecture (2610cc4)