# Changelog - Twin Model

All notable changes to the Twin Model simulation framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Comprehensive API documentation system**:
  - Sphinx-based HTML documentation with full API reference
  - LLM-optimized documentation in markdown format (60KB)
  - Custom documentation generator script (generate_llm_docs.py)
  - AutoAPI integration for automatic code documentation extraction
- **Documentation infrastructure**:
  - Sphinx configuration with AutoAPI, MyST parser, and RTD theme
  - Custom templates for LLM-friendly output
  - Documentation build system with HTML and markdown outputs
- **HOW_TO_RUN.md** - Comprehensive guide for running simulations with practical examples
- Configuration loading system with three-tier hierarchy (ontology defaults → manifest properties → runtime config)
- Helper methods in BasePrimitive for configuration access (get_system_config, get_technical_config, get_failure_config)
- Test files for configuration loading (test_config_loading.py) and failure configuration (test_failure_config.py)
- Test plan documentation (docs/development/test_plan.md) for comprehensive test coverage

### Changed
- **docs/README.md** - Updated to include new API documentation sections:
  - Added section for Sphinx HTML documentation
  - Added section for LLM-optimized documentation
  - Enhanced Quick Start with API reference options
  - Added documentation regeneration commands
- **Major refactor: Removed all V2 suffixes** from class names throughout codebase
  - OntologyDrivenModelBuilderV2 → OntologyDrivenModelBuilder
  - EquipmentPrimitiveV2 → EquipmentPrimitive (and all other primitives)
  - Updated all imports and references to use non-V2 names
- Enhanced model_builder.py to load configuration from config/twin_model.yaml
- Updated all primitives to use configuration values instead of hardcoded defaults
  - Equipment: Failure patterns now use system_config.yaml distributions
  - Source: Changeover parameters from configuration
  - Sink: Throughput window from configuration
- Documentation updates to reflect current architecture
  - Fixed V2 references in SYSTEM_USAGE_GUIDE.md, PRIMITIVE_REFERENCE.md, TWIN_ARCHITECTURE.md
  - Updated docs/README.md with prominent HOW_TO_RUN.md reference
  - Updated documentation date to August 30, 2024

### Fixed
- ProductionOrder import and constructor usage in model_builder.py
- Type checking errors with mypy (reduced from 60 to 31 cosmetic issues)
- Linting issues with ruff (44 issues fixed)
- Configuration access throughout primitives using proper helper methods
- Failure configuration to use system_config.yaml instead of hardcoded values

### Removed
- Legacy V2 files and duplicate code:
  - equipment_v2_fixed.py (duplicate of equipment.py)
  - buffer.py (contradicts NO BUFFERS architecture)
  - state_manager.py (unused)
  - config.py (replaced by configuration loading in model_builder)
  - Various obsolete test files (test_final_verification.py, test_logging.py, test_phases_verification.py)
  - serve_docs.py (unused documentation server)
  - README.md (duplicate at root level)
- Archived TWIN_MODEL_REFACTOR_PLAN.md to docs/archive/ (completed and outdated)

### Added
- **Repository cleanup and organization** - comprehensive restructuring for maintainability
- .gitignore file with comprehensive Python and project-specific patterns
- Documentation index (docs/README.md) for easy navigation
- Organized documentation structure with architecture/, guides/, reference/, and development/ folders
- Scripts folder for utility shell scripts (twin.sh, query-log.sh)
- __init__.py files for all test packages to ensure proper Python module structure
- **Phase 7: Complete LLM Documentation** - comprehensive documentation for AI understanding
- TWIN_ARCHITECTURE.md - System overview, design philosophy, and component descriptions
- ONTOLOGY_GUIDE.md - TBox/RBox structure, manifest system, and extension guidelines
- CONTROL_SYSTEM_GUIDE.md - Two-layer control architecture, mapping functions, and optimization strategies
- PRIMITIVE_REFERENCE.md - Detailed specifications for all primitive types with examples
- SIMULATION_PATTERNS.md - Common patterns for failure modeling, changeovers, and optimization
- TROUBLESHOOTING.md - Diagnostic procedures, common issues, and debugging techniques
- **Phase 5: Changeover Modeling** implementation with realistic product-to-product transitions
- Enhanced changeover matrix in SchedulerPrimitiveV2 with family-based and allergen-aware calculations
- Changeover execution process in SourcePrimitiveV2 with state tracking and setup units
- Setup scrap modeling during changeovers with configurable rates
- SMED (Single-Minute Exchange of Die) reduction effects on changeover times
- Changeover test suite (test_changeover_modeling.py) validating matrix calculations, execution, and optimization
- Campaign mode vs mixed production comparison tests
- Changeover metrics tracking (total time, count, setup scrap) in sources
- Production order system with scheduler-to-source dispatch mechanism
- SchedulerPrimitiveV2 with order queue management and line-specific tracking
- Order-aware generation in SourcePrimitiveV2 with progress tracking
- Scheduler manifest (manifests/scheduler_manifest.yaml) with product configurations
- Control effects test suite (test_control_effects.py) validating 7 scenarios
- Control effects documentation (CONTROL_EFFECTS_DOCUMENTATION.md) mapping control→parameter→outcome relationships
- Production order test suite (test_production_orders.py) for order dispatch and completion
- Order completion tracking with actual vs target quantities
- Source registration system connecting schedulers to production lines
- Two-layer control system architecture for actionable controls to simulation parameters
- Control manager system (`twin_model/control/`) for managing plant controls and parameter mappings
- System usage guide (SYSTEM_USAGE_GUIDE.md) documenting all components and workflows
- Control mappings configuration (ontology/control_mappings.yaml) for control-to-parameter relationships
- Control settings manifest (manifests/control_settings.yaml) with baseline control values
- System configuration manifest (manifests/system_config.yaml) for global settings
- Integration tests for full system validation (test_full_integration.py, test_oee_baseline.py)
- Failure tracking counters (failure_count, micro_stop_count) in equipment primitives
- PEP 8, PEP 257, and PEP 484 compliance throughout new code
- Simulation parameters base values in control_mappings.yaml for proper parameter initialization
- Test suites for control mappings validation (test_control_mappings.py, test_specific_mappings.py)
- Material flow test suite (test_material_flow.py) to validate equipment connections

### Changed
- Changeover matrix calculation now considers product families, complexity, and allergen requirements
- Source primitive enhanced with changeover state management and product tracking
- Control mappings updated with changeover_efficiency parameter for SMED effects
- Scheduler now manages per-line active orders instead of single active order
- Model builder extended to load entities from scheduler manifest
- Source primitive enhanced with order queue and completion tracking
- Complete refactor to v2 primitives with internal queues only (no separate buffers)
- Ontology structure updated to TBox/RBox format (twin_ontology.yaml)
- Equipment primitives now use internal queues exclusively for material handling
- Source primitives support both order-driven and continuous generation modes
- Model builder simplified to handle direct equipment-to-equipment connections
- Failure generation fixed to properly trigger micro-stops and failures
- State duration tracking improved with proper finalization
- Performance factor, scrap rate, and micro-stop probability now properly applied
- Control manager now correctly applies base values and multipliers for parameter computation
- Logarithmic mapping function improved to produce proper multipliers starting at 1.0

### Fixed
- Failure generation not triggering (warmup_complete now properly enables failures)
- Parameter naming inconsistency (micro_stop_frequency vs micro_stop_probability)
- State duration tracking incomplete (added finalization step)
- Control parameter application to equipment (direct instance variable updates)
- Source generation timing issues (fixed exponential distribution calculations)
- Critical material flow issues causing excessive STARVED/BLOCKED states (65% → 2-17%)
- Double-queuing bug in equipment where units were put in output queue then transferred
- Blocking detection now properly checks downstream equipment capacity
- Control mapping calculations producing wrong values (mtbf: 10→283, performance: 0.5→0.85)
- Control manager not applying base parameter values from simulation_parameters section
- Logarithmic mapping function returning 0 for zero input (now starts at 1.0)

### Removed
- All v1 primitives (moved to archive/legacy_v1_files/)
- Old test suite (test_phase1-6, test_balanced_model, etc.)
- Obsolete configuration files (SYNTHETIC_DATA_TUNING_PLAN.md, SYSTEM_ARCHITECTURE.md)
- Debug and utility scripts (debug_availability.py, verify_connections.py)
- Old synthetic data generation scripts

## [0.3.0] - Previous Release

### Added
- `utilities/` directory for reusable calibration and analysis tools
- `calibration_work/` directory for temporary calibration artifacts
- New test files in `twin_model/tests/` for calibration validation
- Comprehensive calibration system for twin model KPI tuning
- Auto-wiring capability for production lines in model builder (`_auto_wire_lines()` method)
- Calibration scripts: `calibrate_twin.py`, `apply_best_calibration.py`, `recalibrate_balanced.py`
- Validation and testing scripts for calibrated models
- Multiple synthetic historical data generation runs for baseline comparison
- Manifest performance analysis and fixing utilities

### Changed  
- Reorganized project structure with dedicated directories for utilities and tests
- Moved calibration scripts to `utilities/` for better organization
- Moved test files to `twin_model/tests/` following project conventions
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

### Removed
- Obsolete documentation files moved to archive
- Old synthetic historical data files (keeping only latest)
- Temporary backup and calibration files

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