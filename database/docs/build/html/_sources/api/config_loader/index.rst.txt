config_loader
=============

.. py:module:: config_loader

.. autoapi-nested-parse::

   Configuration loader for the Virtual Twin system.



Exceptions
----------

.. autoapisummary::

   config_loader.ConfigurationError


Classes
-------

.. autoapisummary::

   config_loader.ConfigLoader


Module Contents
---------------

.. py:exception:: ConfigurationError

   Bases: :py:obj:`Exception`


   Raised when configuration is missing or invalid.


.. py:class:: ConfigLoader

   Load and validate configuration files.


   .. py:method:: load_config(config_name)
      :staticmethod:


      Load a configuration file. FAILS if file doesn't exist.

      :param config_name: Name of config file (without .yaml)

      :returns: Configuration dictionary

      :raises ConfigurationError: If config file missing or invalid



   .. py:method:: get_required(config, path, error_msg = None)
      :staticmethod:


      Get a required configuration value using dot notation.

      :param config: Configuration dictionary
      :param path: Dot-separated path (e.g., "validation.buffer.min_size")
      :param error_msg: Custom error message

      :returns: Configuration value

      :raises ConfigurationError: If path not found



