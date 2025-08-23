twin_model.transduction
=======================

.. py:module:: twin_model.transduction

.. autoapi-nested-parse::

   Transduction layer for converting SimPy observables to MES format.

   This module provides the transduction layer that extracts MES-visible
   information from the comprehensive SimPy event stream.



Submodules
----------

.. toctree::
   :maxdepth: 1

   /api/twin_model/transduction/mes_transducer/index


Classes
-------

.. autoapisummary::

   twin_model.transduction.MESTransducer


Package Contents
----------------

.. py:class:: MESTransducer(time_bucket = 5)

   Converts SimPy observables to MES data format.

   The transducer extracts MES-visible events from the comprehensive
   observable stream and formats them into the standard MES structure.


   .. py:attribute:: time_bucket
      :value: 5



   .. py:attribute:: mes_records
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:attribute:: equipment_states
      :type:  Dict[str, Dict[str, Any]]


   .. py:attribute:: bucket_metrics
      :type:  Dict[Tuple[int, str], Dict[str, Any]]


   .. py:method:: process_observables(observables, manifests = None)

      Process observables into MES format.

      :param observables: List of observable events from simulation
      :param manifests: Optional manifests for product/equipment details

      :returns: DataFrame in MES format



   .. py:method:: save_to_csv(df, filepath)

      Save MES data to CSV file.

      :param df: MES DataFrame
      :param filepath: Output file path



   .. py:method:: generate_summary_statistics(df)

      Generate summary statistics from MES data.

      :param df: MES DataFrame

      :returns: Dictionary of summary statistics



