from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, Query
from sqlmodel import select

from database import create_db_and_tables, import_csv_data, SessionDep
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


@app.get("/")
def read_root():
    return {"message": "MES Data API", "version": "2.0.0"}


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