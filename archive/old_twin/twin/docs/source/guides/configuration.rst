Configuration System Usage Guide
================================

Overview
--------

The Virtual Twin module now uses a centralized configuration system to
manage all settings that were previously hardcoded throughout the
codebase. This makes the system more flexible and easier to customize
for different environments.

Configuration Files
-------------------

Main Configuration File
~~~~~~~~~~~~~~~~~~~~~~~

- **Location**: ``twin/config/defaults.yaml``
- **Purpose**: Contains all default configuration values
- **Format**: YAML with nested structure

Environment-Specific Overrides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

| You can create environment-specific configuration files: -
  ``twin/config/production.yaml`` - Production settings -
  ``twin/config/development.yaml`` - Development settings
| - ``twin/config/test.yaml`` - Test settings

These files only need to contain the values you want to override from
defaults.

Using the Configuration
-----------------------

Basic Usage
~~~~~~~~~~~

.. code:: python

   from twin.config_loader import get_config

   # Get the singleton config instance
   config = get_config()

   # Access configuration values using dot notation
   db_path = config.get("database.path")
   max_workers = config.get("simulation.max_workers", default=4)

   # Get parameter configuration
   param_config = config.get_parameter_config("micro_stop_probability")
   print(f"Bounds: {param_config['bounds']}")
   print(f"Default: {param_config['default']}")

Using with ActionableParameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from twin.actionable_parameters import ActionableParameters
   from twin.config_loader import get_config

   # Parameters can now load from config
   config = get_config()
   params = ActionableParameters()  # Will use config automatically

   # Or load a specific scenario
   scenario_params = config.get_scenario("best_case")
   for param_name, value in scenario_params.items():
       params.set_value(param_name, value)

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

You can override any configuration value using environment variables:

.. code:: bash

   # Override database path
   export TWIN_DATABASE__PATH=/custom/path/to/database.db

   # Override simulation settings
   export TWIN_SIMULATION__MAX_WORKERS=8
   export TWIN_SIMULATION__CONFIDENCE_LEVEL=0.99

   # Set environment
   export TWIN_ENV=production

Environment variables use the pattern: ``TWIN_<SECTION>__<KEY>`` - Use
double underscores (``__``) to separate nested keys - All keys are
converted to lowercase

Configuration Structure
-----------------------

Key Sections
~~~~~~~~~~~~

1.  **database** - Database connection settings
2.  **paths** - File and directory paths
3.  **simulation** - Simulation engine settings
4.  **parameters** - Actionable parameter definitions
5.  **equipment_multipliers** - Equipment-specific settings
6.  **micro_stops** - Micro-stop probability multipliers
7.  **scrap_rates** - Quality and scrap settings
8.  **sync_health** - Synchronization monitoring settings
9.  **retention** - Data retention policies
10. **scenarios** - Pre-configured parameter sets

Migration Guide
---------------

Before (Hardcoded)
~~~~~~~~~~~~~~~~~~

.. code:: python

   class SimulationRunner:
       def __init__(self, db_path="data/mes_database.db"):  # Hardcoded
           self.db_path = db_path
           
       def run_simulation(self, duration_days=7):
           if not 1 <= duration_days <= 30:  # Hardcoded limits
               raise ValueError("Invalid duration")

After (Configuration-Based)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from twin.config_loader import get_config

   class SimulationRunner:
       def __init__(self, db_path=None):
           config = get_config()
           self.db_path = db_path or config.get("database.path")
           
       def run_simulation(self, duration_days=7):
           config = get_config()
           min_days = config.get("simulation.duration_limits.min", 1)
           max_days = config.get("simulation.duration_limits.max", 30)
           if not min_days <= duration_days <= max_days:
               raise ValueError(f"Duration must be between {min_days} and {max_days}")

Testing with Different Configurations
-------------------------------------

.. code:: python

   from twin.config_loader import reload_config

   # Load test configuration
   config = reload_config(environment="test")

   # Run tests with test settings
   runner = SimulationRunner()
   result = runner.run_simulation()

   # Reload development configuration
   config = reload_config(environment="development")

Adding New Configuration Values
-------------------------------

1. Add the new value to ``twin/config/defaults.yaml``:

.. code:: yaml

   my_feature:
     setting1: "default_value"
     setting2: 42

2. Access in code:

.. code:: python

   config = get_config()
   value = config.get("my_feature.setting1", "fallback")

3. Override via environment:

.. code:: bash

   export TWIN_MY_FEATURE__SETTING1="custom_value"

Best Practices
--------------

1. **Always provide defaults** when using ``config.get()``
2. **Document new configuration values** in defaults.yaml with comments
3. **Use meaningful section names** to group related settings
4. **Keep sensitive values** (passwords, keys) in environment variables,
   not config files
5. **Test with different configurations** to ensure flexibility

Debugging Configuration
-----------------------

.. code:: python

   from twin.config_loader import get_config

   config = get_config()

   # Save current configuration to file for inspection
   config.save_override("/tmp/current_config.yaml")

   # Check what environment is loaded
   print(config.environment)  # e.g., "development"

   # Get raw config dictionary
   print(config.config)

Next Steps
----------

To fully migrate the codebase:

1. Update each module to use ``ConfigLoader`` instead of hardcoded
   values
2. Replace all ``TODO: HARDCODED`` comments with config lookups
3. Test with different environment configurations
4. Document any module-specific configuration needs

The configuration system is designed to be backward compatible - modules
will continue to work with their current hardcoded defaults until they
are updated to use the ConfigLoader.
