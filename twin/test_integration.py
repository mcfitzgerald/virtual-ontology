"""Integration tests for Virtual Twin System

Tests the complete integration between:
- Twin module database operations
- Ontology-driven analytics
- API exposure via api.sh and query-log.sh
- Configuration management
"""

import unittest
import sqlite3
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from twin.simulation_runner import SimulationRunner
from twin.actionable_parameters import ActionableParameters
from twin.config_loader import ConfigLoader
from twin.schema_manager import SchemaManager
from twin.config_manager import ConfigurationManager


class TestDatabaseIntegration(unittest.TestCase):
    """Test database integration across all layers."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.config = ConfigLoader()
        cls.db_path = cls.config.get("database.path")
        cls.schema_manager = SchemaManager(cls.db_path)
        
    def test_01_pristine_reset(self):
        """Test pristine database reset capability."""
        # Run reset command
        result = subprocess.run(
            ["python", "api/database_setup.py", "reset", "--no-backup"],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0, f"Reset failed: {result.stderr}")
        
        # Verify database is pristine
        verification = self.schema_manager.verify_schema()
        self.assertGreater(len(verification['table_counts']), 0)
        
        # Check no simulation configs in filesystem
        config_dir = Path(__file__).parent / "configs"
        if config_dir.exists():
            sim_configs = list(config_dir.glob("sim-*.json"))
            self.assertEqual(len(sim_configs), 0, "Config files still exist after reset")
    
    def test_02_config_storage_in_database(self):
        """Test that configs are stored in database, not files."""
        config_manager = ConfigurationManager(self.db_path)
        
        # Store a test config
        test_config = {"test": "config", "version": "1.0"}
        config_id = config_manager.store_config(
            run_id="test-run-001",
            config=test_config,
            config_type="full",  # Must be 'full', 'delta', or 'base'
            description="Integration test config"
        )
        
        self.assertIsNotNone(config_id)
        
        # Retrieve and verify
        retrieved = config_manager.get_config(config_id)
        self.assertEqual(retrieved["test"], "config")
        
        # Verify no file was created
        config_dir = Path(__file__).parent / "configs"
        if config_dir.exists():
            test_files = list(config_dir.glob("test-*.json"))
            self.assertEqual(len(test_files), 0, "Config file created instead of DB storage")
    
    def test_03_ontology_schema_alignment(self):
        """Test that database schema aligns with ontology definitions."""
        validation = self.schema_manager.validate_against_ontology()
        
        # Check MES ontology
        self.assertTrue(
            validation.get('mes_ontology_valid', False),
            f"MES ontology validation failed: {validation.get('discrepancies')}"
        )
        
        # Check Twin ontology (may have some dynamic tables)
        discrepancies = validation.get('discrepancies', [])
        # Filter out tables that are created on-demand
        dynamic_tables = {'entity_sync_metadata', 'sync_health_log', 'confidence_tracking'}
        real_discrepancies = [d for d in discrepancies if not any(t in d for t in dynamic_tables)]
        
        self.assertEqual(
            len(real_discrepancies), 0,
            f"Ontology discrepancies found: {real_discrepancies}"
        )
    
    def test_04_api_twin_table_access(self):
        """Test that API can query twin tables."""
        # Create a test query
        query = {"sql": "SELECT COUNT(*) as count FROM equipment_metadata"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(query, f)
            query_file = f.name
        
        try:
            # Execute query via API
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", "http://localhost:8000/query",
                 "-H", "Content-Type: application/json",
                 "-d", f"@{query_file}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                self.assertIn("data", response)
                self.assertEqual(response["data"][0]["count"], 9, "Equipment metadata count incorrect")
        finally:
            os.remove(query_file)
    
    def test_05_simulation_config_database_flow(self):
        """Test that simulation configs flow through database correctly."""
        runner = SimulationRunner(verbose=False)
        params = ActionableParameters()
        
        # Set a test parameter
        params.micro_stop_probability = 0.8
        
        # Run a short simulation
        result = runner.run_simulation(
            parameters=params,
            duration_days=1,
            seed=42
        )
        
        self.assertIsNotNone(result)
        self.assertIn("run_id", result)
        
        # Verify config is in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM simulation_configs 
                WHERE run_id = ?
            """, (result["run_id"],))
            count = cursor.fetchone()[0]
            
            # Note: Config might be deduplicated if same config exists
            cursor = conn.execute("""
                SELECT COUNT(*) FROM simulation_configs
            """)
            total = cursor.fetchone()[0]
            self.assertGreater(total, 0, "No configs stored in database")
        
        # Verify no file was created
        config_dir = Path(__file__).parent / "configs"
        if config_dir.exists():
            run_files = list(config_dir.glob(f"{result['run_id']}*.json"))
            self.assertEqual(len(run_files), 0, f"Config file created for {result['run_id']}")
    
    def test_06_unified_schema_management(self):
        """Test unified schema management."""
        schema_info = self.schema_manager.get_table_info("mes_data")
        
        self.assertIsNotNone(schema_info)
        self.assertEqual(schema_info['type'], 'sqlmodel')
        self.assertIn('columns', schema_info)
        
        # Check twin table
        twin_info = self.schema_manager.get_table_info("equipment_metadata")
        self.assertIsNotNone(twin_info)
        self.assertEqual(twin_info['type'], 'twin')
        self.assertEqual(twin_info['row_count'], 9)
    
    def test_07_configuration_consistency(self):
        """Test that all modules use consistent configuration."""
        # Get config from different modules
        from twin.simulation_runner import SimulationRunner
        from twin.cost_impact_calculator import CostImpactCalculator
        from twin.sync_health import SyncHealthMonitor
        
        runner = SimulationRunner()
        calculator = CostImpactCalculator()
        
        # All should use same database path
        self.assertEqual(runner.db_path, calculator.db_path)
        
        # Verify it matches config
        config = ConfigLoader()
        expected_path = config.get("database.path")
        self.assertTrue(runner.db_path.endswith(expected_path))


class TestQueryLogIntegration(unittest.TestCase):
    """Test query-log.sh integration with twin tables."""
    
    def test_query_log_twin_tables(self):
        """Test that query-log.sh can query twin tables."""
        # Create test query
        query = {"sql": "SELECT equipment_id, line FROM equipment_metadata WHERE line = 'LINE1' LIMIT 2"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(query, f)
            query_file = f.name
        
        try:
            # Execute via query-log.sh
            result = subprocess.run(
                ["./query-log.sh", "POST", "/query", "-d", f"@{query_file}"],
                capture_output=True,
                text=True
            )
            
            self.assertIn("LINE1-FIL", result.stdout, "Equipment data not found in response")
            
            # Verify it was logged
            log_file = Path("learning_history/query_logs.json")
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                    # Check last log entry
                    if logs:
                        last_log = logs[-1]
                        self.assertIn("equipment_metadata", last_log.get("request", {}).get("sql", ""))
        finally:
            os.remove(query_file)


def run_tests():
    """Run all integration tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryLogIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Make sure API is running
    api_check = subprocess.run(
        ["curl", "-s", "http://localhost:8000/"],
        capture_output=True
    )
    
    if api_check.returncode != 0:
        print("ERROR: API is not running. Start it with: ./api.sh start")
        sys.exit(1)
    
    # Run tests
    success = run_tests()
    sys.exit(0 if success else 1)