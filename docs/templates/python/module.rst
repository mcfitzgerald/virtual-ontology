{{ obj.name }}
{{ "=" * obj.name|length }}

{% if obj.docstring %}
{{ obj.docstring }}
{% endif %}

{% if obj.classes %}
Classes
-------

{% for class in obj.classes %}
{{ class.name }}
{{ "~" * class.name|length }}

{% if class.docstring %}
{{ class.docstring }}
{% endif %}

{% if class.attributes %}
**Attributes:**

{% for attr in class.attributes %}
- **{{ attr.name }}** ({{ attr.type|default("Any") }}): {{ attr.docstring|default("") }}
{% endfor %}
{% endif %}

{% if class.methods %}
**Methods:**

{% for method in class.methods %}
.. method:: {{ method.name }}({{ method.args }})

   {% if method.docstring %}
   {{ method.docstring|indent(3) }}
   {% endif %}

   {% if method.returns %}
   **Returns:** {{ method.returns }}
   {% endif %}

{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

{% if obj.functions %}
Functions
---------

{% for func in obj.functions %}
.. function:: {{ func.name }}({{ func.args }})

   {% if func.docstring %}
   {{ func.docstring|indent(3) }}
   {% endif %}

   {% if func.returns %}
   **Returns:** {{ func.returns }}
   {% endif %}

{% endfor %}
{% endif %}

{% if obj.attributes %}
Module Attributes
-----------------

{% for attr in obj.attributes %}
- **{{ attr.name }}** ({{ attr.type|default("Any") }}): {{ attr.docstring|default("") }}
{% endfor %}
{% endif %}