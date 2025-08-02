from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from sqlmodel import select, inspect, text
import sqlalchemy
from pydantic import BaseModel

from database import create_db_and_tables, import_csv_data, SessionDep, engine
from models import MESData
from schemas import MESDataResponse

app = FastAPI(
    title="MES Data API",
    description="Simple queryable API for Manufacturing Execution System data",
    version="2.0.0"
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    import_csv_data()


class SQLQuery(BaseModel):
    sql: str
    limit: Optional[int] = 1000

class SQLResponse(BaseModel):
    query: str
    columns: List[str]
    data: List[Dict[str, Any]]
    row_count: int
    limited: bool

@app.get("/")
def read_root():
    return {"message": "MES Data API", "version": "2.0.0"}


@app.post("/query", response_model=SQLResponse)
def execute_query(query: SQLQuery, session: SessionDep):
    """Execute a SQL query against the MES database
    
    Safety features:
    - Read-only queries only (SELECT statements)
    - Row limit to prevent excessive data transfer
    - Timeout protection (handled by SQLite)
    """
    sql = query.sql.strip()
    
    # Basic safety check - only allow SELECT statements
    if not sql.upper().startswith('SELECT'):
        raise HTTPException(
            status_code=400, 
            detail="Only SELECT statements are allowed"
        )
    
    # Check for dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
    sql_upper = sql.upper()
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Query contains forbidden keyword: {keyword}"
            )
    
    try:
        # Apply limit if not already present and limit is specified
        limited = False
        if query.limit and 'LIMIT' not in sql_upper:
            sql = f"{sql} LIMIT {query.limit + 1}"  # Add 1 to detect if limit was hit
            limited = True
        
        # Execute the query
        result = session.exec(text(sql))
        
        # Get column names
        columns = list(result.keys()) if result.returns_rows else []
        
        # Fetch all results
        rows = result.fetchall() if result.returns_rows else []
        
        # Check if we hit the limit
        if limited and len(rows) > query.limit:
            rows = rows[:query.limit]
            limited = True
        else:
            limited = False
        
        # Convert rows to list of dicts
        data = [dict(zip(columns, row)) for row in rows]
        
        # Convert datetime objects to strings for JSON serialization
        for row in data:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        return SQLResponse(
            query=query.sql,
            columns=columns,
            data=data,
            row_count=len(data),
            limited=limited
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Query execution failed: {str(e)}"
        )

@app.get("/schema")
def get_schema() -> Dict[str, Any]:
    """Get database schema information for generating YAML configuration"""
    inspector = inspect(engine)
    
    # Get table information
    tables = {}
    for table_name in inspector.get_table_names():
        table_info = {
            "columns": [],
            "indexes": [],
            "primary_key": None
        }
        
        # Get columns
        for column in inspector.get_columns(table_name):
            col_info = {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "default": str(column["default"]) if column["default"] else None,
            }
            
            # Map SQLAlchemy types to simple types
            type_str = str(column["type"])
            if "INTEGER" in type_str or "BIGINT" in type_str:
                col_info["simple_type"] = "integer"
            elif "VARCHAR" in type_str or "TEXT" in type_str:
                col_info["simple_type"] = "string"
            elif "FLOAT" in type_str or "REAL" in type_str or "DOUBLE" in type_str:
                col_info["simple_type"] = "float"
            elif "DATETIME" in type_str or "TIMESTAMP" in type_str:
                col_info["simple_type"] = "datetime"
            elif "DATE" in type_str:
                col_info["simple_type"] = "date"
            elif "BOOLEAN" in type_str:
                col_info["simple_type"] = "boolean"
            else:
                col_info["simple_type"] = "string"
            
            table_info["columns"].append(col_info)
        
        # Get primary key
        pk = inspector.get_pk_constraint(table_name)
        if pk:
            table_info["primary_key"] = pk["constrained_columns"]
        
        # Get indexes
        for index in inspector.get_indexes(table_name):
            table_info["indexes"].append({
                "name": index["name"],
                "columns": index["column_names"],
                "unique": index["unique"]
            })
        
        tables[table_name] = table_info
    
    # Get model field information from SQLModel
    model_info = {}
    if hasattr(MESData, "model_fields"):
        for field_name, field in MESData.model_fields.items():
            field_info = {
                "type": str(field.annotation) if hasattr(field, 'annotation') else "unknown",
                "required": field.is_required() if hasattr(field, 'is_required') else True,
                "default": str(field.default) if field.default is not None else None
            }
            model_info[field_name] = field_info
    
    return {
        "database": {
            "type": "SQLite",
            "file": "../data/mes_database.db",
            "tables": tables
        },
        "model_fields": model_info,
        "api_endpoint": "/data",
        "openapi_schema": app.openapi()["components"]["schemas"].get("MESDataResponse", {})
    }


@app.get("/data", response_model=List[MESDataResponse])
def get_data(
    session: SessionDep,
    # Text field filters
    production_order_id: Optional[str] = None,
    line_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    equipment_type: Optional[str] = None,
    product_id: Optional[str] = None,
    product_name: Optional[str] = None,
    machine_status: Optional[str] = None,
    downtime_reason: Optional[str] = None,
    # Timestamp filters
    timestamp_from: Optional[datetime] = None,
    timestamp_to: Optional[datetime] = None,
    # Numeric range filters
    good_units_min: Optional[int] = None,
    good_units_max: Optional[int] = None,
    scrap_units_min: Optional[int] = None,
    scrap_units_max: Optional[int] = None,
    target_rate_min: Optional[int] = None,
    target_rate_max: Optional[int] = None,
    oee_score_min: Optional[float] = None,
    oee_score_max: Optional[float] = None,
    availability_score_min: Optional[float] = None,
    availability_score_max: Optional[float] = None,
    performance_score_min: Optional[float] = None,
    performance_score_max: Optional[float] = None,
    quality_score_min: Optional[float] = None,
    quality_score_max: Optional[float] = None,
    # Pagination
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0)
):
    """Get MES data with flexible filtering options"""
    query = select(MESData)
    
    # Apply text filters
    if production_order_id:
        query = query.where(MESData.production_order_id == production_order_id)
    if line_id:
        query = query.where(MESData.line_id == line_id)
    if equipment_id:
        query = query.where(MESData.equipment_id == equipment_id)
    if equipment_type:
        query = query.where(MESData.equipment_type == equipment_type)
    if product_id:
        query = query.where(MESData.product_id == product_id)
    if product_name:
        query = query.where(MESData.product_name == product_name)
    if machine_status:
        query = query.where(MESData.machine_status == machine_status)
    if downtime_reason:
        query = query.where(MESData.downtime_reason == downtime_reason)
    
    # Apply timestamp filters
    if timestamp_from:
        query = query.where(MESData.timestamp >= timestamp_from)
    if timestamp_to:
        query = query.where(MESData.timestamp <= timestamp_to)
    
    # Apply numeric range filters
    if good_units_min is not None:
        query = query.where(MESData.good_units_produced >= good_units_min)
    if good_units_max is not None:
        query = query.where(MESData.good_units_produced <= good_units_max)
    if scrap_units_min is not None:
        query = query.where(MESData.scrap_units_produced >= scrap_units_min)
    if scrap_units_max is not None:
        query = query.where(MESData.scrap_units_produced <= scrap_units_max)
    if target_rate_min is not None:
        query = query.where(MESData.target_rate_units_per_5min >= target_rate_min)
    if target_rate_max is not None:
        query = query.where(MESData.target_rate_units_per_5min <= target_rate_max)
    if oee_score_min is not None:
        query = query.where(MESData.oee_score >= oee_score_min)
    if oee_score_max is not None:
        query = query.where(MESData.oee_score <= oee_score_max)
    if availability_score_min is not None:
        query = query.where(MESData.availability_score >= availability_score_min)
    if availability_score_max is not None:
        query = query.where(MESData.availability_score <= availability_score_max)
    if performance_score_min is not None:
        query = query.where(MESData.performance_score >= performance_score_min)
    if performance_score_max is not None:
        query = query.where(MESData.performance_score <= performance_score_max)
    if quality_score_min is not None:
        query = query.where(MESData.quality_score >= quality_score_min)
    if quality_score_max is not None:
        query = query.where(MESData.quality_score <= quality_score_max)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute and return
    results = session.exec(query).all()
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)