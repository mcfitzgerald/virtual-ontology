#!/usr/bin/env python3
"""
Migration script to move file-based configs to database
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'twin'))

from twin.config_manager import ConfigurationManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run config migration"""
    
    # Initialize config manager
    config_manager = ConfigurationManager(
        db_path=str(project_root / "data" / "mes_database.db")
    )
    
    # Migrate existing configs
    logger.info("Starting config migration...")
    migrated = config_manager.migrate_file_configs(
        config_dir=str(project_root / "twin" / "configs")
    )
    
    logger.info(f"Successfully migrated {migrated} configurations")
    
    # List migrated configs
    configs = config_manager.list_configs(limit=20)
    logger.info(f"\nFound {len(configs)} configurations in database:")
    for cfg in configs:
        logger.info(f"  - {cfg['config_id']}: {cfg.get('description', 'No description')}")
    
    # Archive the file configs
    config_dir = project_root / "twin" / "configs"
    archive_dir = project_root / "data" / "simulation_configs" / "archive"
    
    if config_dir.exists():
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\nMoving config files to archive: {archive_dir}")
        import shutil
        for config_file in config_dir.glob("*.json"):
            dest = archive_dir / config_file.name
            shutil.move(str(config_file), str(dest))
            logger.info(f"  Archived: {config_file.name}")
        
        # Remove empty configs directory
        try:
            config_dir.rmdir()
            logger.info(f"Removed empty directory: {config_dir}")
        except:
            pass
    
    logger.info("\nMigration complete!")


if __name__ == "__main__":
    main()