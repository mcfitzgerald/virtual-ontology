twin_model.model_builder
========================

.. py:module:: twin_model.model_builder

.. autoapi-nested-parse::

   Ontology-driven model builder for SimPy simulations.

   This module builds SimPy models from the twin ontology structure and manifests.
   It interprets the ontology to instantiate primitives, wire relationships,
   and configure values from manifests.



Classes
-------

.. autoapisummary::

   twin_model.model_builder.ModelEntity
   twin_model.model_builder.OntologyDrivenModelBuilder


Module Contents
---------------

.. py:class:: ModelEntity

   Represents an entity to be instantiated in the model.

   .. attribute:: id

      Unique identifier

   .. attribute:: ontology_class

      Class name from ontology

   .. attribute:: primitive_type

      Primitive class to instantiate

   .. attribute:: properties

      Configuration properties

   .. attribute:: relationships

      Entity relationships


   .. py:attribute:: id
      :type:  str


   .. py:attribute:: ontology_class
      :type:  str


   .. py:attribute:: primitive_type
      :type:  str


   .. py:attribute:: properties
      :type:  Dict[str, Any]


   .. py:attribute:: relationships
      :type:  Dict[str, List[str]]


.. py:class:: OntologyDrivenModelBuilder(ontology_path, manifest_dir = None)

   Builds SimPy models from ontology structure and manifests.

   This builder interprets the twin ontology to construct a simulation model,
   then configures it with values from manifests. It maintains separation
   between structure (ontology) and configuration (manifests).


   .. py:attribute:: PRIMITIVE_CLASSES


   .. py:attribute:: ontology_path


   .. py:attribute:: manifest_dir
      :value: None



   .. py:attribute:: ontology


   .. py:attribute:: manifests


   .. py:attribute:: entities
      :type:  Dict[str, ModelEntity]


   .. py:attribute:: primitives
      :type:  Dict[str, twin_model.primitives.BasePrimitive]


   .. py:attribute:: production_lines
      :type:  Dict[str, Dict[str, Any]]


   .. py:method:: build_model(env)

      Build complete simulation model from ontology.

      :param env: SimPy environment for the model

      :returns:     - primitives: Instantiated primitive objects
                    - lines: Production line configurations
                    - scheduler: Scheduler primitive if created
                    - monitor: Monitor primitive if created
      :rtype: Dictionary containing



   .. py:method:: get_controllable_parameters()

      Get controllable parameters from ontology.

      :returns: Dictionary of parameter names to definitions



   .. py:method:: apply_parameter_changes(parameters)

      Apply parameter changes to running model.

      :param parameters: Dictionary of parameter name to value



   .. py:method:: get_observables()

      Get all observables from primitives.

      :returns: Dictionary of primitive ID to observable list



   .. py:method:: get_model_structure()

      Get model structure for analysis.

      :returns: Dictionary describing model structure



