"""
Unified test for both old and new ontology structures.

Tests that ontologies are valid regardless of which structure they use.
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List


class TestUnifiedOntologyStructure:
    """Test both old and new ontology structures."""
    
    def get_ontology_files(self) -> List[tuple]:
        """Get all ontology files and their types."""
        ontology_dir = Path(__file__).parent.parent / "ontology"
        
        return [
            # Old structure files
            (ontology_dir / "ontology_spec.yaml", "old_mes"),
            (ontology_dir / "twin_ontology_spec.yaml", "old_twin"),
            # New structure files  
            (ontology_dir / "mes_ontology.yaml", "new_mes"),
            (ontology_dir / "twin_ontology.yaml", "new_twin"),
        ]
    
    @pytest.mark.parametrize("ontology_path,structure_type", [
        (Path(__file__).parent.parent / "ontology" / "ontology_spec.yaml", "old"),
        (Path(__file__).parent.parent / "ontology" / "twin_ontology_spec.yaml", "old"),
        (Path(__file__).parent.parent / "ontology" / "mes_ontology.yaml", "new"),
        (Path(__file__).parent.parent / "ontology" / "twin_ontology.yaml", "new"),
    ])
    def test_ontology_loadable(self, ontology_path: Path, structure_type: str) -> None:
        """Test that ontology files are valid YAML and loadable."""
        if not ontology_path.exists():
            pytest.skip(f"Ontology {ontology_path.name} doesn't exist")
        
        try:
            with open(ontology_path, 'r') as f:
                ontology = yaml.safe_load(f)
            assert isinstance(ontology, dict), "Ontology should be a dictionary"
            assert len(ontology) > 0, "Ontology should not be empty"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {ontology_path.name}: {e}")
    
    def test_metadata_present(self) -> None:
        """Test that all ontologies have metadata (in either format)."""
        for path, ont_type in self.get_ontology_files():
            if not path.exists():
                continue
                
            with open(path, 'r') as f:
                ontology = yaml.safe_load(f)
            
            # Check for metadata in either location
            has_metadata = 'metadata' in ontology or 'ontology' in ontology
            assert has_metadata, f"{path.name} missing metadata section"
            
            # Get metadata regardless of key
            metadata = ontology.get('metadata', ontology.get('ontology', {}))
            
            # Check required fields
            assert 'name' in metadata, f"{path.name} missing name in metadata"
            assert 'version' in metadata, f"{path.name} missing version in metadata"
            assert 'description' in metadata, f"{path.name} missing description in metadata"
    
    def test_structure_consistency(self) -> None:
        """Test that each ontology is internally consistent."""
        for path, ont_type in self.get_ontology_files():
            if not path.exists():
                continue
                
            with open(path, 'r') as f:
                ontology = yaml.safe_load(f)
            
            # Determine structure type
            if 'metadata' in ontology:
                # New structure
                self._validate_new_structure(ontology, path.name)
            elif 'ontology' in ontology:
                # Old structure
                self._validate_old_structure(ontology, path.name)
            else:
                pytest.fail(f"{path.name} has unknown structure")
    
    def _validate_old_structure(self, ontology: Dict[str, Any], filename: str) -> None:
        """Validate old ontology structure."""
        # Old structure should have these sections
        expected_sections = ['ontology', 'classes', 'relationships', 'properties']
        
        for section in expected_sections:
            assert section in ontology, f"{filename} missing {section} section"
        
        # Validate classes
        if 'classes' in ontology:
            assert isinstance(ontology['classes'], dict), f"{filename} classes should be dict"
            
        # Validate relationships
        if 'relationships' in ontology:
            assert isinstance(ontology['relationships'], dict), f"{filename} relationships should be dict"
            
        # Validate properties
        if 'properties' in ontology:
            assert isinstance(ontology['properties'], dict), f"{filename} properties should be dict"
    
    def _validate_new_structure(self, ontology: Dict[str, Any], filename: str) -> None:
        """Validate new ontology structure."""
        # New structure types
        if 'twin' in filename.lower():
            # Twin ontology
            expected = ['metadata', 'tbox', 'rbox', 'properties', 
                       'model_definition', 'behavioral_rules', 
                       'control_parameters', 'parameter_effects', 
                       'transduction_layer']
        else:
            # MES ontology
            expected = ['metadata', 'classes', 'relationships', 
                       'properties', 'business_rules', 'common_queries']
        
        for section in expected:
            assert section in ontology, f"{filename} missing {section} section"
    
    def test_no_conflicting_ontologies(self) -> None:
        """Test that we don't have conflicting ontologies for same purpose."""
        ontology_dir = Path(__file__).parent.parent / "ontology"
        
        # Check if we have both old and new MES ontologies
        old_mes = ontology_dir / "ontology_spec.yaml"
        new_mes = ontology_dir / "mes_ontology.yaml"
        
        if old_mes.exists() and new_mes.exists():
            # Both exist - need to check they don't conflict
            with open(old_mes, 'r') as f:
                old_data = yaml.safe_load(f)
            with open(new_mes, 'r') as f:
                new_data = yaml.safe_load(f)
            
            # Get namespaces
            old_ns = old_data.get('ontology', {}).get('namespace')
            new_ns = new_data.get('metadata', {}).get('namespace')
            
            # If both claim same namespace, that's a problem
            if old_ns and new_ns and old_ns == new_ns:
                pytest.fail(f"Both old and new MES ontologies claim namespace '{old_ns}'")
    
    def test_cross_references_valid(self) -> None:
        """Test that cross-references between ontologies are valid."""
        ontology_dir = Path(__file__).parent.parent / "ontology"
        
        # Load all ontologies
        ontologies = {}
        for path, ont_type in self.get_ontology_files():
            if path.exists():
                with open(path, 'r') as f:
                    ontologies[path.name] = yaml.safe_load(f)
        
        # Check imports/references
        for name, ontology in ontologies.items():
            # Check new-style imports
            if 'metadata' in ontology and 'imports' in ontology['metadata']:
                for imp in ontology['metadata']['imports']:
                    imp_path = imp.get('path', '')
                    if imp_path.startswith('./'):
                        ref_file = imp_path[2:]
                        # Check if referenced file exists
                        ref_path = ontology_dir / ref_file
                        if not ref_path.exists():
                            pytest.fail(f"{name} imports non-existent {ref_file}")
            
            # Check old-style references
            if 'ontology' in ontology:
                related = ontology['ontology'].get('related_ontologies', [])
                for rel in related:
                    imp_path = rel.get('import_path', '')
                    if imp_path.startswith('./'):
                        ref_file = imp_path[2:]
                        ref_path = ontology_dir / ref_file
                        if not ref_path.exists():
                            pytest.fail(f"{name} references non-existent {ref_file}")
    
    def test_determine_active_structure(self) -> None:
        """Determine which ontology structure we should actually use."""
        ontology_dir = Path(__file__).parent.parent / "ontology"
        
        structures = {
            'old': [],
            'new': []
        }
        
        for path, ont_type in self.get_ontology_files():
            if path.exists():
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                
                if 'metadata' in data:
                    structures['new'].append(path.name)
                elif 'ontology' in data:
                    structures['old'].append(path.name)
        
        print("\nOntology Structure Analysis:")
        print(f"Old structure files: {structures['old']}")
        print(f"New structure files: {structures['new']}")
        
        # Recommendation
        if len(structures['new']) > len(structures['old']):
            print("Recommendation: Use NEW structure (metadata, tbox, rbox)")
        elif len(structures['old']) > len(structures['new']):
            print("Recommendation: Use OLD structure (ontology, classes, relationships)")
        else:
            print("WARNING: Mixed structures detected - need to standardize!")
            
        # This test always passes but provides information
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])