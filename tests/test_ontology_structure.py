"""
Test suite for validating ontology structure.

Tests YAML syntax, required sections, and structural integrity.
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List


class TestOntologyStructure:
    """Test cases for ontology structure validation."""
    
    @pytest.fixture
    def twin_ontology_path(self) -> Path:
        """Path to twin ontology file."""
        return Path(__file__).parent.parent / "ontology" / "twin_ontology.yaml"
    
    @pytest.fixture
    def mes_ontology_path(self) -> Path:
        """Path to MES ontology file."""
        return Path(__file__).parent.parent / "ontology" / "mes_ontology.yaml"
    
    @pytest.fixture
    def twin_ontology(self, twin_ontology_path: Path) -> Dict[str, Any]:
        """Load twin ontology."""
        with open(twin_ontology_path, 'r') as f:
            return yaml.safe_load(f)
    
    @pytest.fixture
    def mes_ontology(self, mes_ontology_path: Path) -> Dict[str, Any]:
        """Load MES ontology."""
        with open(mes_ontology_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_twin_ontology_exists(self, twin_ontology_path: Path) -> None:
        """Test that twin ontology file exists."""
        assert twin_ontology_path.exists(), f"Twin ontology not found at {twin_ontology_path}"
    
    def test_mes_ontology_exists(self, mes_ontology_path: Path) -> None:
        """Test that MES ontology file exists."""
        assert mes_ontology_path.exists(), f"MES ontology not found at {mes_ontology_path}"
    
    def test_twin_ontology_valid_yaml(self, twin_ontology: Dict[str, Any]) -> None:
        """Test that twin ontology is valid YAML."""
        assert isinstance(twin_ontology, dict), "Twin ontology should be a dictionary"
        assert len(twin_ontology) > 0, "Twin ontology should not be empty"
    
    def test_mes_ontology_valid_yaml(self, mes_ontology: Dict[str, Any]) -> None:
        """Test that MES ontology is valid YAML."""
        assert isinstance(mes_ontology, dict), "MES ontology should be a dictionary"
        assert len(mes_ontology) > 0, "MES ontology should not be empty"
    
    @pytest.mark.parametrize("required_section", [
        "metadata",
        "tbox",
        "rbox",
        "properties",
        "model_definition",
        "behavioral_rules",
        "control_parameters",
        "parameter_effects",
        "transduction_layer"
    ])
    def test_twin_ontology_required_sections(
        self, 
        twin_ontology: Dict[str, Any], 
        required_section: str
    ) -> None:
        """Test that twin ontology has all required sections."""
        assert required_section in twin_ontology, \
            f"Twin ontology missing required section: {required_section}"
    
    @pytest.mark.parametrize("required_section", [
        "metadata",
        "classes",
        "relationships",
        "properties",
        "business_rules",
        "common_queries"
    ])
    def test_mes_ontology_required_sections(
        self, 
        mes_ontology: Dict[str, Any], 
        required_section: str
    ) -> None:
        """Test that MES ontology has all required sections."""
        assert required_section in mes_ontology, \
            f"MES ontology missing required section: {required_section}"
    
    def test_twin_tbox_structure(self, twin_ontology: Dict[str, Any]) -> None:
        """Test twin ontology TBox structure."""
        tbox = twin_ontology.get("tbox", {})
        assert "classes" in tbox, "TBox should have classes"
        assert "enumerations" in tbox, "TBox should have enumerations"
        
        # Check key classes exist
        classes = tbox.get("classes", {})
        assert "Equipment" in classes, "Equipment class required"
        assert "Buffer" in classes, "Buffer class required"
        
        # Check key enumerations
        enums = tbox.get("enumerations", {})
        assert "EquipmentType" in enums, "EquipmentType enum required"
        assert "EquipmentState" in enums, "EquipmentState enum required"
    
    def test_mes_classes_structure(self, mes_ontology: Dict[str, Any]) -> None:
        """Test MES ontology classes structure."""
        classes = mes_ontology.get("classes", {})
        assert isinstance(classes, dict), "Classes should be a dictionary"
        
        # Check key classes exist
        assert "ProductionSnapshot" in classes, "ProductionSnapshot class required"
        assert "Equipment" in classes, "Equipment class required"
        assert "ProductionLine" in classes, "ProductionLine class required"
    
    def test_twin_model_definition(self, twin_ontology: Dict[str, Any]) -> None:
        """Test twin ontology model definition."""
        model_def = twin_ontology.get("model_definition", {})
        assert "lines" in model_def, "Model definition should have lines"
        
        lines = model_def.get("lines", [])
        assert len(lines) > 0, "At least one production line required"
        
        # Check first line structure
        first_line = lines[0]
        assert "line_id" in first_line, "Line should have ID"
        assert "equipment_sequence" in first_line, "Line should have equipment sequence"
        assert "buffer_capacities" in first_line, "Line should have buffer capacities"
        assert "source_arrival_rate" in first_line, "Line should have arrival rate"
        
        # Check equipment configuration
        equipment = first_line.get("equipment_sequence", [])
        assert len(equipment) > 0, "Line should have equipment"
        
        for eq in equipment:
            assert "id" in eq, "Equipment should have ID"
            assert "type" in eq, "Equipment should have type"
            assert "base_rate" in eq, "Equipment should have base rate"
            assert "mtbf" in eq, "Equipment should have MTBF"
            assert "mttr" in eq, "Equipment should have MTTR"
    
    def test_control_parameters(self, twin_ontology: Dict[str, Any]) -> None:
        """Test control parameters definition."""
        control_params = twin_ontology.get("control_parameters", {})
        
        # Check that we have at least one control parameter
        assert len(control_params) > 0, "Should have at least one control parameter"
        
        # Check that line_speed_setting exists (the main one we defined)
        assert "line_speed_setting" in control_params, "Missing line_speed_setting control parameter"
        
        # Check structure of each control parameter
        for param_name, param_def in control_params.items():
            assert "type" in param_def, f"{param_name} should have type"
            assert "default" in param_def, f"{param_name} should have default value"
            assert "description" in param_def, f"{param_name} should have description"
    
    def test_parameter_effects(self, twin_ontology: Dict[str, Any]) -> None:
        """Test parameter effects mapping."""
        param_effects = twin_ontology.get("parameter_effects", {})
        
        # Check that all control parameters have effects defined
        control_params = twin_ontology.get("control_parameters", {})
        for param_name in control_params:
            assert param_name in param_effects, \
                f"No effects defined for control parameter: {param_name}"
            
            effects = param_effects[param_name]
            assert "affects" in effects, f"{param_name} should have 'affects' list"
            assert len(effects["affects"]) > 0, f"{param_name} should affect something"
            
            # Check effect structure
            for effect in effects["affects"]:
                assert "target" in effect, "Effect should have target"
                assert ("formula" in effect or "mapping" in effect), \
                    "Effect should have formula or mapping"
    
    def test_transduction_layer(self, twin_ontology: Dict[str, Any]) -> None:
        """Test transduction layer configuration."""
        transduction = twin_ontology.get("transduction_layer", {})
        
        assert "mes_snapshot_interval" in transduction, \
            "Transduction layer should define snapshot interval"
        assert "equipment_state_mapping" in transduction, \
            "Transduction layer should map equipment states"
        assert "mes_record_structure" in transduction, \
            "Transduction layer should define MES record structure"
        
        # Check MES record fields
        mes_record = transduction.get("mes_record_structure", {})
        assert "fields" in mes_record, "MES record should have fields"
        
        # Check that we have at least some key fields
        field_dict = {}
        for field in mes_record.get("fields", []):
            if isinstance(field, dict):
                field_dict.update(field)
        
        assert "Timestamp" in field_dict, "MES record should have Timestamp field"
        assert "EquipmentID" in field_dict, "MES record should have EquipmentID field"
        assert "MachineStatus" in field_dict, "MES record should have MachineStatus field"
    
    def test_mes_business_rules(self, mes_ontology: Dict[str, Any]) -> None:
        """Test MES business rules."""
        business_rules = mes_ontology.get("business_rules", {})
        
        assert isinstance(business_rules, dict), "Business rules should be a dictionary"
        assert len(business_rules) > 0, "Should have at least one business rule"
        
        # Check for key business rules
        assert "no_production_when_stopped" in business_rules, "Should have no_production_when_stopped rule"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])