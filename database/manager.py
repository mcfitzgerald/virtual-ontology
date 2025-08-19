"""Database manager using SQLModel with YAML ontologies"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlmodel import create_engine, SQLModel, Session
import yaml
import json
import pandas as pd
from datetime import datetime

from database.models import *


class TwinDatabaseManager:
    """Manage twin database with YAML ontologies"""
    
    def __init__(self, 
                 db_path: Optional[Path] = None,
                 ontology_path: Optional[Path] = None,
                 manifest_dir: Optional[Path] = None):
        
        # Database setup
        self.db_path = db_path or Path("data/twin_database.db")
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False}
        )
        
        # YAML file paths
        self.ontology_path = ontology_path or Path("ontology/twin_ontology.yaml")
        self.manifest_dir = manifest_dir or Path("manifests/")
        
        # Cache for YAML data
        self._ontology_cache = None
        self._manifest_cache = {}
        
    def create_all_tables(self):
        """Create all database tables"""
        SQLModel.metadata.create_all(self.engine)
        print(f"✓ Created tables in {self.db_path}")
        
    def load_ontology(self) -> Dict[str, Any]:
        """Load ontology from YAML file (cached)"""
        if self._ontology_cache is None:
            with open(self.ontology_path) as f:
                self._ontology_cache = yaml.safe_load(f)
        return self._ontology_cache
    
    def load_manifest(self, manifest_name: str) -> Dict[str, Any]:
        """Load manifest from YAML file (cached)"""
        if manifest_name not in self._manifest_cache:
            manifest_path = self.manifest_dir / f"{manifest_name}.yaml"
            with open(manifest_path) as f:
                self._manifest_cache[manifest_name] = yaml.safe_load(f)
        return self._manifest_cache[manifest_name]
    
    def import_historical_data(self, csv_path: Path):
        """Import historical MES data from CSV"""
        df = pd.read_csv(csv_path)
        
        with Session(self.engine) as session:
            # Check if already imported
            existing = session.query(HistoricalMESData).first()
            if existing:
                print("Historical data already imported")
                return
            
            # Import records
            for _, row in df.iterrows():
                record = HistoricalMESData(
                    timestamp=pd.to_datetime(row['Timestamp']),
                    production_order_id=row.get('ProductionOrderID'),
                    line_id=str(row['LineID']),
                    equipment_id=row['EquipmentID'],
                    equipment_type=row['EquipmentType'],
                    product_id=row.get('ProductID'),
                    product_name=row.get('ProductName'),
                    machine_status=row['MachineStatus'],
                    downtime_reason=row.get('DowntimeReason'),
                    good_units_produced=int(row['GoodUnitsProduced']),
                    scrap_units_produced=int(row['ScrapUnitsProduced']),
                    target_rate_units_per_5min=int(row['TargetRate_units_per_5min']),
                    standard_cost_per_unit=float(row['StandardCost_per_unit']),
                    sale_price_per_unit=float(row['SalePrice_per_unit']),
                    availability_score=float(row['Availability_Score']),
                    performance_score=float(row['Performance_Score']),
                    quality_score=float(row['Quality_Score']),
                    oee_score=float(row['OEE_Score']),
                    energy_consumption_kwh=row.get('Energy_Consumption_kWh'),
                    source="historical"
                )
                session.add(record)
            
            session.commit()
            print(f"✓ Imported {len(df)} historical records")
    
    def sync_configurations_from_manifests(self):
        """Sync equipment and product configs from manifest YAMLs"""
        
        with Session(self.engine) as session:
            # Load and sync equipment manifest
            equipment_manifest = self.load_manifest("equipment_manifest")
            
            for eq_id, eq_data in equipment_manifest.get('equipment', {}).items():
                # Check if exists
                existing = session.get(EquipmentConfig, eq_id)
                
                if existing:
                    # Update existing - skip computed properties
                    for key, value in eq_data.items():
                        # Skip properties that are computed from JSON fields
                        if key in ['failure_patterns', 'performance_by_product']:
                            continue
                        if hasattr(existing, key) and not key.startswith('_'):
                            try:
                                setattr(existing, key, value)
                            except AttributeError:
                                # Skip read-only properties
                                pass
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    config = EquipmentConfig(
                        equipment_id=eq_id,
                        equipment_type=eq_data['type'],
                        line_id=eq_data.get('line', 'LINE1'),
                        position=eq_data.get('position'),
                        base_rate=eq_data['base_rate'],
                        mtbf=eq_data['mtbf'],
                        mttr=eq_data['mttr'],
                        energy_consumption_rate=eq_data.get('energy_consumption_rate', 5.0),
                        failure_patterns_json=json.dumps(
                            eq_data.get('failure_patterns', {})
                        ),
                        performance_by_product_json=json.dumps(
                            eq_data.get('performance_by_product', {})
                        )
                    )
                    session.add(config)
            
            # Load and sync production manifest
            production_manifest = self.load_manifest("production_manifest")
            
            for prod_id, prod_data in production_manifest.get('products', {}).items():
                existing = session.get(ProductConfig, prod_id)
                
                if not existing:
                    config = ProductConfig(
                        product_id=prod_id,
                        product_name=prod_data['name'],
                        target_rate_units_per_5min=prod_data['target_rate_units_per_5min'],
                        standard_cost_per_unit=prod_data['standard_cost_per_unit'],
                        sale_price_per_unit=prod_data['sale_price_per_unit'],
                        scrap_rate_normal=prod_data['scrap_rates']['normal'],
                        scrap_rate_startup=prod_data['scrap_rates']['startup'],
                        scrap_rate_quality_issue=prod_data['scrap_rates'].get('quality_issue'),
                        properties_json=json.dumps(prod_data.get('properties', {}))
                    )
                    session.add(config)
            
            session.commit()
            print("✓ Synced configurations from manifests")
    
    def get_ontology_version(self) -> str:
        """Get version of current ontology"""
        ontology = self.load_ontology()
        return ontology.get('metadata', {}).get('version', '1.0.0')
    
    def get_manifest_version(self) -> str:
        """Get combined version hash of manifests"""
        import hashlib
        combined = ""
        for manifest_file in sorted(self.manifest_dir.glob("*.yaml")):
            with open(manifest_file) as f:
                combined += f.read()
        return hashlib.md5(combined.encode()).hexdigest()[:8]