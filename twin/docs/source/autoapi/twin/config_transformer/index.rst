twin.config_transformer
=======================

.. py:module:: twin.config_transformer

.. autoapi-nested-parse::

   Config Transformer Module
   Maps actionable parameters to mes_data_config.json for simulation



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


   .. py:method:: apply_parameters(parameters, save_path = None)

      Apply actionable parameters to create a new configuration

      :param parameters: ActionableParameters instance with current values
      :param save_path: Optional path to save the transformed config

      :returns: Transformed configuration dictionary



   .. py:method:: create_scenario(scenario_name, parameter_changes)

      Create a specific scenario configuration

      :param scenario_name: Name of the scenario
      :param parameter_changes: Dictionary of parameter names and their new values

      :returns: Scenario configuration



   .. py:method:: create_optimization_scenarios()

      Create standard optimization scenarios for comparison

      :returns: Dictionary of scenario configurations



