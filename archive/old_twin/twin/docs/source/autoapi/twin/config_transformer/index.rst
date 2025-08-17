twin.config_transformer
=======================

.. py:module:: twin.config_transformer

.. autoapi-nested-parse::

   Config Transformer Module
   Applies scaling parameters to baseline configuration for simulation.
   All parameters are treated as multipliers where 1.0 = baseline.



Attributes
----------

.. autoapisummary::

   twin.config_transformer.logger


Classes
-------

.. autoapisummary::

   twin.config_transformer.ConfigTransformer


Module Contents
---------------

.. py:data:: logger

.. py:class:: ConfigTransformer(base_config_path = None, db_path = None)

   Transforms actionable parameters into configuration overlays
   for the MES data generator


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: base_config_path
      :type:  pathlib.Path


   .. py:attribute:: base_config
      :type:  Dict[str, Any]


   .. py:attribute:: config_manager
      :type:  twin.config_manager.ConfigurationManager


   .. py:attribute:: baseline_values
      :type:  Dict[str, Any]


   .. py:method:: apply_parameters(parameters, save_path = None)

      Apply scaling parameters to create a new configuration.

      All parameters are treated as multipliers where 1.0 = baseline.

      :param parameters: ActionableParameters instance with scaling values
      :param save_path: Optional path to save the transformed config

      :returns: Transformed configuration dictionary with scaled values



   .. py:method:: create_scenario(scenario_name, parameter_changes)

      Create a specific scenario configuration.

      :param scenario_name: Name of the scenario
      :param parameter_changes: Dictionary of parameter names and their scaling values

      :returns: Scenario configuration with scaled values



   .. py:method:: create_optimization_scenarios()

      Create standard optimization scenarios for comparison

      :returns: Dictionary of scenario configurations



