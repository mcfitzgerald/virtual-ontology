twin_model.ontology_model_builder
=================================

.. py:module:: twin_model.ontology_model_builder

.. autoapi-nested-parse::

   Ontology-driven model builder for twin simulation.

   This module builds simulation models using:
   - Ontology for structure and validation
   - Manifests for equipment instances
   - Config for tunable parameters



Attributes
----------

.. autoapisummary::

   twin_model.ontology_model_builder.logger


Classes
-------

.. autoapisummary::

   twin_model.ontology_model_builder.OntologyModelBuilder


Module Contents
---------------

.. py:data:: logger

.. py:class:: OntologyModelBuilder(env: simpy.Environment, ontology_path: pathlib.Path, manifest_path: pathlib.Path, config_path: pathlib.Path)

   Builds simulation models from ontology, manifests, and config.


   .. py:attribute:: env


   .. py:attribute:: ontology


   .. py:attribute:: manifest


   .. py:attribute:: config


   .. py:attribute:: primitives
      :type:  Dict[str, Any]


   .. py:attribute:: connections
      :type:  List[Dict[str, str]]
      :value: []



   .. py:method:: build_model() -> Dict[str, Any]

      Build complete simulation model.

      :returns: Dictionary containing primitives and metadata



   .. py:method:: get_metrics() -> Dict[str, Any]

      Get current metrics from all equipment.

      :returns: Dictionary of metrics by equipment



