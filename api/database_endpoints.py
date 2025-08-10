"""
API endpoints for database management and monitoring
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
import os
import sys

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twin'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from database import SessionDep
from config_manager import ConfigurationManager

router = APIRouter(prefix="/api/database", tags=["database"])


class DatabaseStats(BaseModel):
    """Database statistics response"""
    database_path: str
    file_size_mb: float
    total_tables: int
    total_records: int
    tables: Dict[str, int]


class TableInfo(BaseModel):
    """Information about a database table"""
    name: str
    record_count: int
    columns: List[str]
    sample_data: Optional[List[Dict[str, Any]]] = None


class ConfigInfo(BaseModel):
    """Simulation configuration information"""
    config_id: str
    run_id: Optional[str]
    config_type: str
    description: Optional[str]
    created_at: str
    config_hash: str


class CleanupRequest(BaseModel):
    """Request for database cleanup"""
    category: Optional[str] = Field(None, description="Category to clean: historical, simulation, optimization, monitoring, metadata, logs")
    tables: Optional[List[str]] = Field(None, description="Specific tables to clean")
    older_than_days: Optional[int] = Field(None, description="Remove data older than N days")
    preserve: Optional[List[str]] = Field(None, description="Tables to preserve during cleanup")


@router.get("/stats", response_model=DatabaseStats)
def get_database_stats(session: SessionDep):
    """Get comprehensive database statistics"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mes_database.db")
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    file_size = os.path.getsize(db_path) / (1024 * 1024)  # Convert to MB
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        table_stats = {}
        total_records = 0
        
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name[0]}")
            count = cursor.fetchone()[0]
            table_stats[table_name[0]] = count
            total_records += count
    
    return DatabaseStats(
        database_path=db_path,
        file_size_mb=round(file_size, 2),
        total_tables=len(tables),
        total_records=total_records,
        tables=table_stats
    )


@router.get("/tables", response_model=List[TableInfo])
def list_tables(
    session: SessionDep,
    include_sample: bool = Query(False, description="Include sample data from each table"),
    limit: int = Query(5, description="Number of sample rows to include")
):
    """List all database tables with their structure and optional sample data"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mes_database.db")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        table_info_list = []
        
        for table_name in tables:
            table_name = table_name[0]
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Get sample data if requested
            sample_data = None
            if include_sample and count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                rows = cursor.fetchall()
                sample_data = [dict(zip(columns, row)) for row in rows]
                
                # Convert datetime objects to strings
                for row in sample_data:
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            row[key] = value.isoformat()
            
            table_info_list.append(TableInfo(
                name=table_name,
                record_count=count,
                columns=columns,
                sample_data=sample_data
            ))
    
    return table_info_list


@router.get("/configs", response_model=List[ConfigInfo])
def list_configurations(
    session: SessionDep,
    config_type: Optional[str] = Query(None, description="Filter by config type: full, delta, base"),
    limit: int = Query(100, description="Maximum number of configs to return")
):
    """List simulation configurations stored in database"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mes_database.db")
    config_mgr = ConfigurationManager(db_path)
    
    configs = config_mgr.list_configs(config_type=config_type, limit=limit)
    
    return [
        ConfigInfo(
            config_id=cfg['config_id'],
            run_id=cfg.get('run_id'),
            config_type=cfg['config_type'],
            description=cfg.get('description'),
            created_at=cfg['created_at'],
            config_hash=cfg['config_hash']
        )
        for cfg in configs
    ]


@router.get("/config/{config_id}")
def get_configuration(config_id: str, session: SessionDep):
    """Get a specific configuration by ID"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mes_database.db")
    config_mgr = ConfigurationManager(db_path)
    
    config = config_mgr.get_config(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
    
    return config


@router.post("/cleanup")
def cleanup_database(request: CleanupRequest, session: SessionDep):
    """
    Perform selective database cleanup
    
    Note: This endpoint is restricted to cleaning non-critical data.
    For safety, it does not allow dropping tables or cleaning core data.
    """
    
    # Define safe categories for cleanup
    SAFE_CATEGORIES = {
        'logs': ['sync_health_log', 'confidence_tracking'],
        'simulation': ['simulation_data'],
        'optimization': ['optimization_results']
    }
    
    # Validate category if provided
    if request.category and request.category not in SAFE_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Category must be one of: {list(SAFE_CATEGORIES.keys())}"
        )
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mes_database.db")
    
    cleaned_tables = []
    total_removed = 0
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Determine tables to clean
            tables_to_clean = []
            
            if request.category:
                tables_to_clean = SAFE_CATEGORIES[request.category]
            elif request.tables:
                # Filter to only safe tables
                all_safe_tables = [t for tables in SAFE_CATEGORIES.values() for t in tables]
                tables_to_clean = [t for t in request.tables if t in all_safe_tables]
                
                if len(tables_to_clean) != len(request.tables):
                    unsafe = set(request.tables) - set(tables_to_clean)
                    raise HTTPException(
                        status_code=400,
                        detail=f"Some tables are not safe to clean: {unsafe}"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Must specify either category or tables to clean"
                )
            
            # Apply preserve filter
            if request.preserve:
                tables_to_clean = [t for t in tables_to_clean if t not in request.preserve]
            
            # Clean tables
            for table in tables_to_clean:
                # Check if table exists
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table}'
                """)
                if not cursor.fetchone():
                    continue
                
                # Get count before cleaning
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                before_count = cursor.fetchone()[0]
                
                # Apply age filter if specified
                if request.older_than_days:
                    # Tables with timestamp columns
                    timestamp_columns = {
                        'sync_health_log': 'timestamp',
                        'simulation_data': 'timestamp',
                        'optimization_results': 'created_at'
                    }
                    
                    if table in timestamp_columns:
                        from datetime import datetime, timedelta
                        cutoff = (datetime.now() - timedelta(days=request.older_than_days)).isoformat()
                        cursor.execute(f"""
                            DELETE FROM {table} 
                            WHERE {timestamp_columns[table]} < ?
                        """, (cutoff,))
                    else:
                        cursor.execute(f"DELETE FROM {table}")
                else:
                    cursor.execute(f"DELETE FROM {table}")
                
                # Get count after cleaning
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                after_count = cursor.fetchone()[0]
                
                removed = before_count - after_count
                if removed > 0:
                    cleaned_tables.append({
                        'table': table,
                        'removed': removed,
                        'remaining': after_count
                    })
                    total_removed += removed
            
            conn.commit()
            
            # Vacuum if significant cleanup
            if total_removed > 1000:
                conn.execute("VACUUM")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        'success': True,
        'total_removed': total_removed,
        'cleaned_tables': cleaned_tables,
        'message': f"Cleaned {len(cleaned_tables)} tables, removed {total_removed} records"
    }


@router.get("/health")
def database_health(session: SessionDep):
    """Check database health and integrity"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mes_database.db")
    
    if not os.path.exists(db_path):
        return {'status': 'error', 'message': 'Database file not found'}
    
    issues = []
    warnings = []
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity != "ok":
            issues.append(f"Integrity check failed: {integrity}")
        
        # Check foreign keys
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        if fk_issues:
            issues.append(f"Foreign key violations: {len(fk_issues)}")
        
        # Check for orphaned records
        cursor.execute("""
            SELECT COUNT(*) FROM simulation_data sd
            LEFT JOIN twin_runs tr ON sd.run_id = tr.run_id
            WHERE tr.run_id IS NULL
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned > 0:
            warnings.append(f"Found {orphaned} orphaned simulation records")
        
        # Check table counts
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        table_count = cursor.fetchone()[0]
        
        # Check if critical tables exist
        critical_tables = ['mes_data', 'twin_runs', 'equipment_metadata']
        for table in critical_tables:
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table}'
            """)
            if not cursor.fetchone():
                issues.append(f"Critical table missing: {table}")
    
    status = 'healthy' if not issues else 'unhealthy'
    if not issues and warnings:
        status = 'warning'
    
    return {
        'status': status,
        'database_path': db_path,
        'table_count': table_count,
        'issues': issues,
        'warnings': warnings,
        'timestamp': datetime.now().isoformat()
    }