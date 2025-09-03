twin_model.scheduling.product_manifest
======================================

.. py:module:: twin_model.scheduling.product_manifest

.. autoapi-nested-parse::

   Product manifest loader and manager.

   This module provides comprehensive product information management
   for production scheduling and cost optimization.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.product_manifest.logger


Classes
-------

.. autoapisummary::

   twin_model.scheduling.product_manifest.PhysicalAttributes
   twin_model.scheduling.product_manifest.ProductionAttributes
   twin_model.scheduling.product_manifest.EconomicAttributes
   twin_model.scheduling.product_manifest.ChangeoverAttributes
   twin_model.scheduling.product_manifest.InventoryAttributes
   twin_model.scheduling.product_manifest.QualityAttributes
   twin_model.scheduling.product_manifest.ProductConstraints
   twin_model.scheduling.product_manifest.Product
   twin_model.scheduling.product_manifest.ProductManifest


Module Contents
---------------

.. py:data:: logger

.. py:class:: PhysicalAttributes

   Physical characteristics of a product.


   .. py:attribute:: volume_ml
      :type:  float


   .. py:attribute:: volume_oz
      :type:  float


   .. py:attribute:: container_type
      :type:  str


   .. py:attribute:: container_weight_g
      :type:  float


   .. py:attribute:: fill_weight_g
      :type:  float


   .. py:attribute:: package_size
      :type:  int


   .. py:attribute:: pallet_size
      :type:  int


   .. py:attribute:: case_dimensions_cm
      :type:  List[float]
      :value: []



   .. py:attribute:: gross_weight_kg
      :type:  float
      :value: 0.0



.. py:class:: ProductionAttributes

   Production characteristics and rates.


   .. py:attribute:: nominal_rate_per_min
      :type:  float


   .. py:attribute:: target_rate_5min
      :type:  float


   .. py:attribute:: quality_rate
      :type:  float


   .. py:attribute:: scrap_rate
      :type:  float


   .. py:attribute:: efficiency_by_line
      :type:  Dict[str, Optional[float]]


   .. py:attribute:: rework_possible
      :type:  bool
      :value: False



   .. py:attribute:: startup_waste_units
      :type:  int
      :value: 0



   .. py:attribute:: shutdown_waste_units
      :type:  int
      :value: 0



.. py:class:: EconomicAttributes

   Economic and cost attributes.


   .. py:attribute:: material_cost
      :type:  float


   .. py:attribute:: packaging_cost
      :type:  float


   .. py:attribute:: labor_cost
      :type:  float


   .. py:attribute:: overhead_cost
      :type:  float


   .. py:attribute:: total_standard_cost
      :type:  float


   .. py:attribute:: sale_price
      :type:  float


   .. py:attribute:: wholesale_price
      :type:  float


   .. py:attribute:: margin_percentage
      :type:  float


   .. py:attribute:: contribution_margin
      :type:  float


   .. py:attribute:: holding_cost_per_day
      :type:  float


   .. py:attribute:: obsolescence_cost
      :type:  float
      :value: 0.0



.. py:class:: ChangeoverAttributes

   Changeover requirements and costs.


   .. py:attribute:: group
      :type:  str


   .. py:attribute:: family
      :type:  str


   .. py:attribute:: cleaning_required_to
      :type:  Dict[str, bool]


   .. py:attribute:: setup_time_minutes
      :type:  Dict[str, float]


   .. py:attribute:: conversion_cost
      :type:  Dict[str, float]


.. py:class:: InventoryAttributes

   Inventory management parameters.


   .. py:attribute:: min_stock_units
      :type:  int


   .. py:attribute:: max_stock_units
      :type:  int


   .. py:attribute:: reorder_point
      :type:  int


   .. py:attribute:: reorder_quantity
      :type:  int


   .. py:attribute:: safety_stock
      :type:  int


   .. py:attribute:: shelf_life_days
      :type:  int


   .. py:attribute:: fifo_required
      :type:  bool


   .. py:attribute:: demand_pattern
      :type:  str


   .. py:attribute:: average_daily_demand
      :type:  float


   .. py:attribute:: demand_variability
      :type:  float


   .. py:attribute:: seasonal_factors
      :type:  Dict[str, float]


.. py:class:: QualityAttributes

   Quality specifications and defect costs.


   .. py:attribute:: critical_parameters
      :type:  List[str]
      :value: []



   .. py:attribute:: specification_limits
      :type:  Dict[str, List[float]]


   .. py:attribute:: defect_categories
      :type:  Dict[str, Dict[str, Any]]


   .. py:attribute:: inspection_time_seconds
      :type:  float
      :value: 0.0



   .. py:attribute:: sampling_rate
      :type:  float
      :value: 0.01



.. py:class:: ProductConstraints

   Production constraints and requirements.


   .. py:attribute:: max_continuous_run_hours
      :type:  float


   .. py:attribute:: min_batch_size
      :type:  int


   .. py:attribute:: max_batch_size
      :type:  int


   .. py:attribute:: optimal_batch_size
      :type:  int


   .. py:attribute:: requires_quality_check_interval
      :type:  int


   .. py:attribute:: temperature_range_celsius
      :type:  List[float]
      :value: []



   .. py:attribute:: humidity_range_percent
      :type:  List[float]
      :value: []



   .. py:attribute:: requires_allergen_control
      :type:  bool
      :value: False



.. py:class:: Product

   Complete product specification.


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: category
      :type:  str


   .. py:attribute:: family
      :type:  str


   .. py:attribute:: status
      :type:  str


   .. py:attribute:: physical
      :type:  PhysicalAttributes


   .. py:attribute:: production
      :type:  ProductionAttributes


   .. py:attribute:: economics
      :type:  EconomicAttributes


   .. py:attribute:: changeover
      :type:  ChangeoverAttributes


   .. py:attribute:: inventory
      :type:  InventoryAttributes


   .. py:attribute:: quality
      :type:  QualityAttributes


   .. py:attribute:: constraints
      :type:  ProductConstraints


   .. py:attribute:: line_compatibility
      :type:  Dict[str, Dict[str, Any]]


.. py:class:: ProductManifest(manifest_path: Optional[pathlib.Path] = None)

   Manages product specifications and relationships.


   .. py:attribute:: products
      :type:  Dict[str, Product]


   .. py:attribute:: product_families
      :type:  Dict[str, Dict[str, Any]]


   .. py:attribute:: changeover_matrix_overrides
      :type:  Dict[str, Dict[str, Dict[str, Any]]]


   .. py:attribute:: cost_factors
      :type:  Dict[str, float]


   .. py:attribute:: performance_targets
      :type:  Dict[str, float]


   .. py:method:: load_from_yaml(filepath: pathlib.Path) -> None

      Load product manifest from YAML file.

      :param filepath: Path to YAML file



   .. py:method:: get_product(product_id: str) -> Optional[Product]

      Get product by ID.

      :param product_id: Product identifier

      :returns: Product object or None if not found



   .. py:method:: get_changeover_time(from_product_id: str, to_product_id: str) -> float

      Get changeover time between products.

      :param from_product_id: Current product
      :param to_product_id: Next product

      :returns: Changeover time in minutes



   .. py:method:: get_changeover_cost(from_product_id: str, to_product_id: str) -> float

      Get changeover cost between products.

      :param from_product_id: Current product
      :param to_product_id: Next product

      :returns: Changeover cost in currency units



   .. py:method:: get_line_efficiency(product_id: str, line_id: str) -> Optional[float]

      Get efficiency of product on specific line.

      :param product_id: Product identifier
      :param line_id: Line identifier (e.g., "Line1", "1", etc.)

      :returns: Efficiency factor (0-1) or None if not capable



   .. py:method:: is_product_capable_on_line(product_id: str, line_id: str) -> bool

      Check if product can be produced on line.

      :param product_id: Product identifier
      :param line_id: Line identifier

      :returns: True if capable, False otherwise



   .. py:method:: get_preferred_line(product_id: str) -> Optional[str]

      Get preferred production line for product.

      :param product_id: Product identifier

      :returns: Preferred line ID or None



   .. py:method:: get_product_family_members(family: str) -> List[str]

      Get all products in a family.

      :param family: Family name

      :returns: List of product IDs in the family



   .. py:method:: calculate_campaign_cost(product_id: str, volume: float, duration_hours: float, line_id: str) -> Dict[str, float]

      Calculate total cost of a production campaign.

      :param product_id: Product to produce
      :param volume: Production volume in units
      :param duration_hours: Campaign duration in hours
      :param line_id: Production line

      :returns: Dictionary of cost components



   .. py:method:: get_summary() -> Dict[str, Any]

      Get summary of loaded products.

      :returns: Summary dictionary



