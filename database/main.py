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


def main():
    """
    Start the FastAPI server with Uvicorn
    
    Configuration options can be set via environment variables:
    - TWIN_API_HOST: Host to bind to (default: 0.0.0.0)
    - TWIN_API_PORT: Port to bind to (default: 8000)
    - TWIN_API_RELOAD: Enable auto-reload (default: True in dev)
    - TWIN_API_LOG_LEVEL: Log level (default: info)
    """
    
    # Get configuration from environment
    host = os.getenv("TWIN_API_HOST", "0.0.0.0")
    port = int(os.getenv("TWIN_API_PORT", "8000"))
    reload = os.getenv("TWIN_API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("TWIN_API_LOG_LEVEL", "info")
    
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
- Swagger UI: http://localhost:{port}/docs
- ReDoc: http://localhost:{port}/redoc
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