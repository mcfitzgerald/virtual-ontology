# Hardcoded Values Documentation

**UPDATE**: A centralized configuration system has been created. See:
- Configuration file: `twin/config/defaults.yaml`
- Configuration loader: `twin/config_loader.py`
- Usage guide: `twin/CONFIG_USAGE.md`

All hardcoded values below have been documented in the configuration file.
Modules still need to be updated to use the ConfigLoader instead of hardcoded values.

## Migration Status

✅ = Configuration created
⏳ = Module needs updating to use config
❌ = Not yet addressed

This document tracks all hardcoded values found during type hint addition.

## actionable_parameters.py

### Parameter Bounds and Defaults
- **micro_stop_probability**: bounds=(0.05, 0.50), default=0.10
- **performance_factor**: bounds=(0.50, 1.00), default=0.85
- **scrap_multiplier**: bounds=(0.5, 5.0), default=1.0
- **material_reliability**: bounds=(0.50, 1.00), default=0.85
- **cascade_sensitivity**: bounds=(0.00, 1.00), default=0.30

### Line References
- Line numbers hardcoded as [1, 2, 3] in `to_config_overlay()`
- Line keys hardcoded as "LINE1", "LINE2", "LINE3"

### Configuration Structure
- Config overlay structure is hardcoded in `to_config_overlay()`
- Mapping from parameters to config sections is hardcoded

## simulation_runner.py

### Date Ranges
- Start date hardcoded as '2025-06-01' in `_execute_simulation()`
- End date format hardcoded

### File Paths
- Generator path default: "synthetic_data_generator/mes_data_generation.py"
- Database path default: "data/mes_database.db"
- Generator version: "1.0.0"

### Simulation Limits
- Duration days limited to 1-30 (should be configurable)
- Random seed range: 0-10000

### Threading
- ThreadPoolExecutor max_workers hardcoded as 4

## sync_health.py

### Default Values
- **Default database path**: "data/mes_database.db"
- **Default sync interval**: 5 minutes
- **Health status thresholds**: 30 minutes for alerts
- **Sync history default**: 24 hours
- **Cleanup retention**: 30 days

### Health Status Thresholds
- HEALTHY: Within sync_interval_minutes
- DELAYED: Within 2x sync_interval_minutes  
- STALE: Beyond 2x sync_interval_minutes

## config_manager.py

### File Paths
- **Default database path**: "data/mes_database.db"
- **Default config directory**: "twin/configs"
- **Default export directory**: "data/simulation_configs"

### Retention Settings
- **Config cleanup retention**: 30 days default

### Limits
- **List configs limit**: 100 (hardcoded in list_configs method)

## config_transformer.py

### File Paths
- **Default base config path**: "synthetic_data_generator/mes_data_config.json"
- **Default database path**: "data/mes_database.db"

### Equipment-Specific Multipliers
- **Filler efficiency**: min=perf_factor*0.88, max=perf_factor*1.08
- **Packer efficiency**: min=perf_factor*0.82, max=perf_factor*1.06
- **Palletizer efficiency**: min=perf_factor*0.94, max=perf_factor*1.12

### Shift Performance Multipliers
- **Shift 1**: min=0.95, max=1.05 of performance_factor
- **Shift 2**: min=0.90, max=1.00 of performance_factor
- **Shift 3**: min=0.85, max=0.95 of performance_factor

### Micro-Stop Probability Multipliers
- **Minor stops Line 1**: 0.8x of micro_stop_probability
- **Recurring jams Line 1**: 0.75x of micro_stop_probability
- **Filler micro-stops**: 0.5x of micro_stop_probability
- **Palletizer micro-stops**: 0.25x of micro_stop_probability

### Scrap Rate Limits & Multipliers
- **Normal scrap rate max**: 0.15 (15%)
- **Startup scrap rate max**: 0.20 (20%)
- **End-of-run quality degradation**: 1.5x scrap_multiplier
- **Changeover scrap spike**: 1.5x scrap_multiplier

### Material & Cascade Settings
- **Material starvation probability**: min=0.01, scale=0.5x(1-reliability)
- **Cascade delay formula**: 10*(1-sensitivity)+1 minutes
- **Performance degradation floor**: 0.3, multipliers: 0.70 min, 0.94 max

### Scenario Parameter Values
All scenario configurations have hardcoded parameter values:
- **Improved Maintenance**: micro_stop=0.10, performance=0.90
- **Better Quality**: scrap_mult=1.2, performance=0.85
- **Optimized Supply**: material_rel=0.95, cascade=0.3
- **Best Case**: micro_stop=0.08, perf=0.95, scrap=1.1, material=0.98, cascade=0.2
- **Worst Case**: micro_stop=0.35, perf=0.60, scrap=3.5, material=0.60, cascade=0.8

## twin_state.py

### Default Values
- **Default database path**: "data/mes_database.db"
- **Default confidence level**: 0.95 (95%) in confidence_tracking table
- **Default validation runs**: 10 for confidence calculation
- **Standard deviation for simulation**: 5% of base value

### Limits
- **Active recommendations limit**: 5 (in _get_active_recommendations)
- **Improvement trends default**: last 5 runs

## cost_impact_calculator.py
(To be checked)

## recommendation_engine.py
(To be checked)

## optimization_engine.py
(To be checked)

## line_coupling_model.py
(To be checked)

## Recommended Actions

1. Create a central configuration file (`twin/config/defaults.yaml`) containing:
   - Parameter definitions (bounds, defaults, units)
   - Line configurations
   - Simulation settings
   - File paths
   - Threading settings

2. Create environment-specific overrides:
   - `twin/config/production.yaml`
   - `twin/config/development.yaml`
   - `twin/config/test.yaml`

3. Add configuration loader class to manage settings

4. Update all classes to accept configuration objects or paths

5. Document configuration schema and options