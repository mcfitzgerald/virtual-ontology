"""
Generic Ontology Validator

Validates ontologies for:
- Structure compliance with templates
- Type correctness
- Cross-references validity
- Inter-ontology alignment
- Business rule consistency
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "ERROR"      # Must fix - ontology is broken
    WARNING = "WARNING"  # Should fix - ontology may not work as expected
    INFO = "INFO"        # Nice to fix - best practices


@dataclass
class ValidationIssue:
    """Single validation issue."""
    level: ValidationLevel
    category: str
    path: str  # Path in YAML structure, e.g., "classes.Equipment.properties.id"
    message: str
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        """Format issue for display."""
        msg = f"[{self.level.value}] {self.category}: {self.path}\n  {self.message}"
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


class OntologyValidator:
    """Generic validator for ontologies."""
    
    def __init__(self, ontology_type: str = "generic"):
        """
        Initialize validator.
        
        Args:
            ontology_type: Type of ontology (mes, twin, database)
        """
        self.ontology_type = ontology_type
        self.issues: List[ValidationIssue] = []
        
        # Define expected structures for different ontology types
        self.expected_structures = {
            "mes": {
                "required_sections": ["metadata", "classes", "relationships", "properties", 
                                     "business_rules", "common_queries"],
                "optional_sections": ["twin_mapping", "glossary"],
            },
            "twin": {
                "required_sections": ["metadata", "tbox", "rbox", "properties",
                                     "model_definition", "behavioral_rules", 
                                     "control_parameters", "parameter_effects",
                                     "transduction_layer"],
                "optional_sections": ["simulation_config", "products", "production_orders"],
            },
            "database": {
                "required_sections": ["metadata", "database", "tables"],
                "optional_sections": ["views", "constraints", "indexes", "procedures",
                                     "validation", "integration"],
            },
            "generic": {
                "required_sections": ["metadata"],
                "optional_sections": [],
            }
        }
    
    def validate(self, ontology_path: Path) -> List[ValidationIssue]:
        """
        Validate an ontology file.
        
        Args:
            ontology_path: Path to ontology YAML file
            
        Returns:
            List of validation issues
        """
        self.issues = []
        
        # Load ontology
        try:
            with open(ontology_path, 'r') as f:
                ontology = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="YAML Syntax",
                path="root",
                message=f"Invalid YAML syntax: {e}",
                suggestion="Fix YAML syntax errors before proceeding"
            ))
            return self.issues
        except FileNotFoundError:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="File",
                path="root",
                message=f"File not found: {ontology_path}",
                suggestion="Ensure file path is correct"
            ))
            return self.issues
        
        # Run validation checks
        self._validate_structure(ontology)
        self._validate_metadata(ontology.get("metadata", {}))
        
        # Type-specific validations
        if self.ontology_type == "mes":
            self._validate_mes_specific(ontology)
        elif self.ontology_type == "twin":
            self._validate_twin_specific(ontology)
        elif self.ontology_type == "database":
            self._validate_database_specific(ontology)
        
        # Common validations
        self._validate_cross_references(ontology)
        self._validate_naming_conventions(ontology)
        self._validate_data_types(ontology)
        
        return self.issues
    
    def validate_alignment(self, ontologies: Dict[str, Dict[str, Any]]) -> List[ValidationIssue]:
        """
        Validate alignment between multiple ontologies.
        
        Args:
            ontologies: Dict of {name: ontology_data}
            
        Returns:
            List of alignment issues
        """
        self.issues = []
        
        # Check if we have the expected set
        if "mes" in ontologies and "twin" in ontologies:
            self._validate_mes_twin_alignment(ontologies["mes"], ontologies["twin"])
        
        if "mes" in ontologies and "database" in ontologies:
            self._validate_mes_database_alignment(ontologies["mes"], ontologies["database"])
        
        if "twin" in ontologies and "database" in ontologies:
            self._validate_twin_database_alignment(ontologies["twin"], ontologies["database"])
        
        return self.issues
    
    def _validate_structure(self, ontology: Dict[str, Any]) -> None:
        """Validate basic structure."""
        structure = self.expected_structures.get(self.ontology_type, {})
        
        # Check required sections
        for section in structure.get("required_sections", []):
            if section not in ontology:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Structure",
                    path=section,
                    message=f"Required section '{section}' is missing",
                    suggestion=f"Add '{section}' section to ontology"
                ))
        
        # Check for unknown sections
        known_sections = set(structure.get("required_sections", []) + 
                           structure.get("optional_sections", []))
        if known_sections:  # Only check if we have defined sections
            for section in ontology.keys():
                if section not in known_sections:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="Structure",
                        path=section,
                        message=f"Unknown section '{section}'",
                        suggestion=f"Verify this section is intended"
                    ))
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate metadata section."""
        required_fields = ["name", "version", "description"]
        
        for field in required_fields:
            if field not in metadata:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Metadata",
                    path=f"metadata.{field}",
                    message=f"Required metadata field '{field}' is missing",
                    suggestion=f"Add '{field}' to metadata section"
                ))
        
        # Validate version format
        if "version" in metadata:
            version = metadata["version"]
            if not re.match(r'^\d+\.\d+\.\d+$', str(version)):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="Metadata",
                    path="metadata.version",
                    message=f"Version '{version}' doesn't follow semver format",
                    suggestion="Use format like '1.0.0'"
                ))
    
    def _validate_mes_specific(self, ontology: Dict[str, Any]) -> None:
        """MES ontology specific validations."""
        # Check classes have SQL mappings
        classes = ontology.get("classes", {})
        for class_name, class_def in classes.items():
            if "maps_to" not in class_def:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="MES Mapping",
                    path=f"classes.{class_name}",
                    message=f"Class '{class_name}' has no SQL mapping",
                    suggestion="Add 'maps_to.sql_table' or 'maps_to.sql_view'"
                ))
        
        # Check properties have SQL columns
        properties = ontology.get("properties", {})
        for prop_name, prop_def in properties.items():
            if "sql_column" not in prop_def:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="MES Mapping",
                    path=f"properties.{prop_name}",
                    message=f"Property '{prop_name}' has no SQL column mapping",
                    suggestion="Add 'sql_column' field"
                ))
        
        # Validate common queries
        queries = ontology.get("common_queries", {})
        for query_name, query_def in queries.items():
            if "sql" not in query_def:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Query",
                    path=f"common_queries.{query_name}",
                    message=f"Query '{query_name}' has no SQL",
                    suggestion="Add 'sql' field with query"
                ))
    
    def _validate_twin_specific(self, ontology: Dict[str, Any]) -> None:
        """Twin ontology specific validations."""
        # Check model definition
        model_def = ontology.get("model_definition", {})
        if "lines" not in model_def:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Model",
                path="model_definition",
                message="No production lines defined",
                suggestion="Add 'lines' list to model_definition"
            ))
        else:
            # Validate each line
            for i, line in enumerate(model_def.get("lines", [])):
                if "equipment_sequence" not in line:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="Model",
                        path=f"model_definition.lines[{i}]",
                        message=f"Line missing equipment_sequence",
                        suggestion="Add equipment_sequence list"
                    ))
        
        # Check control parameters have effects
        control_params = ontology.get("control_parameters", {})
        param_effects = ontology.get("parameter_effects", {})
        
        for param_name in control_params:
            if param_name not in param_effects:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="Parameters",
                    path=f"control_parameters.{param_name}",
                    message=f"Control parameter '{param_name}' has no effects defined",
                    suggestion=f"Add effects in parameter_effects.{param_name}"
                ))
        
        # Check transduction layer
        transduction = ontology.get("transduction_layer", {})
        required_mappings = ["equipment_state_mapping", "mes_record_structure"]
        
        for mapping in required_mappings:
            if mapping not in transduction:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Transduction",
                    path=f"transduction_layer.{mapping}",
                    message=f"Required transduction mapping '{mapping}' is missing",
                    suggestion=f"Add {mapping} to transduction_layer"
                ))
    
    def _validate_database_specific(self, ontology: Dict[str, Any]) -> None:
        """Database schema specific validations."""
        # Check database info
        db_info = ontology.get("database", {})
        if "type" not in db_info:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Database",
                path="database.type",
                message="Database type not specified",
                suggestion="Add 'type' (e.g., SQLite, PostgreSQL)"
            ))
        
        # Check tables have columns
        tables = ontology.get("tables", {})
        for table_name, table_def in tables.items():
            if "columns" not in table_def:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Schema",
                    path=f"tables.{table_name}",
                    message=f"Table '{table_name}' has no columns defined",
                    suggestion="Add 'columns' section"
                ))
            
            # Check for primary key
            if "primary_key" not in table_def:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="Schema",
                    path=f"tables.{table_name}",
                    message=f"Table '{table_name}' has no primary key",
                    suggestion="Define 'primary_key'"
                ))
    
    def _validate_cross_references(self, ontology: Dict[str, Any]) -> None:
        """Validate internal cross-references."""
        # Collect all defined entities
        defined_classes = set(ontology.get("classes", {}).keys())
        defined_properties = set(ontology.get("properties", {}).keys())
        
        # Check relationships reference valid classes
        relationships = ontology.get("relationships", {})
        for rel_name, rel_def in relationships.items():
            if "from" in rel_def and rel_def["from"] not in defined_classes:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Reference",
                    path=f"relationships.{rel_name}.from",
                    message=f"References undefined class '{rel_def['from']}'",
                    suggestion=f"Define class '{rel_def['from']}' in classes section"
                ))
            
            if "to" in rel_def and rel_def["to"] not in defined_classes:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Reference",
                    path=f"relationships.{rel_name}.to",
                    message=f"References undefined class '{rel_def['to']}'",
                    suggestion=f"Define class '{rel_def['to']}' in classes section"
                ))
    
    def _validate_naming_conventions(self, ontology: Dict[str, Any]) -> None:
        """Validate naming conventions."""
        # Check class names (PascalCase)
        classes = ontology.get("classes", {})
        for class_name in classes:
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="Naming",
                    path=f"classes.{class_name}",
                    message=f"Class name '{class_name}' doesn't follow PascalCase",
                    suggestion="Use PascalCase for class names"
                ))
        
        # Check property names (camelCase or snake_case)
        properties = ontology.get("properties", {})
        for prop_name in properties:
            if not (re.match(r'^[a-z][a-zA-Z0-9_]*$', prop_name) or 
                   re.match(r'^[A-Z][a-zA-Z0-9_]*$', prop_name)):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="Naming",
                    path=f"properties.{prop_name}",
                    message=f"Property name '{prop_name}' has unconventional format",
                    suggestion="Use camelCase or snake_case"
                ))
    
    def _validate_data_types(self, ontology: Dict[str, Any]) -> None:
        """Validate data type definitions."""
        valid_types = {"string", "integer", "float", "boolean", "datetime", "date"}
        
        properties = ontology.get("properties", {})
        for prop_name, prop_def in properties.items():
            if isinstance(prop_def, dict) and "type" in prop_def:
                prop_type = prop_def["type"]
                if prop_type not in valid_types:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="Type",
                        path=f"properties.{prop_name}.type",
                        message=f"Unknown type '{prop_type}'",
                        suggestion=f"Use one of: {', '.join(valid_types)}"
                    ))
    
    def _validate_mes_twin_alignment(self, mes: Dict[str, Any], twin: Dict[str, Any]) -> None:
        """Validate alignment between MES and Twin ontologies."""
        # Check twin references MES
        twin_metadata = twin.get("metadata", {})
        imports = twin_metadata.get("imports", [])
        
        has_mes_import = any(imp.get("namespace") == "mes" for imp in imports)
        if not has_mes_import:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="Alignment",
                path="twin:metadata.imports",
                message="Twin ontology doesn't import MES ontology",
                suggestion="Add MES namespace to imports"
            ))
        
        # Check transduction layer maps to MES fields
        transduction = twin.get("transduction_layer", {})
        mes_record = transduction.get("mes_record_structure", {}).get("fields", [])
        mes_properties = set(mes.get("properties", {}).keys())
        
        for field in mes_record:
            if isinstance(field, dict):
                field_name = list(field.keys())[0] if field else None
                if field_name and field_name not in mes_properties:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="Alignment",
                        path=f"twin:transduction_layer.mes_record_structure",
                        message=f"MES record field '{field_name}' not in MES ontology",
                        suggestion="Ensure all generated fields are defined in MES ontology"
                    ))
    
    def _validate_mes_database_alignment(self, mes: Dict[str, Any], db: Dict[str, Any]) -> None:
        """Validate alignment between MES ontology and database schema."""
        # Check all MES properties have database columns
        mes_properties = mes.get("properties", {})
        
        # Collect all database columns
        db_columns = set()
        for table_def in db.get("tables", {}).values():
            if isinstance(table_def, dict) and "columns" in table_def:
                db_columns.update(table_def["columns"].keys())
        
        for prop_name, prop_def in mes_properties.items():
            if isinstance(prop_def, dict):
                sql_column = prop_def.get("sql_column")
                if sql_column and sql_column not in db_columns:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="Alignment",
                        path=f"mes:properties.{prop_name}",
                        message=f"SQL column '{sql_column}' not found in database schema",
                        suggestion="Add column to database or fix mapping"
                    ))
    
    def _validate_twin_database_alignment(self, twin: Dict[str, Any], db: Dict[str, Any]) -> None:
        """Validate alignment between Twin and database."""
        # Check that twin can generate all required database fields
        db_required_fields = set()
        for table_def in db.get("tables", {}).values():
            if isinstance(table_def, dict) and "columns" in table_def:
                for col_name, col_def in table_def["columns"].items():
                    if isinstance(col_def, dict) and not col_def.get("nullable", True):
                        db_required_fields.add(col_name)
        
        # Check twin generates these fields
        transduction = twin.get("transduction_layer", {})
        mes_fields = transduction.get("mes_record_structure", {}).get("fields", [])
        generated_fields = set()
        
        for field in mes_fields:
            if isinstance(field, dict):
                generated_fields.update(field.keys())
        
        missing_fields = db_required_fields - generated_fields
        if missing_fields:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Alignment",
                path="twin:transduction_layer",
                message=f"Twin doesn't generate required DB fields: {missing_fields}",
                suggestion="Add missing fields to transduction layer"
            ))
    
    def print_report(self, issues: Optional[List[ValidationIssue]] = None) -> None:
        """Print validation report."""
        issues = issues or self.issues
        
        if not issues:
            print("✅ Validation passed! No issues found.")
            return
        
        # Group by level
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
        info = [i for i in issues if i.level == ValidationLevel.INFO]
        
        print(f"Validation Report")
        print("=" * 60)
        print(f"Total issues: {len(issues)}")
        print(f"  Errors: {len(errors)}")
        print(f"  Warnings: {len(warnings)}")
        print(f"  Info: {len(info)}")
        print("=" * 60)
        
        if errors:
            print("\n❌ ERRORS (must fix):")
            for issue in errors:
                print(f"\n{issue}")
        
        if warnings:
            print("\n⚠️  WARNINGS (should fix):")
            for issue in warnings:
                print(f"\n{issue}")
        
        if info:
            print("\nℹ️  INFO (nice to fix):")
            for issue in info:
                print(f"\n{issue}")


# Convenience functions
def validate_ontology(path: Path, ontology_type: str = "generic") -> List[ValidationIssue]:
    """Validate a single ontology file."""
    validator = OntologyValidator(ontology_type)
    return validator.validate(path)


def validate_ontology_set(paths: Dict[str, Path]) -> List[ValidationIssue]:
    """
    Validate a set of related ontologies.
    
    Args:
        paths: Dict of {type: path} e.g., {"mes": Path(...), "twin": Path(...)}
    """
    all_issues = []
    ontologies = {}
    
    # Validate each individually
    for ont_type, path in paths.items():
        validator = OntologyValidator(ont_type)
        issues = validator.validate(path)
        all_issues.extend(issues)
        
        # Load for alignment check
        try:
            with open(path, 'r') as f:
                ontologies[ont_type] = yaml.safe_load(f)
        except:
            pass  # Skip if can't load
    
    # Check alignment
    if len(ontologies) > 1:
        validator = OntologyValidator()
        alignment_issues = validator.validate_alignment(ontologies)
        all_issues.extend(alignment_issues)
    
    return all_issues


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ontology_validator.py <ontology_file> [type]")
        print("Types: mes, twin, database, generic")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    ont_type = sys.argv[2] if len(sys.argv) > 2 else "generic"
    
    validator = OntologyValidator(ont_type)
    issues = validator.validate(path)
    validator.print_report(issues)