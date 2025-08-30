twin_model.control.control_manager
==================================

Control manager for two-layer control system.

This module manages the mapping between actionable controls (what plant managers change)
and simulation parameters (internal model behavior). It loads mappings from the ontology
and applies transformations based on control values.


Classes
-------

ControlDefinition
~~~~~~~~~~~~~~~~~

Definition of an actionable control.


**Attributes:**

- **bounds** (attribute): 
- **datatype** (attribute): 
- **default** (attribute): 
- **description** (attribute): 
- **name** (attribute): 
- **options** (attribute): 


ControlManager
~~~~~~~~~~~~~~

Manages the two-layer control system.

This class:
1. Loads control definitions from ontology
2. Loads control mappings from configuration
3. Applies current control settings
4. Computes simulation parameters from controls

Initialize control manager.

:param ontology_path: Path to twin ontology with control definitions
:param mappings_path: Path to control mappings configuration
:param settings_path: Optional path to current control settings


**Attributes:**

- **controls** (attribute): 
- **mappings** (attribute): 
- **mappings_config** (attribute): 
- **mappings_path** (attribute): 
- **ontology** (attribute): 
- **ontology_path** (attribute): 
- **settings_path** (attribute): 
- **state** (attribute): 

**Methods:**

.. method:: __init__(ontology_path: pathlib.Path, mappings_path: pathlib.Path, settings_path: Optional[pathlib.Path] = None)

   Initialize control manager.

   :param ontology_path: Path to twin ontology with control definitions
   :param mappings_path: Path to control mappings configuration
   :param settings_path: Optional path to current control settings



.. method:: _apply_bounds(params: Dict[str, float])

   Apply parameter bounds from configuration.

   :param params: Computed parameters

   :returns: Bounded parameters



.. method:: _apply_defaults()

   Apply default control values.



.. method:: _apply_mapping(control_value: Any, mapping: ParameterMapping)

   Apply a mapping function to transform control to parameter.

   :param control_value: Current control value
   :param mapping: Mapping configuration

   :returns: Computed parameter value



.. method:: _load_yaml(path: pathlib.Path)

   Load YAML configuration file.



.. method:: _parse_controls()

   Parse control definitions from ontology.



.. method:: _parse_mappings()

   Parse control to parameter mappings.



.. method:: apply_scenario(scenario_name: str)

   Apply a predefined scenario.

   :param scenario_name: Name of scenario to apply

   :returns: True if scenario was applied



.. method:: describe_control(name: str)

   Get human-readable description of a control.

   :param name: Control name

   :returns: Description string



.. method:: get_all_parameters()

   Get all computed parameters.

   :returns: Dictionary of parameter values



.. method:: get_control_value(name: str)

   Get current value of a control.

   :param name: Control name

   :returns: Current control value



.. method:: get_parameter(name: str, default: float = 0)

   Get computed simulation parameter.

   :param name: Parameter name
   :param default: Default value if not found

   :returns: Parameter value



.. method:: get_recommendations()

   Get recommendations for control improvements.

   :returns: List of recommendations with expected impact



.. method:: get_scenario(scenario_name: str)

   Get predefined scenario configuration.

   :param scenario_name: Name of scenario

   :returns: Scenario configuration or None



.. method:: load_settings(path: pathlib.Path)

   Load control settings from file.

   :param path: Path to control settings YAML



.. method:: save_settings(path: pathlib.Path)

   Save current control settings to file.

   :param path: Path to save settings



.. method:: set_control_value(name: str, value: Any)

   Set control value and recompute parameters.

   :param name: Control name
   :param value: New value



.. method:: update_parameters()

   Recompute all simulation parameters from current controls.




ControlState
~~~~~~~~~~~~

Current state of all controls.


**Attributes:**

- **computed_parameters** (attribute): 
- **values** (attribute): 

**Methods:**

.. method:: get(control_name: str, default: Any = None)

   Get control value with default.



.. method:: set(control_name: str, value: Any)

   Set control value.




MappingFunction
~~~~~~~~~~~~~~~

Types of mapping functions supported.

Initialize self.  See help(type(self)) for accurate signature.


**Attributes:**

- **EXPONENTIAL** (attribute): 
- **LINEAR** (attribute): 
- **LOGARITHMIC** (attribute): 
- **POLYNOMIAL** (attribute): 
- **SIGMOID** (attribute): 
- **STEPPED** (attribute): 

**Methods:**

.. method:: __add__()

   Return self+value.



.. method:: __contains__()

   Return bool(key in self).



.. method:: __copy__()



.. method:: __deepcopy__(memo)



.. method:: __delattr__()

   Implement delattr(self, name).



.. method:: __dir__()

   Default dir() implementation.



.. method:: __eq__()

   Return self==value.



.. method:: __format__()

   Return a formatted version of the string as described by format_spec.



.. method:: __ge__()

   Return self>=value.



.. method:: __getattribute__()

   Return getattr(self, name).



.. method:: __getitem__()

   Return self[key].



.. method:: __getnewargs__()



.. method:: __getstate__()

   Helper for pickle.



.. method:: __gt__()

   Return self>value.



.. method:: __hash__()

   Return hash(self).



.. method:: __init__()

   Initialize self.  See help(type(self)) for accurate signature.



.. method:: __iter__()

   Implement iter(self).



.. method:: __le__()

   Return self<=value.



.. method:: __len__()

   Return len(self).



.. method:: __lt__()

   Return self<value.



.. method:: __mod__()

   Return self%value.



.. method:: __mul__()

   Return self*value.



.. method:: __ne__()

   Return self!=value.



.. method:: __new__()

   Create and return a new object.  See help(type) for accurate signature.



.. method:: __reduce__()

   Helper for pickle.



.. method:: __reduce_ex__()

   Helper for pickle.



.. method:: __repr__()

   Return repr(self).



.. method:: __rmod__()

   Return value%self.



.. method:: __rmul__()

   Return value*self.



.. method:: __setattr__()

   Implement setattr(self, name, value).



.. method:: __signature__()



.. method:: __sizeof__()

   Return the size of the string in memory, in bytes.



.. method:: __str__()

   Return str(self).



.. method:: __subclasshook__()

   Abstract classes can override this to customize issubclass().

   This is invoked early on by abc.ABCMeta.__subclasscheck__().
   It should return True, False or NotImplemented.  If it returns
   NotImplemented, the normal algorithm is used.  Otherwise, it
   overrides the normal algorithm (and the outcome is cached).



.. method:: _generate_next_value_(name, start, count, last_values)

   Generate the next value when not given.

   name: the name of the member
   start: the initial start value or None
   count: the number of existing members
   last_values: the list of values assigned



.. method:: _missing_(value)



.. method:: capitalize()

   Return a capitalized version of the string.

   More specifically, make the first character have upper case and the rest lower
   case.



.. method:: casefold()

   Return a version of the string suitable for caseless comparisons.



.. method:: center()

   Return a centered string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: count()

   S.count(sub[, start[, end]]) -> int

   Return the number of non-overlapping occurrences of substring sub in
   string S[start:end].  Optional arguments start and end are
   interpreted as in slice notation.



.. method:: encode()

   Encode the string using the codec registered for encoding.

   encoding
     The encoding in which to encode the string.
   errors
     The error handling scheme to use for encoding errors.
     The default is 'strict' meaning that encoding errors raise a
     UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
     'xmlcharrefreplace' as well as any other name registered with
     codecs.register_error that can handle UnicodeEncodeErrors.



.. method:: endswith()

   S.endswith(suffix[, start[, end]]) -> bool

   Return True if S ends with the specified suffix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   suffix can also be a tuple of strings to try.



.. method:: expandtabs()

   Return a copy where all tab characters are expanded using spaces.

   If tabsize is not given, a tab size of 8 characters is assumed.



.. method:: find()

   S.find(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: format()

   S.format(*args, **kwargs) -> str

   Return a formatted version of S, using substitutions from args and kwargs.
   The substitutions are identified by braces ('{' and '}').



.. method:: format_map()

   S.format_map(mapping) -> str

   Return a formatted version of S, using substitutions from mapping.
   The substitutions are identified by braces ('{' and '}').



.. method:: index()

   S.index(sub[, start[, end]]) -> int

   Return the lowest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: isalnum()

   Return True if the string is an alpha-numeric string, False otherwise.

   A string is alpha-numeric if all characters in the string are alpha-numeric and
   there is at least one character in the string.



.. method:: isalpha()

   Return True if the string is an alphabetic string, False otherwise.

   A string is alphabetic if all characters in the string are alphabetic and there
   is at least one character in the string.



.. method:: isascii()

   Return True if all characters in the string are ASCII, False otherwise.

   ASCII characters have code points in the range U+0000-U+007F.
   Empty string is ASCII too.



.. method:: isdecimal()

   Return True if the string is a decimal string, False otherwise.

   A string is a decimal string if all characters in the string are decimal and
   there is at least one character in the string.



.. method:: isdigit()

   Return True if the string is a digit string, False otherwise.

   A string is a digit string if all characters in the string are digits and there
   is at least one character in the string.



.. method:: isidentifier()

   Return True if the string is a valid Python identifier, False otherwise.

   Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
   such as "def" or "class".



.. method:: islower()

   Return True if the string is a lowercase string, False otherwise.

   A string is lowercase if all cased characters in the string are lowercase and
   there is at least one cased character in the string.



.. method:: isnumeric()

   Return True if the string is a numeric string, False otherwise.

   A string is numeric if all characters in the string are numeric and there is at
   least one character in the string.



.. method:: isprintable()

   Return True if all characters in the string are printable, False otherwise.

   A character is printable if repr() may use it in its output.



.. method:: isspace()

   Return True if the string is a whitespace string, False otherwise.

   A string is whitespace if all characters in the string are whitespace and there
   is at least one character in the string.



.. method:: istitle()

   Return True if the string is a title-cased string, False otherwise.

   In a title-cased string, upper- and title-case characters may only
   follow uncased characters and lowercase characters only cased ones.



.. method:: isupper()

   Return True if the string is an uppercase string, False otherwise.

   A string is uppercase if all cased characters in the string are uppercase and
   there is at least one cased character in the string.



.. method:: join()

   Concatenate any number of strings.

   The string whose method is called is inserted in between each given string.
   The result is returned as a new string.

   Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'



.. method:: ljust()

   Return a left-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: lower()

   Return a copy of the string converted to lowercase.



.. method:: lstrip()

   Return a copy of the string with leading whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: name()

   The name of the Enum member.



.. method:: partition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string.  If the separator is found,
   returns a 3-tuple containing the part before the separator, the separator
   itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing the original string
   and two empty strings.



.. method:: removeprefix()

   Return a str with the given prefix string removed if present.

   If the string starts with the prefix string, return string[len(prefix):].
   Otherwise, return a copy of the original string.



.. method:: removesuffix()

   Return a str with the given suffix string removed if present.

   If the string ends with the suffix string and that suffix is not empty,
   return string[:-len(suffix)]. Otherwise, return a copy of the original
   string.



.. method:: replace()

   Return a copy with all occurrences of substring old replaced by new.

     count
       Maximum number of occurrences to replace.
       -1 (the default value) means replace all occurrences.

   If the optional argument count is given, only the first count occurrences are
   replaced.



.. method:: rfind()

   S.rfind(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Return -1 on failure.



.. method:: rindex()

   S.rindex(sub[, start[, end]]) -> int

   Return the highest index in S where substring sub is found,
   such that sub is contained within S[start:end].  Optional
   arguments start and end are interpreted as in slice notation.

   Raises ValueError when the substring is not found.



.. method:: rjust()

   Return a right-justified string of length width.

   Padding is done using the specified fill character (default is a space).



.. method:: rpartition()

   Partition the string into three parts using the given separator.

   This will search for the separator in the string, starting at the end. If
   the separator is found, returns a 3-tuple containing the part before the
   separator, the separator itself, and the part after it.

   If the separator is not found, returns a 3-tuple containing two empty strings
   and the original string.



.. method:: rsplit()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the end of the string and works to the front.



.. method:: rstrip()

   Return a copy of the string with trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: split()

   Return a list of the substrings in the string, using sep as the separator string.

     sep
       The separator used to split the string.

       When set to None (the default value), will split on any whitespace
       character (including \n \r \t \f and spaces) and will discard
       empty strings from the result.
     maxsplit
       Maximum number of splits.
       -1 (the default value) means no limit.

   Splitting starts at the front of the string and works to the end.

   Note, str.split() is mainly useful for data that has been intentionally
   delimited.  With natural text that includes punctuation, consider using
   the regular expression module.



.. method:: splitlines()

   Return a list of the lines in the string, breaking at line boundaries.

   Line breaks are not included in the resulting list unless keepends is given and
   true.



.. method:: startswith()

   S.startswith(prefix[, start[, end]]) -> bool

   Return True if S starts with the specified prefix, False otherwise.
   With optional start, test S beginning at that position.
   With optional end, stop comparing S at that position.
   prefix can also be a tuple of strings to try.



.. method:: strip()

   Return a copy of the string with leading and trailing whitespace removed.

   If chars is given and not None, remove characters in chars instead.



.. method:: swapcase()

   Convert uppercase characters to lowercase and lowercase characters to uppercase.



.. method:: title()

   Return a version of the string where each word is titlecased.

   More specifically, words start with uppercased characters and all remaining
   cased characters have lower case.



.. method:: translate()

   Replace each character in the string using the given translation table.

     table
       Translation table, which must be a mapping of Unicode ordinals to
       Unicode ordinals, strings, or None.

   The table must implement lookup/indexing via __getitem__, for instance a
   dictionary or list.  If this operation raises LookupError, the character is
   left untouched.  Characters mapped to None are deleted.



.. method:: upper()

   Return a copy of the string converted to uppercase.



.. method:: value()

   The value of the Enum member.



.. method:: zfill()

   Pad a numeric string with zeros on the left, to fill a field of the given width.

   The string is never truncated.




ParameterMapping
~~~~~~~~~~~~~~~~

Mapping from control to parameter.


**Attributes:**

- **config** (attribute): 
- **control_name** (attribute): 
- **description** (attribute): 
- **function** (attribute): 
- **parameter_name** (attribute): 




