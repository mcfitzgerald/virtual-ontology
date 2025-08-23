"""
Main entry point for Virtual Twin Database API server

Run with:
    python -m database.main
    
Or use the management script:
    ./twin.sh start
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration loader
from config.config_loader import ConfigLoader, ConfigurationError

# Load database configuration
try:
    db_config = ConfigLoader.load_config('database')
except ConfigurationError as e:
    print(f"ERROR: Failed to load database configuration: {e}")
    sys.exit(1)


def main():
    """
    Start the FastAPI server with Uvicorn
    
    Configuration options can be set via environment variables:
    - TWIN_API_HOST: Host to bind to (default: 0.0.0.0)
    - TWIN_API_PORT: Port to bind to (default: 8000)
    - TWIN_API_RELOAD: Enable auto-reload (default: True in dev)
    - TWIN_API_LOG_LEVEL: Log level (default: info)
    """
    
    # Get configuration from config file, allow environment override
    host = os.getenv("TWIN_API_HOST", db_config['api']['host'])
    port = int(os.getenv("TWIN_API_PORT", db_config['api']['port']))
    reload = os.getenv("TWIN_API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("TWIN_API_LOG_LEVEL", db_config['logging']['level'])
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           Virtual Twin Database API Server v4.0.0               ║
╚══════════════════════════════════════════════════════════════════╝

Starting server...
- Host: {host}
- Port: {port}
- Auto-reload: {reload}
- Log level: {log_level}

API Documentation will be available at:
- Swagger UI: {db_config['api']['base_url']}:{port}{db_config['api']['endpoints']['swagger_ui']}
- ReDoc: {db_config['api']['base_url']}:{port}{db_config['api']['endpoints']['redoc']}
    """)
    
    # Run the server
    uvicorn.run(
        "database.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()