app
===

.. py:module:: app

.. autoapi-nested-parse::

   Ontology Knowledge Graph Visualization Dashboard
   Main Dash application for interactive ontology exploration.



Attributes
----------

.. autoapisummary::

   app.app
   app.parser
   app.ontology_data
   app.builder
   app.graph
   app.elements
   app.node_types
   app.namespaces


Functions
---------

.. autoapisummary::

   app.filter_elements
   app.update_graph
   app.select_node
   app.update_detail_panel
   app.highlight_connected
   app.handle_export


Module Contents
---------------

.. py:data:: app

.. py:data:: parser

.. py:data:: ontology_data

.. py:data:: builder

.. py:data:: graph

.. py:data:: elements

.. py:data:: node_types

.. py:data:: namespaces

.. py:function:: filter_elements(namespace, node_types_selected, search_term)

   Filter graph elements based on user selections.


.. py:function:: update_graph(filtered_elements, layout_name, display_options)

   Update graph elements and layout.


.. py:function:: select_node(node_data)

   Store selected node data.


.. py:function:: update_detail_panel(node_data)

   Update the detail panel with selected node information.


.. py:function:: highlight_connected(selected_node, display_options, current_elements)

   Highlight selected node and its connections.


.. py:function:: handle_export(image_clicks, pyvis_clicks, obsidian_clicks, elements)

   Handle export button clicks.


