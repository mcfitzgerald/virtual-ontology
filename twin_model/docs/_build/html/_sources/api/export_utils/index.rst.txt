export_utils
============

.. py:module:: export_utils

.. autoapi-nested-parse::

   Export Utilities Module
   Provides functions to export the graph in various formats.



Functions
---------

.. autoapisummary::

   export_utils.export_to_pyvis
   export_utils.export_to_obsidian


Module Contents
---------------

.. py:function:: export_to_pyvis(elements: List[Dict]) -> str

   Export Cytoscape elements to an interactive PyVis HTML string.

   :param elements: List of Cytoscape elements (nodes and edges)

   :returns: HTML string containing the PyVis visualization


.. py:function:: export_to_obsidian(elements: List[Dict], ontology_data: Dict = None) -> bytes

   Export Cytoscape elements to Obsidian-compatible markdown files as a zip.

   :param elements: List of Cytoscape elements
   :param ontology_data: Optional original ontology data for richer export

   :returns: Bytes of zip file containing Obsidian vault


