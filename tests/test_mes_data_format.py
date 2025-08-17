"""
Test MES data format validation.

Ensures generated MES data matches the expected format from mes_data_sample.csv.
"""

import pytest
import csv
import io
from pathlib import Path
from typing import Dict, Any, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMESDataFormat:
    """Test MES data format compliance."""
    
    @pytest.fixture
    def expected_columns(self) -> List[str]:
        """Expected column names from mes_data_sample.csv."""
        return [
            "Timestamp", "ProductionOrderID", "LineID", "EquipmentID",
            "EquipmentType", "ProductID", "ProductName", "MachineStatus",
            "DowntimeReason", "GoodUnitsProduced", "ScrapUnitsProduced",
            "TargetRate_units_per_5min", "StandardCost_per_unit",
            "SalePrice_per_unit", "Availability_Score", "Performance_Score",
            "Quality_Score", "OEE_Score"
        ]
    
    @pytest.fixture
    def sample_mes_record(self) -> Dict[str, Any]:
        """Sample MES record matching expected format."""
        return {
            "Timestamp": "2025-06-01 00:00:00",
            "ProductionOrderID": "ORD-1000",
            "LineID": 1,
            "EquipmentID": "LINE1-FIL",
            "EquipmentType": "Filler",
            "ProductID": "SKU-2001",
            "ProductName": "12oz Soda",
            "MachineStatus": "Running",
            "DowntimeReason": "",
            "GoodUnitsProduced": 250,
            "ScrapUnitsProduced": 5,
            "TargetRate_units_per_5min": 475,
            "StandardCost_per_unit": 0.20,
            "SalePrice_per_unit": 0.65,
            "Availability_Score": 100.0,
            "Performance_Score": 52.6,
            "Quality_Score": 98.0,
            "OEE_Score": 51.5
        }
    
    def test_column_names(self, expected_columns):
        """Test that all expected columns are defined."""
        # This is more of a documentation test
        assert len(expected_columns) == 18
        assert "Timestamp" in expected_columns
        assert "OEE_Score" in expected_columns
    
    def test_validate_record_structure(self, sample_mes_record, expected_columns):
        """Test that sample record has all required fields."""
        for column in expected_columns:
            assert column in sample_mes_record, f"Missing column: {column}"
    
    def test_validate_data_types(self, sample_mes_record):
        """Test data types of MES record fields."""
        # String fields
        assert isinstance(sample_mes_record["Timestamp"], str)
        assert isinstance(sample_mes_record["ProductionOrderID"], str)
        assert isinstance(sample_mes_record["EquipmentID"], str)
        assert isinstance(sample_mes_record["EquipmentType"], str)
        assert isinstance(sample_mes_record["ProductID"], str)
        assert isinstance(sample_mes_record["ProductName"], str)
        assert isinstance(sample_mes_record["MachineStatus"], str)
        assert isinstance(sample_mes_record["DowntimeReason"], str)
        
        # Integer fields
        assert isinstance(sample_mes_record["LineID"], int)
        assert isinstance(sample_mes_record["GoodUnitsProduced"], int)
        assert isinstance(sample_mes_record["ScrapUnitsProduced"], int)
        assert isinstance(sample_mes_record["TargetRate_units_per_5min"], int)
        
        # Float fields
        assert isinstance(sample_mes_record["StandardCost_per_unit"], (int, float))
        assert isinstance(sample_mes_record["SalePrice_per_unit"], (int, float))
        assert isinstance(sample_mes_record["Availability_Score"], (int, float))
        assert isinstance(sample_mes_record["Performance_Score"], (int, float))
        assert isinstance(sample_mes_record["Quality_Score"], (int, float))
        assert isinstance(sample_mes_record["OEE_Score"], (int, float))
    
    def test_validate_value_ranges(self, sample_mes_record):
        """Test that values are within expected ranges."""
        # LineID should be 1-10
        assert 1 <= sample_mes_record["LineID"] <= 10
        
        # Production counts should be non-negative
        assert sample_mes_record["GoodUnitsProduced"] >= 0
        assert sample_mes_record["ScrapUnitsProduced"] >= 0
        
        # Percentages should be 0-100 (or slightly over for performance)
        assert 0 <= sample_mes_record["Availability_Score"] <= 100
        assert 0 <= sample_mes_record["Performance_Score"] <= 120
        assert 0 <= sample_mes_record["Quality_Score"] <= 100
        assert 0 <= sample_mes_record["OEE_Score"] <= 100
        
        # Costs should be positive
        assert sample_mes_record["StandardCost_per_unit"] >= 0
        assert sample_mes_record["SalePrice_per_unit"] >= 0
    
    def test_validate_business_rules(self, sample_mes_record):
        """Test business rule compliance."""
        # If stopped, production should be 0
        if sample_mes_record["MachineStatus"] == "Stopped":
            assert sample_mes_record["GoodUnitsProduced"] == 0
            assert sample_mes_record["ScrapUnitsProduced"] == 0
            assert sample_mes_record["DowntimeReason"] != ""
        
        # If running, downtime reason should be empty
        if sample_mes_record["MachineStatus"] == "Running":
            assert sample_mes_record["DowntimeReason"] == ""
        
        # OEE calculation check (within tolerance)
        if all(score > 0 for score in [
            sample_mes_record["Availability_Score"],
            sample_mes_record["Performance_Score"],
            sample_mes_record["Quality_Score"]
        ]):
            calculated_oee = (
                sample_mes_record["Availability_Score"] *
                sample_mes_record["Performance_Score"] *
                sample_mes_record["Quality_Score"]
            ) / 10000
            
            assert abs(calculated_oee - sample_mes_record["OEE_Score"]) < 0.5, \
                f"OEE mismatch: calculated={calculated_oee:.1f}, actual={sample_mes_record['OEE_Score']}"
    
    def test_equipment_id_format(self, sample_mes_record):
        """Test equipment ID follows naming convention."""
        equipment_id = sample_mes_record["EquipmentID"]
        
        # Should match pattern LINE[0-9]-[A-Z]{3}
        import re
        pattern = r'^LINE[0-9]-[A-Z]{3}$'
        assert re.match(pattern, equipment_id), \
            f"Equipment ID '{equipment_id}' doesn't match pattern"
    
    def test_machine_status_values(self):
        """Test valid machine status values."""
        valid_statuses = {"Running", "Stopped", "Idle"}
        
        test_cases = [
            ("Running", True),
            ("Stopped", True),
            ("Idle", True),
            ("RUNNING", False),  # Case sensitive
            ("Unknown", False),
            ("", False)
        ]
        
        for status, should_be_valid in test_cases:
            is_valid = status in valid_statuses
            assert is_valid == should_be_valid, \
                f"Status '{status}' validation failed"
    
    def test_downtime_reason_values(self):
        """Test valid downtime reason values."""
        valid_reasons = {
            "UNP-JAM", "UNP-MECH", "UNP-ELEC",  # Unplanned
            "PL-CLEAN", "PL-SETUP",              # Planned
            ""                                    # No downtime
        }
        
        test_cases = [
            ("UNP-JAM", True),
            ("PL-CLEAN", True),
            ("", True),
            ("UNKNOWN", False),
            ("JAM", False)  # Missing prefix
        ]
        
        for reason, should_be_valid in test_cases:
            is_valid = reason in valid_reasons
            assert is_valid == should_be_valid, \
                f"Downtime reason '{reason}' validation failed"
    
    def test_csv_generation(self, sample_mes_record, expected_columns):
        """Test CSV generation from MES records."""
        records = [sample_mes_record]
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=expected_columns)
        writer.writeheader()
        writer.writerows(records)
        
        # Read back and validate
        output.seek(0)
        reader = csv.DictReader(output)
        
        # Check header
        assert reader.fieldnames == expected_columns
        
        # Check data
        rows = list(reader)
        assert len(rows) == 1
        
        # Values should match (accounting for string conversion)
        row = rows[0]
        assert row["Timestamp"] == sample_mes_record["Timestamp"]
        assert int(row["LineID"]) == sample_mes_record["LineID"]
        assert float(row["OEE_Score"]) == sample_mes_record["OEE_Score"]
    
    def test_sample_file_format(self):
        """Test that mes_data_sample.csv has expected format."""
        sample_path = Path(__file__).parent.parent / "mes_data_sample.csv"
        
        if not sample_path.exists():
            pytest.skip("mes_data_sample.csv not found")
        
        with open(sample_path, 'r') as f:
            reader = csv.DictReader(f)
            
            # Check we can read at least one row
            first_row = next(reader, None)
            assert first_row is not None, "Sample file is empty"
            
            # Check has expected columns (may have extra spaces)
            for col in ["Timestamp", "LineID", "EquipmentID", "OEE_Score"]:
                assert any(col in field for field in first_row.keys()), \
                    f"Column '{col}' not found in sample"


class TestMESDataIntegration:
    """Test integration with twin model MES data generation."""
    
    def test_twin_model_mes_format(self):
        """Test that twin model generates correct MES format."""
        try:
            from twin_model import SimulationRunner
            
            runner = SimulationRunner()
            results = runner.run_simulation(
                duration_days=1/24,  # 1 hour
                seed=42
            )
            
            # Get MES data
            mes_data = results.mes_data
            assert len(mes_data) > 0
            
            # Check structure of first snapshot
            snapshot = mes_data[0]
            
            # Should have key fields
            assert 'timestamp' in snapshot
            assert 'line_id' in snapshot
            assert 'equipment_states' in snapshot
            
            # Equipment states should have OEE info
            for eq_id, state in snapshot['equipment_states'].items():
                assert 'state' in state
                assert 'oee' in state
                assert 'units_produced' in state
                assert 'units_scrapped' in state
                
                # OEE should be 0-100
                assert 0 <= state['oee'] <= 100
                
        except ImportError:
            pytest.skip("twin_model not available")
    
    def test_format_conversion_needed(self):
        """Test that we need to convert twin format to MES CSV format."""
        try:
            from twin_model import SimulationRunner
            
            runner = SimulationRunner()
            results = runner.run_simulation(duration_days=1/48, seed=42)
            
            # Current format is hierarchical
            snapshot = results.mes_data[0]
            
            # Need to flatten to CSV format
            # Each equipment should become a row
            assert 'equipment_states' in snapshot
            
            # This confirms we need a transduction layer
            # to convert from twin's hierarchical format
            # to flat CSV format matching mes_data_sample.csv
            
        except ImportError:
            pytest.skip("twin_model not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])