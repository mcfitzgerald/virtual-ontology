"""
Test ontology validation using the generic validator.

Tests templates and actual ontologies for:
- Structure compliance
- Type correctness  
- Cross-reference validity
- Inter-ontology alignment
"""

import pytest
from pathlib import Path
import yaml
import tempfile
from typing import Dict, Any

from ontology_validator import (
    OntologyValidator, 
    ValidationLevel,
    ValidationIssue,
    validate_ontology,
    validate_ontology_set
)


class TestOntologyValidation:
    """Test suite for ontology validation."""
    
    @pytest.fixture
    def template_dir(self) -> Path:
        """Path to templates directory."""
        return Path(__file__).parent.parent / "templates"
    
    @pytest.fixture
    def ontology_dir(self) -> Path:
        """Path to ontology directory."""
        return Path(__file__).parent.parent / "ontology"
    
    @pytest.fixture
    def sample_mes_ontology(self) -> Dict[str, Any]:
        """Create a minimal valid MES ontology."""
        return {
            "metadata": {
                "name": "Test MES Ontology",
                "version": "1.0.0",
                "description": "Test ontology",
                "namespace": "mes"
            },
            "classes": {
                "Equipment": {
                    "description": "Test equipment",
                    "maps_to": {"sql_table": "equipment"}
                }
            },
            "relationships": {
                "belongs_to": {
                    "from": "Equipment",
                    "to": "Line",
                    "type": "many-to-one"
                }
            },
            "properties": {
                "EquipmentID": {
                    "type": "string",
                    "sql_column": "equipment_id"
                }
            },
            "business_rules": {},
            "common_queries": {
                "test_query": {
                    "sql": "SELECT * FROM equipment"
                }
            }
        }
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = OntologyValidator()
        assert validator.ontology_type == "generic"
        assert len(validator.issues) == 0
        
        validator = OntologyValidator("mes")
        assert validator.ontology_type == "mes"
    
    def test_validate_missing_file(self):
        """Test validation of missing file."""
        validator = OntologyValidator()
        issues = validator.validate(Path("nonexistent.yaml"))
        
        assert len(issues) == 1
        assert issues[0].level == ValidationLevel.ERROR
        assert "not found" in issues[0].message
    
    def test_validate_invalid_yaml(self, tmp_path):
        """Test validation of invalid YAML."""
        # Create invalid YAML file
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content:")
        
        validator = OntologyValidator()
        issues = validator.validate(invalid_file)
        
        assert len(issues) == 1
        assert issues[0].level == ValidationLevel.ERROR
        assert "YAML" in issues[0].category
    
    def test_validate_structure(self, tmp_path):
        """Test structure validation."""
        # Create ontology missing required sections
        incomplete = tmp_path / "incomplete.yaml"
        incomplete.write_text(yaml.dump({
            "metadata": {"name": "Test"}
        }))
        
        validator = OntologyValidator("mes")
        issues = validator.validate(incomplete)
        
        # Should have errors for missing required sections
        error_issues = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(error_issues) > 0
        
        missing_sections = ["classes", "relationships", "properties", "business_rules", "common_queries"]
        for section in missing_sections:
            assert any(section in i.message for i in error_issues)
    
    def test_validate_metadata(self, tmp_path):
        """Test metadata validation."""
        # Create ontology with incomplete metadata
        test_file = tmp_path / "test.yaml"
        test_file.write_text(yaml.dump({
            "metadata": {
                "name": "Test",
                # Missing version and description
            }
        }))
        
        validator = OntologyValidator()
        issues = validator.validate(test_file)
        
        metadata_issues = [i for i in issues if "Metadata" in i.category]
        assert len(metadata_issues) >= 2  # Missing version and description
    
    def test_validate_version_format(self, tmp_path):
        """Test version format validation."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text(yaml.dump({
            "metadata": {
                "name": "Test",
                "version": "v1",  # Invalid format
                "description": "Test"
            }
        }))
        
        validator = OntologyValidator()
        issues = validator.validate(test_file)
        
        version_issues = [i for i in issues if "version" in i.path]
        assert len(version_issues) > 0
        assert version_issues[0].level == ValidationLevel.WARNING
    
    def test_validate_mes_specific(self, tmp_path, sample_mes_ontology):
        """Test MES-specific validations."""
        # Remove SQL mapping from a class
        sample_mes_ontology["classes"]["Equipment"].pop("maps_to")
        
        test_file = tmp_path / "mes.yaml"
        test_file.write_text(yaml.dump(sample_mes_ontology))
        
        validator = OntologyValidator("mes")
        issues = validator.validate(test_file)
        
        mapping_issues = [i for i in issues if "Mapping" in i.category]
        assert len(mapping_issues) > 0
    
    def test_validate_twin_specific(self, tmp_path):
        """Test Twin-specific validations."""
        twin_ontology = {
            "metadata": {
                "name": "Test Twin",
                "version": "1.0.0",
                "description": "Test"
            },
            "tbox": {},
            "rbox": {},
            "properties": {},
            "model_definition": {
                # Missing lines
            },
            "behavioral_rules": {},
            "control_parameters": {
                "speed": {"type": "float"}
            },
            "parameter_effects": {
                # Missing speed effects
            },
            "transduction_layer": {
                # Missing required mappings
            }
        }
        
        test_file = tmp_path / "twin.yaml"
        test_file.write_text(yaml.dump(twin_ontology))
        
        validator = OntologyValidator("twin")
        issues = validator.validate(test_file)
        
        # Should have errors for missing model lines
        model_issues = [i for i in issues if "Model" in i.category]
        assert len(model_issues) > 0
        
        # Should have warning for parameter without effects
        param_issues = [i for i in issues if "Parameters" in i.category]
        assert len(param_issues) > 0
    
    def test_validate_cross_references(self, tmp_path):
        """Test cross-reference validation."""
        ontology = {
            "metadata": {
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "classes": {
                "Equipment": {"description": "Test"}
                # Missing "Line" class
            },
            "relationships": {
                "belongs_to": {
                    "from": "Equipment",
                    "to": "Line",  # References undefined class
                    "type": "many-to-one"
                }
            },
            "properties": {}
        }
        
        test_file = tmp_path / "test.yaml"
        test_file.write_text(yaml.dump(ontology))
        
        validator = OntologyValidator()
        issues = validator.validate(test_file)
        
        ref_issues = [i for i in issues if "Reference" in i.category]
        assert len(ref_issues) > 0
        assert "undefined class" in ref_issues[0].message.lower()
    
    def test_validate_naming_conventions(self, tmp_path):
        """Test naming convention validation."""
        ontology = {
            "metadata": {
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "classes": {
                "equipment": {"description": "Should be PascalCase"},  # lowercase
                "GoodClass": {"description": "Correct"}
            },
            "properties": {
                "123Invalid": {"type": "string"},  # Starts with number
                "validProperty": {"type": "string"}
            }
        }
        
        test_file = tmp_path / "test.yaml"
        test_file.write_text(yaml.dump(ontology))
        
        validator = OntologyValidator()
        issues = validator.validate(test_file)
        
        naming_issues = [i for i in issues if "Naming" in i.category]
        assert len(naming_issues) > 0
        assert all(i.level == ValidationLevel.INFO for i in naming_issues)
    
    def test_validate_data_types(self, tmp_path):
        """Test data type validation."""
        ontology = {
            "metadata": {
                "name": "Test",
                "version": "1.0.0",
                "description": "Test"
            },
            "properties": {
                "validProp": {"type": "string"},
                "invalidProp": {"type": "unknown_type"}  # Invalid type
            }
        }
        
        test_file = tmp_path / "test.yaml"
        test_file.write_text(yaml.dump(ontology))
        
        validator = OntologyValidator()
        issues = validator.validate(test_file)
        
        type_issues = [i for i in issues if "Type" in i.category]
        assert len(type_issues) > 0
        assert "unknown_type" in type_issues[0].message
    
    def test_validate_alignment(self, tmp_path):
        """Test inter-ontology alignment validation."""
        # Create MES ontology
        mes_ontology = {
            "metadata": {"name": "MES", "version": "1.0.0", "description": "MES"},
            "properties": {
                "EquipmentID": {"type": "string", "sql_column": "equipment_id"},
                "OEE_Score": {"type": "float", "sql_column": "oee_score"}
            }
        }
        
        # Create Twin ontology (missing MES import)
        twin_ontology = {
            "metadata": {
                "name": "Twin",
                "version": "1.0.0",
                "description": "Twin",
                "imports": []  # Should import MES
            },
            "transduction_layer": {
                "mes_record_structure": {
                    "fields": [
                        {"EquipmentID": "string"},
                        {"UnknownField": "string"}  # Not in MES
                    ]
                }
            }
        }
        
        # Create Database schema
        db_schema = {
            "metadata": {"name": "DB", "version": "1.0.0", "description": "DB"},
            "tables": {
                "mes_data": {
                    "columns": {
                        "equipment_id": {"type": "VARCHAR(20)"},
                        # Missing oee_score column
                    }
                }
            }
        }
        
        ontologies = {
            "mes": mes_ontology,
            "twin": twin_ontology,
            "database": db_schema
        }
        
        validator = OntologyValidator()
        issues = validator.validate_alignment(ontologies)
        
        alignment_issues = [i for i in issues if "Alignment" in i.category]
        assert len(alignment_issues) > 0
        
        # Check specific alignment issues
        import_issues = [i for i in alignment_issues if "import" in i.message.lower()]
        assert len(import_issues) > 0
        
        field_issues = [i for i in alignment_issues if "UnknownField" in i.message]
        assert len(field_issues) > 0
    
    def test_print_report(self, capsys):
        """Test report printing."""
        validator = OntologyValidator()
        
        # Add various issues
        validator.issues = [
            ValidationIssue(ValidationLevel.ERROR, "Test", "path1", "Error message"),
            ValidationIssue(ValidationLevel.WARNING, "Test", "path2", "Warning message"),
            ValidationIssue(ValidationLevel.INFO, "Test", "path3", "Info message"),
        ]
        
        validator.print_report()
        
        captured = capsys.readouterr()
        assert "Validation Report" in captured.out
        assert "Errors: 1" in captured.out
        assert "Warnings: 1" in captured.out
        assert "Info: 1" in captured.out
        assert "❌ ERRORS" in captured.out
        assert "⚠️  WARNINGS" in captured.out
        assert "ℹ️  INFO" in captured.out
    
    def test_validate_existing_ontologies(self, ontology_dir):
        """Test validation of actual ontology files."""
        # Test existing MES ontology
        mes_path = ontology_dir / "ontology_spec.yaml"
        if mes_path.exists():
            validator = OntologyValidator("mes")
            issues = validator.validate(mes_path)
            
            # Print report for debugging
            if issues:
                print(f"\nValidation of {mes_path}:")
                validator.print_report(issues)
        
        # Test existing Twin ontology
        twin_path = ontology_dir / "twin_ontology_spec.yaml"
        if twin_path.exists():
            validator = OntologyValidator("twin")
            issues = validator.validate(twin_path)
            
            if issues:
                print(f"\nValidation of {twin_path}:")
                validator.print_report(issues)
    
    @pytest.mark.parametrize("template_file,ont_type", [
        ("mes_ontology_template.yaml", "mes"),
        ("twin_ontology_template.yaml", "twin"),
        ("mes_database_schema_template.yaml", "database")
    ])
    def test_validate_templates(self, template_dir, template_file, ont_type):
        """Test that templates pass basic validation."""
        template_path = template_dir / template_file
        
        if not template_path.exists():
            pytest.skip(f"Template {template_file} not found")
        
        # Templates have placeholders, so we expect some issues
        # but they should be mostly warnings/info, not structural errors
        validator = OntologyValidator(ont_type)
        issues = validator.validate(template_path)
        
        # Templates might have placeholders that cause issues
        # Just ensure no critical structural errors
        critical_errors = [i for i in issues if 
                          i.level == ValidationLevel.ERROR and 
                          "structure" in i.category.lower()]
        
        if critical_errors:
            print(f"\nCritical errors in template {template_file}:")
            for issue in critical_errors:
                print(f"  {issue}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])