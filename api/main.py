from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from sqlmodel import select, inspect, text
import sqlalchemy
from pydantic import BaseModel

from database import create_db_and_tables, import_csv_data, SessionDep, engine
from models import MESData

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
        "api_endpoint": "/query"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)