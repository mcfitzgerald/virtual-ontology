twin_model.control.parameter_effects
====================================

Parameter effects module for simulation parameter management.

This module defines how simulation parameters affect the actual behavior
of equipment and other primitives in the virtual twin model.


Classes
-------

ParameterCategory
~~~~~~~~~~~~~~~~~

Categories of simulation parameters.


**Attributes:**

- **FAILURE** (attribute): 
- **MAINTENANCE** (attribute): 
- **PERFORMANCE** (attribute): 
- **QUALITY** (attribute): 
- **RESOURCE** (attribute): 
- **SCHEDULING** (attribute): 

**Methods:**

.. method:: __copy__()



.. method:: __deepcopy__(memo)



.. method:: __dir__()

   Returns public methods and other interesting attributes.



.. method:: __format__(format_spec)



.. method:: __hash__()



.. method:: __init__(*args, **kwds)



.. method:: __new__(value)



.. method:: __reduce_ex__(proto)



.. method:: __repr__()



.. method:: __signature__()



.. method:: __str__()



.. method:: _generate_next_value_(name, start, count, last_values)

   Generate the next value when not given.

   name: the name of the member
   start: the initial start value or None
   count: the number of existing members
   last_values: the list of values assigned



.. method:: _missing_(value)



.. method:: name()

   The name of the Enum member.



.. method:: value()

   The value of the Enum member.




ParameterEffect
~~~~~~~~~~~~~~~

Defines how a parameter affects simulation behavior.


**Attributes:**

- **affects_primitives** (attribute): 
- **application_function** (attribute): 
- **base_value** (attribute): 
- **bounds** (attribute): 
- **category** (attribute): 
- **current_value** (attribute): 
- **description** (attribute): 
- **name** (attribute): 
- **unit** (attribute): 


ParameterEffectsManager
~~~~~~~~~~~~~~~~~~~~~~~

Manages how simulation parameters affect model behavior.

This class:
1. Defines all simulation parameters
2. Tracks current parameter values
3. Applies parameters to primitives
4. Validates parameter interactions
5. Provides parameter recommendations

Initialize parameter effects manager.


**Attributes:**

- **parameters** (attribute): 

**Methods:**

.. method:: __init__()

   Initialize parameter effects manager.



.. method:: _define_parameters()

   Define all simulation parameters and their effects.



.. method:: apply_to_config(config: Dict[str, Any], primitive_type: str)

   Apply current parameter values to a primitive configuration.

   :param config: Primitive configuration dictionary
   :param primitive_type: Type of primitive

   :returns: Updated configuration with parameter values



.. method:: get_all_current_values()

   Get current values of all parameters.

   :returns: Dictionary of parameter name to current value



.. method:: get_parameter(name: str)

   Get a parameter by name.

   :param name: Parameter name

   :returns: ParameterEffect or None if not found



.. method:: get_parameters_by_category(category: ParameterCategory)

   Get all parameters in a category.

   :param category: Parameter category

   :returns: Dictionary of parameters in category



.. method:: get_parameters_for_primitive(primitive_type: str)

   Get parameters that affect a specific primitive type.

   :param primitive_type: Type of primitive (e.g., 'EquipmentPrimitive')

   :returns: Dictionary of relevant parameters



.. method:: get_recommendations()

   Get recommendations for parameter improvements.

   :returns: List of parameter adjustment recommendations



.. method:: reset_to_base_values()

   Reset all parameters to their base values.



.. method:: set_parameter_value(name: str, value: float)

   Set a parameter value.

   :param name: Parameter name
   :param value: New value

   :raises ValueError: If parameter doesn't exist or value out of bounds



.. method:: update_from_control_manager(computed_parameters: Dict[str, float])

   Update parameter values from control manager output.

   :param computed_parameters: Dictionary of computed parameter values



.. method:: validate_parameter_set()

   Validate current parameter set for conflicts or issues.

   :returns: List of validation warnings/errors






