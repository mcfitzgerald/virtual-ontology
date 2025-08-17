#!/usr/bin/env python3
"""Configuration Manager for Virtual Twin Simulations
Handles storage and retrieval of simulation configurations in database
"""

import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from sqlite3 import Connection, Cursor
import logging
from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages simulation configurations with database storage
    Provides efficient storage using deltas and on-demand generation
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the ConfigurationManager.
        
        Args:
            db_path: Path to SQLite database. If None, uses path from configuration.
            
        Raises:
            KeyError: If database path not found in configuration.

        """
        self.loader = ConfigLoader()
        self.config = self.loader.config
        
        if db_path is None:
            db_path = self.config["database"]["path"]
            
        self.db_path: str = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize configuration storage tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Table for storing full configurations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulation_configs (
                    config_id TEXT PRIMARY KEY,
                    run_id TEXT REFERENCES twin_runs(run_id),
                    config_type TEXT CHECK(config_type IN ('full', 'delta', 'base')),
                    config_json TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    is_archived BOOLEAN DEFAULT 0
                )
            """)
            
            # Index for quick lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_config_run 
                ON simulation_configs(run_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_config_hash 
                ON simulation_configs(config_hash)
            """)
            
            conn.commit()
    
    def _calculate_hash(self, config: Dict[str, Any]) -> str:
        """Calculate hash of configuration for deduplication"""
        # Remove metadata fields that change every time
        config_copy = config.copy()
        if 'twin_metadata' in config_copy:
            metadata = config_copy['twin_metadata'].copy()
            metadata.pop('transformation_timestamp', None)
            config_copy['twin_metadata'] = metadata
        
        config_str = json.dumps(config_copy, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def store_config(
        self,
        config: Dict[str, Any],
        run_id: Optional[str] = None,
        config_type: str = 'full',
        description: Optional[str] = None
    ) -> str:
        """Store configuration in database
        
        Args:
            config: Configuration dictionary
            run_id: Associated simulation run ID
            config_type: Type of config (full, delta, base)
            description: Optional description
            
        Returns:
            config_id of stored configuration

        """
        config_hash = self._calculate_hash(config)
        
        # Check if identical config already exists
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT config_id FROM simulation_configs 
                WHERE config_hash = ?
            """, (config_hash,))
            
            existing = cursor.fetchone()
            if existing:
                logger.info(f"Config already exists with ID: {existing[0]}")
                return existing[0]
            
            # Generate new config ID
            timestamp: str = datetime.now().strftime("%Y%m%d-%H%M%S")
            config_id = f"cfg-{timestamp}-{config_hash[:8]}"
            
            # Store configuration
            cursor.execute("""
                INSERT INTO simulation_configs 
                (config_id, run_id, config_type, config_json, config_hash, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                config_id,
                run_id,
                config_type,
                json.dumps(config),
                config_hash,
                description
            ))
            
            conn.commit()
            logger.info(f"Stored configuration: {config_id}")
            
        return config_id
    
    def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve configuration by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT config_json FROM simulation_configs 
                WHERE config_id = ?
            """, (config_id,))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            
        return None
    
    def get_config_by_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve configuration associated with a run"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT config_json FROM simulation_configs 
                WHERE run_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (run_id,))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            
        return None
    
    def list_configs(
        self,
        config_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List available configurations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query: str = """
                SELECT config_id, run_id, config_type, description, 
                       created_at, config_hash
                FROM simulation_configs 
                WHERE is_archived = 0
            """
            
            params: List[Any] = []
            if config_type:
                query += " AND config_type = ?"
                params.append(config_type)
            
            if limit is None:
                limit = self.config["display_limits"]["max_config_list"]
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            configs: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                configs.append({
                    'config_id': row[0],
                    'run_id': row[1],
                    'config_type': row[2],
                    'description': row[3],
                    'created_at': row[4],
                    'config_hash': row[5]
                })
            
        return configs
    
    def archive_config(self, config_id: str) -> bool:
        """Archive a configuration (soft delete)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE simulation_configs 
                SET is_archived = 1 
                WHERE config_id = ?
            """, (config_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_old_configs(self, days_to_keep: Optional[int] = None) -> int:
        """Archive configs older than specified days"""
        if days_to_keep is None:
            days_to_keep = self.config["retention"]["config_history_days"]
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE simulation_configs 
                SET is_archived = 1 
                WHERE created_at < datetime('now', '-' || ? || ' days')
                AND is_archived = 0
            """, (days_to_keep,))
            
            conn.commit()
            archived_count = cursor.rowcount
            
            if archived_count > 0:
                logger.info(f"Archived {archived_count} old configurations")
            
        return archived_count
    
    def migrate_file_configs(self, config_dir: Optional[str] = None) -> int:
        """Migrate existing file-based configs to database
        
        Args:
            config_dir: Directory containing config JSON files
            
        Returns:
            Number of configs migrated

        """
        if config_dir is None:
            config_dir = self.config["paths"]["config_dir"]
            
        config_path: Path = Path(config_dir)
        if not config_path.exists():
            logger.warning(f"Config directory not found: {config_dir}")
            return 0
        
        migrated: int = 0
        for config_file in config_path.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Extract run_id from filename if possible
                # Format: sim-YYYYMMDD-HHMMSS-hash.json
                filename: str = config_file.stem
                parts: List[str] = filename.split('-')
                
                # Try to find matching run in database
                run_id: Optional[str] = None
                if len(parts) >= 4:
                    # Reconstruct potential timestamp
                    timestamp_str: str = f"{parts[1]}-{parts[2]}"
                    
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT run_id FROM twin_runs 
                            WHERE datetime(started_at) LIKE ?
                            LIMIT 1
                        """, (f"%{parts[1]}%{parts[2]}%",))
                        
                        result = cursor.fetchone()
                        if result:
                            run_id = result[0]
                
                # Store in database
                description: str = f"Migrated from {config_file.name}"
                config_id = self.store_config(
                    config,
                    run_id=run_id,
                    config_type='full',
                    description=description
                )
                
                logger.info(f"Migrated {config_file.name} -> {config_id}")
                migrated += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate {config_file}: {e}")
        
        return migrated
    
    def export_config_to_file(
        self,
        config_id: str,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """Export configuration to file for archival
        
        Args:
            config_id: Configuration ID to export
            output_dir: Directory to save file
            
        Returns:
            Path to exported file or None if failed

        """
        if output_dir is None:
            output_dir = self.config["paths"]["export_dir"]
            
        config = self.get_config(config_id)
        if not config:
            logger.error(f"Config not found: {config_id}")
            return None
        
        output_path: Path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename: str = f"{config_id}.json"
        file_path: Path = output_path / filename
        
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Exported config to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return None