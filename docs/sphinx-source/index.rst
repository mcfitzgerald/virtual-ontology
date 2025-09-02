Twin Model Documentation
========================

Twin Model is an ontology-driven simulation framework for manufacturing systems using SimPy containers.

Key Features
------------

* **Ontology-driven architecture** - Separates structure, instances, and parameters
* **Container-based flow simulation** - Continuous material flow with SimPy
* **Real-time monitoring** - Track OEE, throughput, and quality metrics
* **Flexible configuration** - YAML-based configuration system

Architecture Overview
--------------------

The system uses three configuration files:

1. **Ontology** (``ontology.yaml``) - Defines equipment types and their properties
2. **Manifest** (``manifest.yaml``) - Declares equipment instances and topology
3. **Config** (``config.yaml``) - Contains tunable simulation parameters

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   ontology_guide
   api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`