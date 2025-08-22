twin.twin_state
===============

.. py:module:: twin.twin_state

.. autoapi-nested-parse::

   Twin State Management
   Manages the current state of the virtual twin and run ledger



Classes
-------

.. autoapisummary::

   twin.twin_state.TwinState
   twin.twin_state.TwinStateManager


Module Contents
---------------

.. py:class:: TwinState

   Current state of the virtual twin


   .. py:attribute:: current_run_id
      :type:  str


   .. py:attribute:: baseline_run_id
      :type:  str


   .. py:attribute:: last_update
      :type:  datetime.datetime


   .. py:attribute:: current_parameters
      :type:  Dict[str, float]


   .. py:attribute:: current_kpis
      :type:  Dict[str, float]


   .. py:attribute:: sync_status
      :type:  Dict[str, str]


   .. py:attribute:: active_recommendations
      :type:  List[Dict[str, Any]]


   .. py:attribute:: confidence_intervals
      :type:  Dict[str, Tuple[float, float]]


.. py:class:: TwinStateManager(db_path: Optional[str] = None)

   Manages virtual twin state and provides high-level operations
   for querying, comparing, and optimizing the twin

   Initialize the TwinStateManager.

   :param db_path: Path to SQLite database. If None, uses path from configuration.

   :raises KeyError: If database path not found in configuration.


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: module_config


   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:method:: get_current_state() -> Optional[TwinState]

      Get the current state of the virtual twin



   .. py:method:: update_state(run_id: str, baseline_run_id: Optional[str] = None, notes: Optional[str] = None) -> None

      Update the twin state based on a simulation run

      :param run_id: Run ID to set as current state
      :param baseline_run_id: Optional baseline for comparison
      :param notes: Optional notes about the state change



   .. py:method:: calculate_confidence(run_id: str, n_validation_runs: Optional[int] = None, confidence_level: Optional[float] = None) -> None

      Calculate confidence intervals for KPIs using validation runs

      :param run_id: Base run to validate
      :param n_validation_runs: Number of validation runs (uses config if None)
      :param confidence_level: Confidence level (uses config if None)



   .. py:method:: create_recommendation(parameters: Dict[str, float], expected_improvement: Dict[str, float], recommendation_type: str = 'optimization', confidence: float = 0.0, notes: Optional[str] = None) -> int

      Create a new recommendation

      :param parameters: Recommended parameter values
      :param expected_improvement: Expected KPI improvements
      :param recommendation_type: Type of recommendation
      :param confidence: Confidence in recommendation (0-1)
      :param notes: Optional notes

      :returns: Recommendation ID



   .. py:method:: accept_recommendation(recommendation_id: int) -> Dict[str, float]

      Accept a recommendation and return its parameters

      :param recommendation_id: ID of recommendation to accept

      :returns: Parameter values from the recommendation



   .. py:method:: get_improvement_trends(n_runs: int = 10) -> Dict[str, List[float]]

      Get KPI improvement trends over recent runs

      :param n_runs: Number of recent runs to analyze

      :returns: Dictionary of KPI trends



   .. py:method:: generate_state_report() -> str

      Generate a comprehensive state report



