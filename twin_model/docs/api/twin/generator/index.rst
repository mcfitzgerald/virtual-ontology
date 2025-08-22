twin.generator
==============

.. py:module:: twin.generator

.. autoapi-nested-parse::

   Virtual Twin Data Generator Module
   Generates manufacturing data with realistic OEE values based on configuration
   Part of the Virtual Twin system for both baseline and simulation data generation



Functions
---------

.. autoapisummary::

   twin.generator.load_config
   twin.generator.apply_scaling_factors
   twin.generator.get_product_master
   twin.generator.get_equipment_master
   twin.generator.get_downtime_reasons
   twin.generator.generate_production_orders
   twin.generator.get_shift_number
   twin.generator.apply_anomalies
   twin.generator.calculate_kpis
   twin.generator.calculate_energy_consumption
   twin.generator.save_to_csv
   twin.generator.save_to_database
   twin.generator.generate_mes_data
   twin.generator.main


Module Contents
---------------

.. py:function:: load_config(config_file: str = 'mes_data_config.json') -> Dict[str, Any]

   Load configuration from JSON or YAML file.

   :param config_file: Path to configuration file (JSON or YAML)

   :returns: Configuration dictionary


.. py:function:: apply_scaling_factors(config: Dict[str, Any]) -> Dict[str, Any]

   Apply scaling parameters to baseline values if present.

   :param config: Raw configuration dictionary

   :returns: Configuration with scaled values


.. py:function:: get_product_master(config)

   Returns a DataFrame of product master data from configuration.


.. py:function:: get_equipment_master(config)

   Returns a DataFrame of equipment master data from configuration.


.. py:function:: get_downtime_reasons(config)

   Returns a map of downtime reason codes and descriptions from configuration.


.. py:function:: generate_production_orders(products_df, start_date, end_date, config)

   Generates a list of production orders for each line using configuration.


.. py:function:: get_shift_number(current_time)

   Determine shift number based on time (1: 6am-2pm, 2: 2pm-10pm, 3: 10pm-6am)


.. py:function:: apply_anomalies(equip_id, current_time, order_info, config, changeover_start_times, performance_drop_tracker, last_cleaning_times)

   Apply configured anomalies to determine equipment status and production rates.


.. py:function:: calculate_kpis(status, good_units, scrap_units, target_rate)

   Calculate instantaneous KPIs for 5-minute intervals.


.. py:function:: calculate_energy_consumption(status, equipment_type, product_id, performance_score, config, is_micro_stop=False)

   Calculate energy consumption for 5-minute interval based on equipment status and performance.

   NOTE: This function is preserved for use by the virtual sensor layer.
   Energy is no longer stored as raw data in MES/simulation tables, but is instead
   derived as an observation by the PowerMeterSensor in virtual_sensors.py.

   :param status: Machine status (Running/Stopped)
   :param equipment_type: Type of equipment (Filler/Packer/Palletizer)
   :param product_id: Product being produced
   :param performance_score: Performance percentage (0-100)
   :param config: Configuration dictionary with energy parameters
   :param is_micro_stop: Whether this is a micro-stop (uses surge power)

   :returns: Energy consumption in kWh for the 5-minute interval


.. py:function:: save_to_csv(df, filename=None)

   Save DataFrame to CSV file.

   :param df: DataFrame to save
   :param filename: Optional filename, defaults to timestamped name

   :returns: Path to saved CSV file
   :rtype: str


.. py:function:: save_to_database(df, table_name, run_id=None)

   Save DataFrame to database table


.. py:function:: generate_mes_data(start_date, end_date, config)

   Main function to generate the complete MES dataset with inline KPIs.


.. py:function:: main()

   Main execution function.


