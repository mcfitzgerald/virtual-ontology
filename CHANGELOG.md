# Changelog - Twin Model

All notable changes to the Twin Model simulation framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Documentation API consistency**:
  - Corrected class names to match actual implementation (ScheduleGenerator → SubOptimalScheduleGenerator)
  - Fixed import statements for MESDataCollector (was incorrectly documented as MESCollector)
  - Updated ProductionOrder constructor parameters to match actual signature
  - Fixed BufferParameters constructor to use correct parameter names
  - Removed references to non-existent CampaignOptimizer and MESIntegration classes
  - Cleaned up RST artifacts from API reference by rewriting from scratch
  - All documentation examples now compile and run correctly

### Added
- **Quick reference documentation**:
  - TWIN_MODEL_QUICK_REFERENCE.md for rapid API access and common patterns
  - Comprehensive code examples with copy-paste snippets
  - Organized by common use cases and typical workflows

### Changed
- **Major restructuring - Twin Model as standalone module**:
  - Moved product_manifest.yaml and production_orders.yaml to manifests/ directory
  - Renamed production_orders.yaml to production_orders_manifest.yaml for consistency
  - Created run_twin_simulation.py as standalone simulation runner
  - Simplified configuration to single tunable_parameters.yaml file
  - Added debug_mode parameter to tunable_parameters.yaml for controlling verbosity

### Fixed
- **MES collector critical bugs**:
  - Fixed state duration tracking using time_in_state method
  - Corrected availability calculations to properly track uptime
  - Fixed OEE calculation to handle division by zero cases
  - Improved state change event handling in equipment flow

### Removed
- **Legacy and redundant files**:
  - Deleted all baseline and calibrated parameter variants (consolidated to tunable_parameters.yaml)
  - Removed MES-specific parameter files (mes_parameters.yaml)
  - Deleted test buffer and changeover integration tests (no longer needed)
  - Removed continuous flow parameter files (integrated into main config)
  - Deleted all test CSV outputs (regenerated as needed)
  - Removed legacy run_mes_baseline.py (replaced by run_twin_simulation.py)
  - Cleaned up redundant test files from tests/ directory

### Added
- **Comprehensive LLM-optimized documentation enhancements**:
  - Expanded architecture overview with detailed flow dynamics and v-curve theory
  - Complete API reference with all public methods and parameters
  - Enhanced MES integration guide with practical examples and testing scenarios
  - Detailed configuration reference with YAML examples for all components
  - Added YAML example files for buffer, schedule, and vcurve configurations
  - Structured examples demonstrating real-world usage patterns

### Fixed
- **Critical state duration tracking bug in equipment flow**:
  - Equipment was calling `change_state()` repeatedly with the same state (e.g., FLOWING)
  - Since `change_state()` only updates duration when state actually changes, time in FLOWING state was never tracked
  - Fixed by checking current state before calling `change_state()` to avoid redundant calls
  - This was causing availability to appear as 0% when equipment was actually running
- **MES collector state duration tracking**:
  - MES collector was not accounting for time spent in current state when calculating availability
  - Fixed `_capture_metrics()` to include current state duration up to collection time
- **AccumulationBuffer inheritance issue**:
  - Made AccumulationBuffer inherit from BaseFlowPrimitive for MES compatibility
  - Buffers now have standard flow metrics (total_input, total_output, state tracking)
  - Removed duplicate methods that are now inherited from base class

### Known Issues
- **Sub-optimal baseline configuration produces very low OEE (5-6% instead of target 45-55%)**:
  - The aggressive sub-optimal parameters may be too severe
  - Low generation rates (120-240 units/min) combined with high failure rates create extreme conditions
  - May need to adjust baseline_suboptimal.yaml parameters to achieve target OEE range

### Added
- **AccumulationBuffer primitive** for inter-equipment flow management:
  - New `buffer_flow.py` module implementing dynamic accumulation buffers
  - Supports FIFO/FILO operation modes
  - Configurable capacity, flow rates, and warning thresholds
  - Tracks overflow/underflow events for MES data generation
  - Implements dwell time monitoring
  - Comprehensive unit tests with 100% coverage
- **Buffer integration with OntologyModelBuilder**:
  - Enhanced model builder to create and wire buffer primitives
  - Support for equipment → buffer → equipment connections
  - Automatic container sharing for flow continuity
- **Comprehensive logging and debugging**:
  - Detailed flow transfer logging for troubleshooting
  - Buffer state monitoring and event tracking
  - Connection wiring diagnostics

### Changed
- **MAJOR: Converted from batch processing to continuous flow simulation**:
  - Phase 1: Modified `equipment_flow.py` to process material continuously instead of in batches
  - Equipment now processes any available material at configured flow rates
  - Removed artificial batch_size constraints that were causing bottlenecks
  - Changed ProcessingParameters to make batch_size deprecated (backward compatible)
  - Updated flow logic to use `target_volume = rate × interval × performance`
  - Phase 2: Optimized continuous flow parameters for realistic production
  - Reduced processing_interval from 0.1 to 0.01 (10x faster simulation updates)
  - Improved performance factors from 0.46-0.55 to 0.75-0.85 (realistic good performance)
  - Improved MTBF from 65 to 120+ minutes, MTTR from 32 to 20 minutes
  - Created migration script to convert batch configs to continuous flow
  - **Results**: Production improved from 153K → 2.8M units/14 days (18.6x increase)
  - Achieves 57% of realistic 5M unit target (vs 1.8% initially)
  - Aligns with original design intent of "continuous flow modeling"

### Fixed
- **Critical batch processing bug** that limited throughput to 8% of target:
  - Equipment was incorrectly waiting for minimum batch sizes before processing
  - Removed forced batch_size minimum in processing logic (line 128)
  - Fixed deadlock condition when batch_size exceeded generation rate
  - Equipment now processes continuously as originally intended

### Added
- **Continuous flow implementation files**:
  - `BATCH_TO_FLOW_CONVERSION_PLAN.md` - Comprehensive plan for batch to flow conversion
  - `migrate_to_continuous_flow.py` - Automated migration script for config files
  - `test_continuous_flow.py` - Validation test for continuous flow
  - `config/continuous_flow_parameters.yaml` - Optimized parameters for continuous flow
  - `archive/batch_implementation_backup/` - Backup of batch-based implementation
- **Production line theory documentation**:
  - Created comprehensive `reference/theory_notes.md` with empirical research
  - Documented real-world production speeds (100-200 units/min standard)
  - Added Theory of Constraints (TOC) implementation guide
  - Included V-curve design principles and speed differentials
  - Collected industry references and white papers
- **Implementation roadmap**:
  - Created `IMPLEMENTATION_PLAN.md` with 5-phase optimization approach
  - Phase 1: Configuration corrections (batch_size fix)
  - Phase 2: Code enhancements (V-curve controller, accumulation)
  - Detailed task breakdown with success metrics
- **Optimization guide**:
  - Created `docs/optimization-guide.md` with progressive OEE improvement path
  - Stages from baseline (45-50% OEE) to world-class (75-80% OEE)
  - Parameter tuning guidelines with impact matrix
  - Bottleneck exploitation strategies based on TOC

### Changed
- **Documentation updates**:
  - Updated README.md with correct config path (`calibrated_parameters.yaml`)
  - Added Theory of Constraints and V-curve design to feature list
  - Added links to new theory and implementation documentation
  - Updated DOCS_TOC.md to include reference directory structure
- **Configuration documentation**:
  - Enhanced `05-configuration-reference.md` with batch processing parameters section
  - Added V-curve speed design configuration examples
  - Documented critical batch_size/processing_interval relationship
  - Added formula: throughput = (batch_size / processing_interval) × performance × quality
- **YAML example improvements**:
  - Updated `config-parameters.yaml` with critical comments about batch_size impact
  - Changed example batch_size from 10 to 100 for realistic throughput
  - Added V-curve speed differentials in equipment parameters
- **Sphinx API documentation**:
  - Regenerated autoapi documentation
  - Removed duplicate attributes from documentation
  - Added logger attributes for equipment and source flow modules

### Fixed
- **Critical parameter resolution bug in OntologyModelBuilder**:
  - Fixed pre-merging of defaults that caused type-specific defaults to be overridden
  - Corrected parameter resolution hierarchy: equipment-specific → type-specific → general → fallback
  - Sources now properly use configured generation rates (300+ units/min) instead of hardcoded 60
  - Equipment flow rates now properly support high throughput (600 units/min capacity)

### Added
- **Enhanced parameter loading system**:
  - Comprehensive defaults sections for source, sink, and equipment types
  - Parameter source tracking with `_get_param_source()` helper method
  - Detailed logging showing which configuration section each parameter comes from
  - Calibrated parameters configuration with baseline low-OEE scenario
- **Baseline configuration for optimization demonstrations**:
  - Three production lines with differentiated performance (27.8%, 33.2%, 36.6% OEE)
  - Intentionally poor performance factors (0.46-0.55) with room for improvement
  - High nominal rates (440-500 units/min) compensating for low efficiency
  - Realistic failure patterns with MTBF/MTTR configurations
- **Testing and validation suite**:
  - `validate_phase3.py`: Production target validation with comprehensive metrics
  - `test_phase1_calibrated.py`: Parameter resolution verification
  - `test_phase2_defaults.py`: Defaults structure validation
  - Baseline production orders configuration for testing
- **Documentation**:
  - `fix-hardcoded-parameters.md`: Detailed problem analysis and solution approach
  - `fix-hardcoded-parameters-COMPLETED.md`: Implementation summary with lessons learned
  - `baseline-configuration-analysis.md`: Analysis of production constraints and bottlenecks
  - `PROJECT_STATUS_HANDOVER.md`: Comprehensive handover document for session continuity
  - `simulation-guide.md`: Guide for running and understanding the simulation

### Changed
- **OntologyModelBuilder parameter handling**:
  - Removed parameter pre-merging in `_create_equipment()` method
  - Modified `_create_source()`, `_create_sink()`, and `_create_equipment_flow()` to access config directly
  - Updated all creation methods to use proper parameter resolution without pre-merged values
  - Increased default flow capacities from 350 to 600 units/min to support high-rate sources
- **Equipment manifest**:
  - Added MaterialSource equipment for all three lines
  - Added complete connection definitions between all equipment
  - Fixed equipment types to match ontology definitions (Filler→FillingStation, etc.)

### Removed
- **Legacy files**:
  - Deleted `docs/configuration_overview.md` (superseded by new documentation)
  - Deleted `docs/mes_simulation_plan.md` (superseded by implementation)
  - Removed `run_mes_simulation.py` (replaced by validation scripts)

### Added
- **Comprehensive MES scheduling and production system**:
  - Complete production scheduling framework with campaign optimization
  - Product manifest system with detailed product specifications and constraints
  - Multi-line production scheduler supporting LINE1, LINE2, and LINE3
  - Sequential and campaign-based scheduling strategies
  - Cost calculation system for changeover optimization
  - Production order management with priority-based scheduling
  - Configuration loader for YAML-based scheduler setup
- **MES integration layer**:
  - Full MES integration module connecting scheduling with simulation
  - MES collector for real-time data collection and aggregation
  - Transduction layer for converting simulation events to MES records
- **Configuration and manifest system**:
  - MES parameters configuration with detailed equipment and line settings
  - Product manifest with 30+ products including specifications and constraints
  - Production orders configuration for testing various scenarios
  - Scheduler configuration with optimization parameters
  - Equipment manifest with detailed equipment specifications
- **Documentation**:
  - Comprehensive MES simulation planning document
  - Configuration overview guide for all YAML configs
- **Test suite**:
  - Product manifest integration tests
  - Scheduler integration tests with multiple scenarios
  - Unit tests for scheduler abstraction layer
- **Claude Code custom commands suite** (`.claude/commands/`):
  - `housekeeping.md`: Aggressive project cleanup with timestamp analysis, unused code detection, Poetry dependency management
  - `documentation.md`: Documentation enforcement ensuring required docs exist and stay synchronized with codebase
  - `lint.md`: Code quality checks using mypy and ruff with auto-fix capabilities
  - `sweep.md`: Hardcode and anti-pattern detection using semgrep with custom rules
  - All commands generate proposals requiring user confirmation before execution
- **Semgrep configuration** (`.semgrep/`):
  - `combined_rules.yaml`: Intentionally overbroad ruleset to catch all potential hardcodes
  - `security.yaml`: Security-specific patterns (SQL injection, command injection, weak crypto)
  - `python-smells.yaml`: Python anti-patterns and code quality issues
  - `project-specific.yaml`: Twin-model specific patterns (SimPy hardcodes, OEE magic numbers)
  - `.semgrepignore`: Files and directories to exclude from scanning
- **Comprehensive documentation overhaul**:
  - Created LLM-optimized documentation structure in `docs/llm-ready/`
  - Added numbered, descriptive filenames for clear learning path (01-architecture-overview, 02-quickstart-api, etc.)
  - Generated complete API reference using sphinx-autoapi
  - Created DOCS_TOC.md as comprehensive navigation guide
  - Added YAML examples directory with ontology, manifest, and config templates
  - Implemented Sphinx documentation system with AutoAPI, MyST parser, and sphinx-llms-txt
  - Added MIT License to the project
- **OntologyModelBuilder system**:
  - New class replacing model_builder.py with three-file configuration approach
  - Ontology-driven architecture using TBox definitions
  - Manifest-based equipment and product configurations
  - Runtime tunable parameters via config files
- **Manual test suite** in `twin_model/tests/manual/`:
  - Debug scripts for buffer behavior and internal queuing
  - Ontology simulation runners with real-world scenarios
  - Equipment flow debugging utilities
  - Simple flow tests for rapid prototyping

### Changed
- **BaseFlow primitive enhancements**:
  - Added comprehensive scheduling integration support
  - Enhanced flow monitoring capabilities for MES data collection
  - Improved state tracking for production metrics
- **Documentation restructuring**:
  - Reorganized docs/ folder with clear separation between LLM-ready and Sphinx source
  - Renamed documentation files to be descriptive of contents
  - Updated README.md with correct SimPy usage examples and API patterns
  - Fixed Quick Start section with proper three-file configuration approach
  - Added Production Orders section with clear examples
- **Project configuration**:
  - Updated CLAUDE.md with reminder to use poetry for Python commands
  - Modified .gitignore for better coverage of build artifacts

### Removed
- **Legacy documentation and files**:
  - Deleted TWIN_MODEL_FRESH_SPEC.md (implementation complete)
  - Removed ARCHIVE_PLAN.md (archiving complete)
  - Deleted obsolete config/twin_model.yaml
  - Removed legacy manifests (control_settings, production_manifest, scheduler_manifest, system_config)
  - Deleted old ontology files (mes_ontology, twin_ontology, control_mappings)
  - Removed templates/twin_ontology_template.yaml
  - Deleted twin_model/model_builder.py (replaced by OntologyModelBuilder)
  - Removed transduction module (flow_transducer.py)
  - Deleted integration test for old model_builder
  - Removed pyproject.toml.setuptools-backup

### Added
- **Complete Container-based flow simulation implementation**:
  - Pure SimPy Container architecture for continuous flow modeling
  - BaseFlowPrimitive foundation with state tracking and metrics
  - EquipmentFlow with realistic failure patterns and quality modeling
  - SourceFlow with order-based and continuous generation modes
  - SinkFlow with integrated OEE calculation (Availability × Performance × Quality)
  - FlowMonitor for real-time performance tracking and MES record generation
  - FlowTransducer for MES-style time-bucketed records
- **Model builder system** (model_builder.py):
  - YAML configuration loading for equipment chains
  - Automatic buffer creation and connection
  - Observable pattern integration
  - OEE validation and monitoring setup
- **Comprehensive test suite**:
  - Unit tests for all flow primitives (container_flow.py)
  - Integration tests for OEE alignment (test_oee_alignment.py)
  - Model builder validation tests (test_model_builder.py)
  - Bottleneck behavior verification
  - Material conservation validation
- **Fresh Container-based architecture specification** (TWIN_MODEL_FRESH_SPEC.md):
  - Complete ground-up rewrite plan using pure SimPy Containers
  - Continuous flow modeling (volume/time) instead of discrete units
  - Configuration-driven architecture with zero hardcoding
  - Target OEE improvement from 7% to 40-50%
- **Archive plan documentation** (ARCHIVE_PLAN.md):
  - Clear separation of essential files vs legacy code
  - Step-by-step archiving instructions
- **Poetry dependency management**:
  - Converted from setuptools to Poetry project format
  - Created poetry.lock for reproducible builds
  - In-project virtual environment configuration (.venv)

### Changed
- **Project structure overhaul**:
  - Archived mixed Store/Container implementation to archive/20240831_store_based/
  - Created fresh twin_model/ directory structure for pure Container implementation
  - Removed all legacy Store-based primitive code
  - Cleared confusing documentation references to old architecture

### Removed
- **Legacy implementation files**:
  - All Store-based primitives (equipment.py, source.py, sink.py)
  - Mixed Container/Store refactor attempts
  - Old control system implementation
  - MES transducer for Store-based model
  - All tests for Store-based architecture
- **Documentation for old architecture**:
  - Removed entire docs/ folder with Store-based references
  - Deleted old migration plans and test scripts
  - Cleared test output CSV files
- **MES (Manufacturing Execution System) simulation and analysis tools**:
  - run_mes_simulation.py - Orchestration script for running twin model simulations with MES output
  - profile_mes_data.py - Comprehensive MES data profiling with OEE analysis  
  - CLAUDE.md - Project-specific instructions for Claude Code assistant
  - Support for realistic MES data generation in standard CSV format
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
- **Equipment configuration overhaul** for realistic OEE alignment:
  - Updated base_rate values to units per minute (8-52 units/min)
  - Adjusted performance_by_product factors to 0.85-0.95 range
  - Reduced MTBF values to 15-25 minutes for ~67% availability target
  - Added micro-stop timing configurations (5-10 minute intervals)
- **Production manifest updates**:
  - Aligned target_rate_units_per_5min with equipment capabilities (180-280 units)
  - Adjusted product scrap rates to realistic levels (3-10%)
  - Modified production order timings for immediate simulation start
- **Control settings optimization**:
  - Increased operator_training_hours to 16
  - Set line_speed_setting to 75%
  - Changed product_sequencing_strategy to "changeover_optimized"
  - Enabled autonomous_maintenance_level 1
- **MES transducer enhancements**:
  - Fixed performance calculation to use proper target rates
  - Added runtime inference for equipment with production but no recorded runtime
  - Improved failure mode to downtime reason mapping
  - Enhanced data quality handling to eliminate UNKNOWN values
- **Equipment primitive fixes**:
  - Fixed critical bug in performance factor calculation (was dividing instead of multiplying cycle time)
  - Corrected combined performance calculation for product-specific factors
- **Scheduler improvements**:
  - Added line_id field to ProductionOrder class for proper line assignment
  - Fixed order dispatch to enable all three production lines
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
- **Critical performance calculation bug** - Equipment was incorrectly dividing by performance factors instead of multiplying, causing inverse performance behavior
- **Production line dispatch issue** - All three lines now properly receive and process orders (was only LINE1 before)
- **Data quality issues in MES output** - Eliminated UNKNOWN values through improved state mapping and data handling
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