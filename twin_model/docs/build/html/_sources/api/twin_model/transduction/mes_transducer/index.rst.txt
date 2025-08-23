twin_model.transduction.mes_transducer
======================================

.. py:module:: twin_model.transduction.mes_transducer

.. autoapi-nested-parse::

   MES Transduction Layer.

   This module converts rich SimPy observables into MES-compatible data format
   matching the structure of mes_data_with_kpis.csv. It extracts the subset
   of information visible to a real MES system from comprehensive simulation events.



Attributes
----------

.. autoapisummary::

   twin_model.transduction.mes_transducer.logger


Classes
-------

.. autoapisummary::

   twin_model.transduction.mes_transducer.MESTransducer


Module Contents
---------------

.. py:data:: logger

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



