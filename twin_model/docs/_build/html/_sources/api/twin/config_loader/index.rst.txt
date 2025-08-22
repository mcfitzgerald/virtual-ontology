twin.config_loader
==================

.. py:module:: twin.config_loader

.. autoapi-nested-parse::

   Configuration Loader for Virtual Twin
   Loads configuration from YAML files with environment-specific overrides



Attributes
----------

.. autoapisummary::

   twin.config_loader.logger


Classes
-------

.. autoapisummary::

   twin.config_loader.ConfigLoader


Functions
---------

.. autoapisummary::

   twin.config_loader.get_config
   twin.config_loader.reload_config


Module Contents
---------------

.. py:data:: logger

.. py:class:: ConfigLoader(config_dir: Optional[str] = None, environment: Optional[str] = None, load_generator: bool = True, load_system: bool = True)

   Loads and manages configuration for the Virtual Twin system.

   Configuration is loaded in the following priority order:
   1. system.yaml (system configuration)
   2. generator.yaml (generator configuration)
   3. defaults.yaml (legacy, if exists)
   4. Environment-specific config (e.g., production.yaml, development.yaml)
   5. Environment variables (prefixed with TWIN_)
   6. Runtime overrides

   Initialize the configuration loader.

   :param config_dir: Directory containing configuration files
                      Defaults to twin/config relative to this file
   :param environment: Environment name (production, development, test)
                       Defaults to TWIN_ENV environment variable or 'development'
   :param load_generator: Whether to load generator.yaml
   :param load_system: Whether to load system.yaml


   .. py:attribute:: config_dir
      :type:  pathlib.Path


   .. py:attribute:: environment
      :type:  str
      :value: None



   .. py:attribute:: config
      :type:  Dict[str, Any]


   .. py:attribute:: generator_config
      :type:  Dict[str, Any]


   .. py:attribute:: system_config
      :type:  Dict[str, Any]


   .. py:method:: get(key_path: str, default: Any = None) -> Any

      Get a configuration value using dot notation.

      :param key_path: Dot-separated path to the configuration key
                       e.g., "database.path" or "simulation.max_workers"
      :param default: Default value if key is not found

      :returns: Configuration value or default

      .. rubric:: Example

      >>> config = ConfigLoader()
      >>> db_path = config.get("database.path")
      >>> max_workers = config.get("simulation.max_workers", 4)



   .. py:method:: get_parameter_config(param_name: str) -> Dict[str, Any]

      Get configuration for a specific actionable parameter.

      :param param_name: Name of the parameter

      :returns: Dictionary with parameter configuration including bounds, default, etc.

      :raises KeyError: If parameter is not found in configuration



   .. py:method:: get_all_parameters() -> Dict[str, Dict[str, Any]]

      Get all parameter configurations.

      :returns: Dictionary of parameter configurations



   .. py:method:: get_module_config(module_name: str) -> Dict[str, Any]

      Get configuration for a specific twin module.

      :param module_name: Name of the module (e.g., 'twin_state', 'optimization_engine')

      :returns: Dictionary with module-specific configuration

      .. rubric:: Example

      >>> config = ConfigLoader()
      >>> twin_state_config = config.get_module_config('twin_state')
      >>> validation_runs = twin_state_config['validation']['n_runs']



   .. py:method:: get_generator_config() -> Dict[str, Any]

      Get the complete generator configuration.

      :returns: Dictionary with generator configuration



   .. py:method:: get_system_config() -> Dict[str, Any]

      Get the complete system configuration.

      :returns: Dictionary with system configuration



   .. py:method:: get_scenario(scenario_name: str) -> Dict[str, float]

      Get a pre-configured scenario.

      :param scenario_name: Name of the scenario

      :returns: Dictionary of parameter values for the scenario

      :raises KeyError: If scenario is not found in configuration



   .. py:method:: save_override(override_path: str) -> None

      Save current configuration to a file (useful for debugging).

      :param override_path: Path to save the configuration



.. py:function:: get_config() -> ConfigLoader

   Get the singleton configuration instance.

   :returns: ConfigLoader instance

   .. rubric:: Example

   >>> from twin.config_loader import get_config
   >>> config = get_config()
   >>> db_path = config.get("database.path")


.. py:function:: reload_config(environment: Optional[str] = None) -> ConfigLoader

   Reload configuration with a different environment.

   :param environment: Environment name (production, development, test)

   :returns: New ConfigLoader instance


