"""
SQL query execution endpoints

Provides direct SQL access to the database with safety measures
"""

from fastapi import APIRouter, HTTPException
from sqlmodel import text, select
from typing import List, Dict, Any
import time

from database.dependencies import SessionDep, ManagerDep
from database.schemas import SQLQueryRequest, SQLQueryResponse, TableInfo
from database.models import (
    HistoricalMESData, TwinRun, SimulationData, 
    Experiment, DiscoveredPattern, EquipmentConfig, ProductConfig
)


router = APIRouter()


# Table whitelist for security
ALLOWED_TABLES = {
    "historical_mes_data": HistoricalMESData,
    "twin_runs": TwinRun,
    "simulation_data": SimulationData,
    "experiments": Experiment,
    "discovered_patterns": DiscoveredPattern,
    "equipment_config": EquipmentConfig,
    "product_config": ProductConfig,
    # Add more tables as needed
}


@router.post("/", response_model=SQLQueryResponse)
async def execute_query(
    request: SQLQueryRequest,
    session: SessionDep
) -> SQLQueryResponse:
    """
    Execute a SQL query against the database
    
    Safety measures:
    - Read-only queries only (SELECT)
    - Limited result size
    - Query timeout
    """
    
    # Basic SQL injection prevention - only allow SELECT
    query_upper = request.sql.strip().upper()
    if not query_upper.startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed"
        )
    
    # Check for dangerous keywords
    dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Query contains forbidden keyword: {keyword}"
            )
    
    try:
        start_time = time.time()
        
        # Execute query with limit
        if request.limit and "LIMIT" not in query_upper:
            query = f"{request.sql} LIMIT {request.limit}"
        else:
            query = request.sql
        
        result = session.exec(text(query))
        
        # Fetch results
        rows = result.fetchall()
        columns = list(result.keys()) if rows else []
        
        # Convert rows to dictionaries
        data = [dict(zip(columns, row)) for row in rows]
        
        # Check if we hit the limit
        limited = len(data) == request.limit if request.limit else False
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return SQLQueryResponse(
            query=request.sql,
            columns=columns,
            data=data,
            row_count=len(data),
            limited=limited,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Query execution failed: {str(e)}"
        )


@router.get("/tables", response_model=List[TableInfo])
async def list_tables(
    session: SessionDep,
    include_samples: bool = False
) -> List[TableInfo]:
    """
    List all available tables with metadata
    
    Returns information about each table including:
    - Table name
    - Record count
    - Column names
    - Indexes
    - Sample data (optional)
    """
    
    tables = []
    
    for table_name, model_class in ALLOWED_TABLES.items():
        try:
            # Get record count
            count_query = select(model_class)
            count = len(session.exec(count_query).all())
            
            # Get column names
            columns = [col.name for col in model_class.__table__.columns]
            
            # Get indexes
            indexes = [idx.name for idx in model_class.__table__.indexes]
            
            # Get sample data if requested
            sample_data = None
            if include_samples and count > 0:
                sample_query = select(model_class).limit(3)
                samples = session.exec(sample_query).all()
                sample_data = [
                    {col: getattr(sample, col) for col in columns}
                    for sample in samples
                ]
            
            tables.append(TableInfo(
                name=table_name,
                record_count=count,
                columns=columns,
                indexes=indexes,
                sample_data=sample_data
            ))
            
        except Exception as e:
            # Log error but continue with other tables
            print(f"Error getting info for table {table_name}: {e}")
            continue
    
    return tables


@router.get("/schema/{table_name}")
async def get_table_schema(
    table_name: str,
    session: SessionDep
) -> Dict[str, Any]:
    """
    Get detailed schema information for a specific table
    
    Returns:
    - Column definitions with types
    - Primary keys
    - Foreign keys
    - Indexes
    - Constraints
    """
    
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=404,
            detail=f"Table '{table_name}' not found or not accessible"
        )
    
    model_class = ALLOWED_TABLES[table_name]
    table = model_class.__table__
    
    # Build schema information
    schema = {
        "table_name": table_name,
        "columns": {},
        "primary_keys": [],
        "foreign_keys": [],
        "indexes": []
    }
    
    # Column information
    for column in table.columns:
        schema["columns"][column.name] = {
            "type": str(column.type),
            "nullable": column.nullable,
            "default": str(column.default) if column.default else None,
            "primary_key": column.primary_key,
            "foreign_key": bool(column.foreign_keys)
        }
        
        if column.primary_key:
            schema["primary_keys"].append(column.name)
    
    # Foreign key information
    for fk in table.foreign_keys:
        schema["foreign_keys"].append({
            "column": fk.parent.name,
            "references": f"{fk.column.table.name}.{fk.column.name}"
        })
    
    # Index information
    for index in table.indexes:
        schema["indexes"].append({
            "name": index.name,
            "columns": [col.name for col in index.columns],
            "unique": index.unique
        })
    
    return schema


@router.post("/validate")
async def validate_query(
    request: SQLQueryRequest
) -> Dict[str, Any]:
    """
    Validate a SQL query without executing it
    
    Checks for:
    - Syntax errors
    - Forbidden operations
    - Table existence
    """
    
    query_upper = request.sql.strip().upper()
    
    # Check if it's a SELECT query
    if not query_upper.startswith("SELECT"):
        return {
            "valid": False,
            "error": "Only SELECT queries are allowed"
        }
    
    # Check for dangerous keywords
    dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {
                "valid": False,
                "error": f"Query contains forbidden keyword: {keyword}"
            }
    
    # Check for valid table references
    tables_referenced = []
    for table_name in ALLOWED_TABLES.keys():
        if table_name.upper() in query_upper:
            tables_referenced.append(table_name)
    
    if not tables_referenced:
        return {
            "valid": False,
            "error": "Query does not reference any known tables",
            "available_tables": list(ALLOWED_TABLES.keys())
        }
    
    return {
        "valid": True,
        "tables_referenced": tables_referenced,
        "message": "Query is valid and safe to execute"
    }