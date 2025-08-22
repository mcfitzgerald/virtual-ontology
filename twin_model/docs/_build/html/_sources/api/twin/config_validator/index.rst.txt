twin.config_validator
=====================

.. py:module:: twin.config_validator

.. autoapi-nested-parse::

   Configuration Validator for Virtual Twin Simulations
   Ensures parameter changes are correctly reflected in generated configurations



Attributes
----------

.. autoapisummary::

   twin.config_validator.logger


Exceptions
----------

.. autoapisummary::

   twin.config_validator.ConfigValidationError


Classes
-------

.. autoapisummary::

   twin.config_validator.ConfigValidator


Functions
---------

.. autoapisummary::

   twin.config_validator.validate_parameter_bounds


Module Contents
---------------

.. py:data:: logger

.. py:exception:: ConfigValidationError

   Bases: :py:obj:`Exception`


   Raised when configuration validation fails

   Initialize self.  See help(type(self)) for accurate signature.


.. py:class:: ConfigValidator

   Validates that transformed configurations will produce expected simulation effects


   Initialize the ConfigValidator with empty error and warning lists.


   .. py:attribute:: validation_errors
      :value: []



   .. py:attribute:: validation_warnings
      :value: []



   .. py:method:: validate_config(config: Dict[str, Any], parameters: Optional[Dict[str, float]] = None) -> bool

      Validate a configuration for simulation

      :param config: The configuration dictionary to validate
      :param parameters: Optional parameter values that were applied

      :returns: True if valid, False otherwise



   .. py:method:: get_report() -> Dict[str, Any]

      Get a detailed validation report



   .. py:method:: validate_config_file(config_path: str) -> bool

      Validate a configuration file



.. py:function:: validate_parameter_bounds(parameters: Dict[str, float]) -> Tuple[bool, List[str]]

   Validate that parameter values are within their defined bounds

   :param parameters: Dictionary of parameter names to values

   :returns: Tuple of (is_valid, list_of_errors)


