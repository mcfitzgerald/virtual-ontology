twin_model.transduction.mes_transducer
======================================

MES Transduction Layer.

This module converts rich SimPy observables into MES-compatible data format
matching the structure of mes_data_with_kpis.csv. It extracts the subset
of information visible to a real MES system from comprehensive simulation events.


Classes
-------

MESTransducer
~~~~~~~~~~~~~

Converts SimPy observables to MES data format.

The transducer extracts MES-visible events from the comprehensive
observable stream and formats them into the standard MES structure.

Initialize MES transducer.

:param time_bucket: Time bucket in minutes (default 5 for 5-minute intervals)


**Attributes:**

- **bucket_metrics** (attribute): 
- **equipment_states** (attribute): 
- **mes_records** (attribute): 
- **time_bucket** (attribute): 

**Methods:**

.. method:: __init__(time_bucket: int = 5)

   Initialize MES transducer.

   :param time_bucket: Time bucket in minutes (default 5 for 5-minute intervals)



.. method:: _calculate_availability(metrics: Dict[str, Any])

   Calculate availability score.

   :param metrics: Bucket metrics

   :returns: Availability percentage



.. method:: _calculate_performance(metrics: Dict[str, Any], equipment_info: Dict[str, Any], product_info: Dict[str, Any])

   Calculate performance score with safety checks.

   :param metrics: Bucket metrics
   :param equipment_info: Equipment manifest data
   :param product_info: Product manifest data

   :returns: Performance percentage



.. method:: _calculate_quality(metrics: Dict[str, Any])

   Calculate quality score.

   :param metrics: Bucket metrics

   :returns: Quality percentage



.. method:: _determine_equipment_type(equipment_id: str, equipment_info: Dict[str, Any])

   Determine equipment type from ID or manifest.

   :param equipment_id: Equipment identifier
   :param equipment_info: Equipment manifest data

   :returns: Equipment type string



.. method:: _extract_line_id(equipment_id: str, equipment_info: Dict[str, Any])

   Extract line ID from equipment ID or manifest.

   :param equipment_id: Equipment identifier
   :param equipment_info: Equipment manifest data

   :returns: Line ID



.. method:: _generate_mes_records(manifests: Optional[Dict[str, Any]] = None)

   Generate MES records from bucket metrics.

   :param manifests: Optional manifests for equipment details

   :returns: List of MES records



.. method:: _get_product_name(product_id: str, manifests: Optional[Dict[str, Any]] = None)

   Get product name from manifests.

   :param product_id: Product identifier
   :param manifests: Optional manifests

   :returns: Product name



.. method:: _map_state_to_mes(state: str)

   Map SimPy state to MES status.

   :param state: SimPy equipment state

   :returns: MES machine status



.. method:: _process_equipment_event(obs: Dict[str, Any], bucket_key: Tuple[int, str], manifests: Optional[Dict[str, Any]] = None)

   Process equipment-specific events.

   :param obs: Equipment observable
   :param bucket_key: Time bucket and equipment ID
   :param manifests: Optional manifests



.. method:: _process_observable(obs: Dict[str, Any], manifests: Optional[Dict[str, Any]] = None)

   Process single observable event.

   :param obs: Observable event
   :param manifests: Optional manifests for context



.. method:: _process_order_assignment(obs: Dict[str, Any], bucket_key: Tuple[int, str])

   Process order assignment events.

   :param obs: Order assignment observable
   :param bucket_key: Time bucket and equipment ID



.. method:: generate_summary_statistics(df: pandas.DataFrame)

   Generate summary statistics from MES data.

   :param df: MES DataFrame

   :returns: Dictionary of summary statistics



.. method:: process_observables(observables: List[Dict[str, Any]], manifests: Optional[Dict[str, Any]] = None)

   Process observables into MES format.

   :param observables: List of observable events from simulation
   :param manifests: Optional manifests for product/equipment details

   :returns: DataFrame in MES format



.. method:: save_to_csv(df: pandas.DataFrame, filepath: pathlib.Path)

   Save MES data to CSV file.

   :param df: MES DataFrame
   :param filepath: Output file path






