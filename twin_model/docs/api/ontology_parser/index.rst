ontology_parser
===============

.. py:module:: ontology_parser

.. autoapi-nested-parse::

   Ontology Parser Module
   Parses YAML ontology specifications and extracts classes, relationships, properties, and business rules.



Classes
-------

.. autoapisummary::

   ontology_parser.OntologyParser


Module Contents
---------------

.. py:class:: OntologyParser(mes_path: str, twin_path: str)

   
   Initialize the parser with paths to ontology files.


   .. py:attribute:: mes_path


   .. py:attribute:: twin_path


   .. py:attribute:: mes_ontology
      :value: None



   .. py:attribute:: twin_ontology
      :value: None



   .. py:method:: load_ontologies() -> Tuple[Dict, Dict]

      Load both ontology YAML files with enhanced error handling.



   .. py:method:: extract_classes(ontology: Dict, namespace: str) -> List[Dict]

      Extract all classes from an ontology.



   .. py:method:: extract_relationships(ontology: Dict, namespace: str) -> List[Dict]

      Extract all relationships from an ontology.



   .. py:method:: extract_properties(ontology: Dict, namespace: str) -> List[Dict]

      Extract all properties from an ontology.



   .. py:method:: extract_business_rules(ontology: Dict, namespace: str) -> List[Dict]

      Extract all business rules from an ontology.



   .. py:method:: extract_common_queries(ontology: Dict, namespace: str) -> List[Dict]

      Extract common queries from an ontology.



   .. py:method:: extract_glossary(ontology: Dict, namespace: str) -> Dict

      Extract glossary terms from an ontology.



   .. py:method:: parse_all() -> Dict

      Parse both ontologies and extract all components.



