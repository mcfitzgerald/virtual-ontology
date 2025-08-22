graph_builder
=============

.. py:module:: graph_builder

.. autoapi-nested-parse::

   Graph Builder Module
   Constructs NetworkX graph from parsed ontology data and prepares it for visualization.



Classes
-------

.. autoapisummary::

   graph_builder.GraphBuilder


Module Contents
---------------

.. py:class:: GraphBuilder(ontology_data: Dict)

   
   Initialize with parsed ontology data.


   .. py:attribute:: data


   .. py:attribute:: graph


   .. py:attribute:: class_registry


   .. py:method:: build_graph() -> networkx.DiGraph

      Build the complete graph from ontology data.



   .. py:method:: get_cytoscape_elements() -> List[Dict]

      Convert NetworkX graph to Cytoscape elements format.



   .. py:method:: get_node_types() -> List[str]

      Get all unique node types in the graph.



   .. py:method:: get_namespaces() -> List[str]

      Get all unique namespaces in the graph.



