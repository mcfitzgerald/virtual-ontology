{{ obj.name }}
{{ "=" * obj.name|length }}

.. class:: {{ obj.name }}{% if obj.bases %}({{ obj.bases|join(", ") }}){% endif %}

{% if obj.docstring %}
   {{ obj.docstring|indent(3) }}
{% endif %}

{% if obj.attributes %}
   **Attributes:**

{% for attr in obj.attributes %}
   .. attribute:: {{ attr.name }}
      :type: {{ attr.type|default("Any") }}

      {% if attr.docstring %}
      {{ attr.docstring|indent(6) }}
      {% endif %}

{% endfor %}
{% endif %}

{% if obj.methods %}
   **Methods:**

{% for method in obj.methods %}
   .. method:: {{ method.name }}({{ method.args }})

      {% if method.docstring %}
      {{ method.docstring|indent(6) }}
      {% endif %}

      {% if method.returns %}
      :returns: {{ method.returns }}
      {% endif %}

      {% if method.raises %}
      :raises: {{ method.raises }}
      {% endif %}

{% endfor %}
{% endif %}