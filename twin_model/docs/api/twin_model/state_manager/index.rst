twin_model.state_manager
========================

.. py:module:: twin_model.state_manager

.. autoapi-nested-parse::

   State persistence and management for simulation pause/resume.

   This module provides functionality to save and restore simulation state,
   enabling pause/resume capabilities and recovery from interruptions.



Classes
-------

.. autoapisummary::

   twin_model.state_manager.SimulationCheckpoint
   twin_model.state_manager.StateManager
   twin_model.state_manager.SimulationRunner


Module Contents
---------------

.. py:class:: SimulationCheckpoint

   Represents a saved simulation state checkpoint.

   Stores all necessary information to restore a simulation
   from a specific point in time.

   .. attribute:: checkpoint_id

      Unique identifier for this checkpoint

   .. attribute:: simulation_time

      Current simulation time when saved

   .. attribute:: real_time

      Real-world timestamp when saved

   .. attribute:: primitives_state

      Serialized state of all primitives

   .. attribute:: environment_state

      SimPy environment state

   .. attribute:: cache_path

      Path to associated event cache

   .. attribute:: metadata

      Additional checkpoint metadata


   .. py:attribute:: checkpoint_id
      :type:  str


   .. py:attribute:: simulation_time
      :type:  float


   .. py:attribute:: real_time
      :type:  datetime.datetime


   .. py:attribute:: primitives_state
      :type:  Dict[str, Any]


   .. py:attribute:: environment_state
      :type:  Dict[str, Any]


   .. py:attribute:: cache_path
      :type:  Optional[str]


   .. py:attribute:: metadata
      :type:  Dict[str, Any]


   .. py:method:: to_file(filepath: pathlib.Path) -> None

      Save checkpoint to file.

      :param filepath: Path to save checkpoint file



   .. py:method:: from_file(filepath: pathlib.Path) -> SimulationCheckpoint
      :classmethod:


      Load checkpoint from file.

      :param filepath: Path to checkpoint file

      :returns: Loaded checkpoint instance



   .. py:method:: get_summary() -> Dict[str, Any]

      Get human-readable checkpoint summary.

      :returns: Dictionary with checkpoint summary information



.. py:class:: StateManager(checkpoint_dir: str = 'checkpoints', max_checkpoints: int = 10, compression: bool = True)

   Manages simulation state persistence and recovery.

   Provides methods to save simulation state at checkpoints,
   restore from saved states, and manage checkpoint lifecycle.

   .. attribute:: checkpoint_dir

      Directory for storing checkpoints

   .. attribute:: max_checkpoints

      Maximum number of checkpoints to retain

   .. attribute:: compression

      Whether to compress checkpoint files

   .. attribute:: checkpoints

      List of available checkpoints

   Initialize state manager.

   :param checkpoint_dir: Directory for checkpoint storage
   :param max_checkpoints: Maximum checkpoints to retain
   :param compression: Enable checkpoint compression


   .. py:attribute:: checkpoint_dir


   .. py:attribute:: max_checkpoints
      :value: 10



   .. py:attribute:: compression
      :value: True



   .. py:attribute:: checkpoints
      :type:  List[str]


   .. py:method:: save_checkpoint(env: simpy.Environment, primitives: Dict[str, Any], cache_path: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str

      Save current simulation state as checkpoint.

      :param env: SimPy environment
      :param primitives: Dictionary of primitive instances
      :param cache_path: Optional path to event cache
      :param metadata: Optional checkpoint metadata

      :returns: Checkpoint ID



   .. py:method:: load_checkpoint(checkpoint_id: str) -> SimulationCheckpoint

      Load checkpoint by ID.

      :param checkpoint_id: ID of checkpoint to load

      :returns: Loaded checkpoint

      :raises ValueError: If checkpoint not found



   .. py:method:: restore_simulation(checkpoint_id: str, primitive_classes: Dict[str, Type]) -> Tuple[simpy.Environment, Dict[str, Any]]

      Restore simulation from checkpoint.

      :param checkpoint_id: ID of checkpoint to restore
      :param primitive_classes: Mapping of type names to primitive classes

      :returns: Tuple of (environment, primitives dictionary)



   .. py:method:: list_checkpoints() -> List[Dict[str, Any]]

      List all available checkpoints.

      :returns: List of checkpoint summaries



   .. py:method:: delete_checkpoint(checkpoint_id: str) -> None

      Delete a checkpoint.

      :param checkpoint_id: ID of checkpoint to delete



.. py:class:: SimulationRunner(env: simpy.Environment, primitives: Dict[str, Any], checkpoint_dir: str = 'checkpoints', enable_monitoring: bool = True)

   Enhanced simulation runner with chunking and state management.

   Provides chunked execution with automatic checkpointing,
   progress reporting, and pause/resume capabilities.

   .. attribute:: env

      SimPy environment

   .. attribute:: primitives

      Dictionary of simulation primitives

   .. attribute:: state_manager

      State persistence manager

   .. attribute:: monitor

      Optional simulation monitor

   .. attribute:: cache_path

      Path to event cache

   Initialize simulation runner.

   :param env: SimPy environment
   :param primitives: Dictionary of primitives
   :param checkpoint_dir: Directory for checkpoints
   :param enable_monitoring: Enable performance monitoring


   .. py:attribute:: env


   .. py:attribute:: primitives


   .. py:attribute:: state_manager


   .. py:attribute:: cache_path
      :type:  Optional[str]
      :value: None



   .. py:method:: run_chunked(total_days: int, chunk_size_days: float = 1.0, progress_callback: Optional[Any] = None, checkpoint_interval: Optional[float] = None) -> Dict[str, Any]

      Run simulation in chunks with progress reporting.

      :param total_days: Total simulation duration in days
      :param chunk_size_days: Size of each execution chunk
      :param progress_callback: Optional progress reporter
      :param checkpoint_interval: Days between auto checkpoints

      :returns: Simulation results and metrics



   .. py:method:: resume_from_checkpoint(checkpoint_id: str, primitive_classes: Dict[str, Type]) -> None

      Resume simulation from checkpoint.

      :param checkpoint_id: ID of checkpoint to resume from
      :param primitive_classes: Mapping of type names to classes



