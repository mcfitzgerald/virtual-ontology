# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive calibration system for twin model KPI tuning
- Auto-wiring capability for production lines in model builder (`_auto_wire_lines()` method)
- Calibration scripts: `calibrate_twin.py`, `apply_best_calibration.py`, `recalibrate_balanced.py`
- Validation and testing scripts for calibrated models
- Multiple synthetic historical data generation runs for baseline comparison
- Manifest performance analysis and fixing utilities

### Changed  
- Equipment manifest parameters extensively tuned for realistic KPIs:
  - Performance factors adjusted from 0.43-0.55 to 0.77-0.95
  - MTBF reduced to 15-25 minutes for 60% availability target
  - Base rates increased to 80 units/min
  - Quality rates set to 0.95 for 95% quality target
- Production line auto-wiring now establishes bidirectional relationships (feeds_into/draws_from)

### Fixed
- Critical performance issue where `performance_by_product` values <1.0 caused severe slowdown
- Production line connectivity - equipment now properly connected via auto-wiring
- Critical bug where failure patterns weren't loading from manifests to equipment primitives
- Equipment state duration tracking now properly calculates and emits `duration_in_state`
- Availability calculation now correctly reflects MTBF/MTTR settings
- State changes marked as critical events for proper MES transduction

### Changed
- Equipment primitive `_change_state()` method now accepts optional `failure_mode` parameter
- Aggressive tuning of equipment manifests to achieve target KPIs (OEE: 47%, Availability: 69%)
- MTBF reduced from 150-250 to 30-46 minutes for realistic failure rates
- MTTR increased from 30-45 to 74-90 minutes for realistic repair times
- Failure probabilities increased significantly (0.15-0.25 per 5-min interval)

### Added
- Failure pattern loading from manifests based on equipment type in model builder
- Debug scripts for availability calculation analysis (`debug_availability.py`)
- Test script for state duration verification (`test_state_duration.py`)
- Comprehensive Sphinx documentation for `database/` and `twin_model/` modules
- sphinx-autoapi integration for automatic API documentation generation
- System architecture documentation (`SYSTEM_ARCHITECTURE.md`)
- Module-specific documentation structure with source and build directories
- Detailed usage examples and quickstart guides for both modules
- Configuration documentation for database and twin model
- Overview and primitive documentation for the simulation framework
- Ontology-driven architecture documentation

### Changed (Documentation)
- Documentation structure to keep separate docs within each module directory
- Build process to use sphinx-autoapi instead of manual API documentation

### Documentation
- Complete API reference documentation auto-generated from source code
- Intersphinx configuration for cross-module references
- Napoleon extension configured for Google/NumPy docstring styles
- RTD theme applied for professional documentation appearance
- Comprehensive examples for production simulation, scenario testing, and optimization

### Previous Release Notes

### Added
- Full type hints and mypy compliance for `twin_model/` and `database/` directories
- pandas-stubs for better DataFrame type checking
- Explicit imports replacing all star imports for better code clarity
- Type annotations for all function parameters and return types
- Generator type hints with proper return type annotations

### Changed
- All implicit Optional types to explicit Optional[T] for PEP 484 compliance
- SQLAlchemy column attribute access with proper type ignores
- Float/int type conversions in database operations for type safety
- Star imports to explicit imports in database modules
- Boolean comparisons to use proper SQLAlchemy methods with noqa comments

### Fixed
- 109 mypy type errors in `twin_model/` directory (now 0 errors)
- 53 mypy type errors in `database/` directory (now 0 errors)
- All bare except clauses to catch Exception explicitly
- Unused imports and variables throughout codebase
- SQLAlchemy .desc() attribute-defined errors with type ignores
- None handling in method calls with proper type checks
- Variable reuse issues in database cleanup loops

### Removed
- Hardcode analysis files (analysis complete and applied)
- CONFIG_REFACTOR_RESULTS.md (refactoring complete)
- HARDCODE_ANALYSIS_REPORT.md (analysis complete)
- generate_30day_baseline.py (replaced with better testing)
- All hardcodes-*.txt analysis files

### Code Quality
- Full PEP 8, PEP 257, and PEP 484 compliance achieved
- All ruff linting checks pass with zero errors
- Complete type safety with mypy strict checking
- Clean import structure throughout codebase

## [Previous Commits]

### Recent Changes
- Enhancements to twin model (5389da8)
- Working SimPy implementation (f704265)
- Database updates (3cff603)
- Major overhaul of system architecture (2610cc4)