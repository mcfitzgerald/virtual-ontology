twin_model.transduction.mes_collector
=====================================

.. py:module:: twin_model.transduction.mes_collector

.. autoapi-nested-parse::

   MES Data Collector for capturing simulation events in MES format.

   This module provides a data collector that captures simulation events
   and formats them according to MES (Manufacturing Execution System) standards.



Attributes
----------

.. autoapisummary::

   twin_model.transduction.mes_collector.logger


Classes
-------

.. autoapisummary::

   twin_model.transduction.mes_collector.MESRecord
   twin_model.transduction.mes_collector.ProductInfo
   twin_model.transduction.mes_collector.MESDataCollector


Module Contents
---------------

.. py:data:: logger

.. py:class:: MESRecord

   Single MES data record for a 5-minute interval.


   .. py:attribute:: timestamp
      :type:  datetime.datetime


   .. py:attribute:: production_order_id
      :type:  str


   .. py:attribute:: line_id
      :type:  str


   .. py:attribute:: equipment_id
      :type:  str


   .. py:attribute:: equipment_type
      :type:  str


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: product_name
      :type:  str


   .. py:attribute:: machine_status
      :type:  str


   .. py:attribute:: downtime_reason
      :type:  Optional[str]


   .. py:attribute:: good_units_produced
      :type:  float


   .. py:attribute:: scrap_units_produced
      :type:  float


   .. py:attribute:: target_rate_units_per_5min
      :type:  float


   .. py:attribute:: standard_cost_per_unit
      :type:  float


   .. py:attribute:: sale_price_per_unit
      :type:  float


   .. py:attribute:: availability_score
      :type:  float


   .. py:attribute:: performance_score
      :type:  float


   .. py:attribute:: quality_score
      :type:  float


   .. py:attribute:: oee_score
      :type:  float


.. py:class:: ProductInfo

   Product information for MES records.


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: product_name
      :type:  str


   .. py:attribute:: standard_cost
      :type:  float


   .. py:attribute:: sale_price
      :type:  float


   .. py:attribute:: target_rate
      :type:  float


.. py:class:: MESDataCollector(env: simpy.Environment, interval_minutes: float = 5.0, start_date: Optional[datetime.datetime] = None)

   Collects simulation data and formats it for MES output.

   This collector monitors equipment primitives and captures their state
   and production metrics at regular intervals (default 5 minutes).


   .. py:attribute:: env


   .. py:attribute:: interval
      :value: 5.0



   .. py:attribute:: start_date


   .. py:attribute:: records
      :type:  List[MESRecord]
      :value: []



   .. py:attribute:: equipment_registry
      :type:  Dict[str, twin_model.primitives.base_flow.BaseFlowPrimitive]


   .. py:attribute:: product_info
      :type:  Dict[str, ProductInfo]


   .. py:attribute:: interval_start_metrics
      :type:  Dict[str, Dict[str, Any]]


   .. py:attribute:: current_order
      :type:  Dict[str, str]


   .. py:attribute:: current_product
      :type:  Dict[str, str]


   .. py:method:: register_equipment(equipment_id: str, equipment: twin_model.primitives.base_flow.BaseFlowPrimitive, equipment_type: str, line_id: str)

      Register equipment for monitoring.

      :param equipment_id: Unique equipment identifier
      :param equipment: Equipment primitive to monitor
      :param equipment_type: Type (Filler, Packer, Palletizer)
      :param line_id: Production line ID



   .. py:method:: update_production_order(equipment_id: str, order_id: str, product_id: str)

      Update current production order for equipment.

      :param equipment_id: Equipment identifier
      :param order_id: Production order ID
      :param product_id: Product being produced



   .. py:method:: collect_data()

      Collect data at regular intervals (coroutine).



   .. py:method:: to_dataframe() -> pandas.DataFrame

      Convert collected records to pandas DataFrame.

      :returns: DataFrame with MES records



   .. py:method:: save_to_csv(filepath: pathlib.Path)

      Save collected data to CSV file.

      :param filepath: Path to save CSV file



   .. py:method:: get_summary() -> Dict[str, Any]

      Get summary statistics of collected data.

      :returns: Dictionary with summary statistics



