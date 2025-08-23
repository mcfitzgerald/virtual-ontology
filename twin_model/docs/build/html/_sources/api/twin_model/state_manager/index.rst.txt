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


   .. py:method:: to_file(filepath)

      Save checkpoint to file.

      :param filepath: Path to save checkpoint file



   .. py:method:: from_file(filepath)
      :classmethod:


      Load checkpoint from file.

      :param filepath: Path to checkpoint file

      :returns: Loaded checkpoint instance



   .. py:method:: get_summary()

      Get human-readable checkpoint summary.

      :returns: Dictionary with checkpoint summary information



.. py:class:: StateManager(checkpoint_dir = 'checkpoints', max_checkpoints = 10, compression = True)

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


   .. py:attribute:: checkpoint_dir


   .. py:attribute:: max_checkpoints
      :value: 10



   .. py:attribute:: compression
      :value: True



   .. py:attribute:: checkpoints
      :type:  List[str]


   .. py:method:: save_checkpoint(env, primitives, cache_path = None, metadata = None)

      Save current simulation state as checkpoint.

      :param env: SimPy environment
      :param primitives: Dictionary of primitive instances
      :param cache_path: Optional path to event cache
      :param metadata: Optional checkpoint metadata

      :returns: Checkpoint ID



   .. py:method:: load_checkpoint(checkpoint_id)

      Load checkpoint by ID.

      :param checkpoint_id: ID of checkpoint to load

      :returns: Loaded checkpoint

      :raises ValueError: If checkpoint not found



   .. py:method:: restore_simulation(checkpoint_id, primitive_classes)

      Restore simulation from checkpoint.

      :param checkpoint_id: ID of checkpoint to restore
      :param primitive_classes: Mapping of type names to primitive classes

      :returns: Tuple of (environment, primitives dictionary)



   .. py:method:: list_checkpoints()

      List all available checkpoints.

      :returns: List of checkpoint summaries



   .. py:method:: delete_checkpoint(checkpoint_id)

      Delete a checkpoint.

      :param checkpoint_id: ID of checkpoint to delete



.. py:class:: SimulationRunner(env, primitives, checkpoint_dir = 'checkpoints', enable_monitoring = True)

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


   .. py:attribute:: env


   .. py:attribute:: primitives


   .. py:attribute:: state_manager


   .. py:attribute:: cache_path
      :type:  Optional[str]
      :value: None



   .. py:method:: run_chunked(total_days, chunk_size_days = 1.0, progress_callback = None, checkpoint_interval = None)

      Run simulation in chunks with progress reporting.

      :param total_days: Total simulation duration in days
      :param chunk_size_days: Size of each execution chunk
      :param progress_callback: Optional progress reporter
      :param checkpoint_interval: Days between auto checkpoints

      :returns: Simulation results and metrics



   .. py:method:: resume_from_checkpoint(checkpoint_id, primitive_classes)

      Resume simulation from checkpoint.

      :param checkpoint_id: ID of checkpoint to resume from
      :param primitive_classes: Mapping of type names to classes



