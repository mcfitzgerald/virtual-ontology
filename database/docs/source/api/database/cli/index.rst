database.cli
============

.. py:module:: database.cli

.. autoapi-nested-parse::

   CLI for database operations



Functions
---------

.. autoapisummary::

   database.cli.cli
   database.cli.init
   database.cli.import_historical
   database.cli.sync_manifests
   database.cli.run_simulation
   database.cli.run_experiment
   database.cli.discover_patterns
   database.cli.generate_recommendations
   database.cli.status


Module Contents
---------------

.. py:function:: cli()

   Twin Database Management CLI


.. py:function:: init()

   Initialize database with all tables


.. py:function:: import_historical(csv_path)

   Import historical MES data from CSV


.. py:function:: sync_manifests()

   Sync configurations from manifest YAMLs


.. py:function:: run_simulation(days, run_type)

   Run simulation and store in database


.. py:function:: run_experiment(name, hypothesis, days, runs)

   Run an experiment with parameter changes


.. py:function:: discover_patterns(min_confidence)

   Discover patterns from experiments


.. py:function:: generate_recommendations()

   Generate recommendations from patterns


.. py:function:: status()

   Show database status


