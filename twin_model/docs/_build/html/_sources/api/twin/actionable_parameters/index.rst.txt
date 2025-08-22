twin.actionable_parameters
==========================

.. py:module:: twin.actionable_parameters

.. autoapi-nested-parse::

   Actionable Parameters Module for Virtual Twin
   Defines the 5 tunable parameters that serve as proxies for real-world improvements



Classes
-------

.. autoapisummary::

   twin.actionable_parameters.ParameterType
   twin.actionable_parameters.ActionableParameter
   twin.actionable_parameters.ActionableParameters


Module Contents
---------------

.. py:class:: ParameterType(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Types of actionable parameters


   .. py:attribute:: PROBABILITY
      :value: 'probability'



   .. py:attribute:: FACTOR
      :value: 'factor'



   .. py:attribute:: RATE
      :value: 'rate'



   .. py:attribute:: SENSITIVITY
      :value: 'sensitivity'



.. py:class:: ActionableParameter

   A tunable parameter that can be adjusted in simulation to model operational changes



   .. py:attribute:: name
      :type:  str


   .. py:attribute:: description
      :type:  str


   .. py:attribute:: bounds
      :type:  Tuple[float, float]


   .. py:attribute:: default_value
      :type:  float


   .. py:attribute:: unit
      :type:  str


   .. py:attribute:: parameter_type
      :type:  ParameterType


   .. py:attribute:: causal_effect
      :type:  str


   .. py:attribute:: invariants
      :type:  List[str]
      :value: []



   .. py:method:: validate(value: float) -> bool

      Check if value is within bounds



   .. py:method:: normalize(value: float) -> float

      Normalize value to [0, 1] range



   .. py:method:: denormalize(normalized: float) -> float

      Convert from [0, 1] back to parameter range



.. py:class:: ActionableParameters(config_path: Optional[str] = None)

   The 5 key parameters that control virtual twin behavior
   These serve as proxies for real-world operational improvements

   Configuration is REQUIRED - all parameter definitions must come from config

   Initialize actionable parameters from configuration.
   Configuration is required - will raise error if not available.

   :param config_path: Optional path to JSON config file for parameter definitions.
                       If not provided, will use ConfigLoader.


   .. py:attribute:: current_values
      :type:  Dict[str, float]


   .. py:method:: set_value(parameter_name: str, value: float) -> None

      Set the value of a parameter with validation

      :param parameter_name: Name of the parameter to set
      :param value: New value for the parameter

      :raises KeyError: If parameter_name is not recognized
      :raises ValueError: If value is outside valid bounds



   .. py:method:: get_value(parameter_name: str) -> float

      Get the current value of a parameter

      :param parameter_name: Name of the parameter

      :returns: Current value of the parameter

      :raises KeyError: If parameter_name is not recognized



   .. py:method:: get_all_values() -> Dict[str, float]

      Get all current parameter values



   .. py:method:: get_all() -> Dict[str, float]

      Alias for get_all_values() for backward compatibility



   .. py:method:: reset(parameter_name: Optional[str] = None) -> None

      Reset parameter(s) to default values

      :param parameter_name: Specific parameter to reset, or None to reset all



   .. py:method:: get_normalized_vector() -> numpy.typing.NDArray[numpy.float64]

      Get all parameters as a normalized vector [0, 1]

      :returns: Numpy array of normalized parameter values



   .. py:method:: set_from_normalized_vector(vector: numpy.typing.NDArray[numpy.float64]) -> None

      Set all parameters from a normalized vector

      :param vector: Numpy array of normalized values [0, 1]

      :raises ValueError: If vector length doesn't match number of parameters



   .. py:method:: get_bounds_for_optimization() -> Tuple[numpy.typing.NDArray[numpy.float64], numpy.typing.NDArray[numpy.float64]]

      Get parameter bounds as arrays for optimization algorithms

      :returns: Tuple of (lower_bounds, upper_bounds) as numpy arrays



   .. py:method:: describe() -> str

      Get human-readable description of all parameters and their current values

      :returns: Formatted string describing all parameters



   .. py:method:: to_dict() -> Dict[str, Any]

      Convert parameters to dictionary representation

      :returns: Dictionary containing parameter definitions and current values



   .. py:method:: to_config_overlay() -> Dict[str, Any]

      Convert current values to configuration overlay format

      :returns: Dictionary in format expected by ConfigTransformer



   .. py:method:: validate_all() -> Tuple[bool, List[str]]

      Validate all current parameter values

      :returns: Tuple of (is_valid, list_of_errors)



