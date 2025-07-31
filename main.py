from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from sqlmodel import select, func
import math

from database import create_db_and_tables, import_csv_data, SessionDep
from models import MESData
from schemas import MESDataResponse, KPISummary, PaginatedResponse

app = FastAPI(
    title="MES Data API",
    description="API for accessing Manufacturing Execution System data with KPIs",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    import_csv_data()


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to MES Data API", "endpoints": ["/docs", "/data", "/kpis/summary"]}


@app.get("/data", response_model=PaginatedResponse, tags=["Data"])
def get_all_data(
    session: SessionDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    machine_status: Optional[str] = None,
    line_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    production_order_id: Optional[str] = None,
    product_id: Optional[str] = None,
    downtime_reason: Optional[str] = None
):
    """Get all MES data with pagination and optional filters"""
    query = select(MESData)
    
    # Apply filters
    if machine_status:
        query = query.where(MESData.machine_status == machine_status)
    if line_id:
        query = query.where(MESData.line_id == line_id)
    if equipment_id:
        query = query.where(MESData.equipment_id == equipment_id)
    if production_order_id:
        query = query.where(MESData.production_order_id == production_order_id)
    if product_id:
        query = query.where(MESData.product_id == product_id)
    if downtime_reason:
        query = query.where(MESData.downtime_reason == downtime_reason)
    
    # Get total count
    count_query = select(func.count()).select_from(MESData)
    if machine_status:
        count_query = count_query.where(MESData.machine_status == machine_status)
    if line_id:
        count_query = count_query.where(MESData.line_id == line_id)
    if equipment_id:
        count_query = count_query.where(MESData.equipment_id == equipment_id)
    if production_order_id:
        count_query = count_query.where(MESData.production_order_id == production_order_id)
    if product_id:
        count_query = count_query.where(MESData.product_id == product_id)
    if downtime_reason:
        count_query = count_query.where(MESData.downtime_reason == downtime_reason)
    
    total = session.exec(count_query).one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    items = session.exec(query).all()
    total_pages = math.ceil(total / page_size)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@app.get("/data/{data_id}", response_model=MESDataResponse, tags=["Data"])
def get_data_by_id(data_id: int, session: SessionDep):
    """Get a single MES data record by ID"""
    data = session.get(MESData, data_id)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    return data


@app.get("/data/by-order/{order_id}", response_model=List[MESDataResponse], tags=["Data"])
def get_data_by_order(order_id: str, session: SessionDep):
    """Get all data for a specific production order"""
    query = select(MESData).where(MESData.production_order_id == order_id)
    data = session.exec(query).all()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this order")
    return data


@app.get("/data/by-line/{line_id}", response_model=List[MESDataResponse], tags=["Data"])
def get_data_by_line(line_id: str, session: SessionDep):
    """Get all data for a specific production line"""
    query = select(MESData).where(MESData.line_id == line_id)
    data = session.exec(query).all()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this line")
    return data


@app.get("/data/by-equipment/{equipment_id}", response_model=List[MESDataResponse], tags=["Data"])
def get_data_by_equipment(equipment_id: str, session: SessionDep):
    """Get all data for a specific equipment"""
    query = select(MESData).where(MESData.equipment_id == equipment_id)
    data = session.exec(query).all()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this equipment")
    return data


@app.get("/kpis/summary", response_model=KPISummary, tags=["KPIs"])
def get_kpi_summary(
    session: SessionDep,
    line_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    production_order_id: Optional[str] = None
):
    """Get aggregated KPI summary with optional filters"""
    query = select(
        func.avg(MESData.oee_score).label("avg_oee"),
        func.avg(MESData.availability_score).label("avg_availability"),
        func.avg(MESData.performance_score).label("avg_performance"),
        func.avg(MESData.quality_score).label("avg_quality"),
        func.sum(MESData.good_units_produced).label("total_good"),
        func.sum(MESData.scrap_units_produced).label("total_scrap"),
        func.count(func.distinct(MESData.equipment_id)).label("equipment_count")
    )
    
    # Apply filters
    if line_id:
        query = query.where(MESData.line_id == line_id)
    if equipment_id:
        query = query.where(MESData.equipment_id == equipment_id)
    if production_order_id:
        query = query.where(MESData.production_order_id == production_order_id)
    
    result = session.exec(query).one()
    
    total_units = (result[4] or 0) + (result[5] or 0)
    scrap_rate = (result[5] / total_units * 100) if total_units > 0 else 0
    
    return KPISummary(
        avg_oee_score=result[0] or 0,
        avg_availability_score=result[1] or 0,
        avg_performance_score=result[2] or 0,
        avg_quality_score=result[3] or 0,
        total_good_units=result[4] or 0,
        total_scrap_units=result[5] or 0,
        scrap_rate=scrap_rate,
        equipment_count=result[6] or 0
    )


@app.get("/kpis/by-equipment", tags=["KPIs"])
def get_kpis_by_equipment(session: SessionDep):
    """Get KPI summary grouped by equipment"""
    query = select(
        MESData.equipment_id,
        MESData.equipment_type,
        func.avg(MESData.oee_score).label("avg_oee"),
        func.avg(MESData.availability_score).label("avg_availability"),
        func.avg(MESData.performance_score).label("avg_performance"),
        func.avg(MESData.quality_score).label("avg_quality"),
        func.count().label("record_count")
    ).group_by(MESData.equipment_id, MESData.equipment_type)
    
    results = session.exec(query).all()
    
    return [
        {
            "equipment_id": r[0],
            "equipment_type": r[1],
            "avg_oee_score": r[2],
            "avg_availability_score": r[3],
            "avg_performance_score": r[4],
            "avg_quality_score": r[5],
            "record_count": r[6]
        }
        for r in results
    ]


@app.get("/kpis/by-product", tags=["KPIs"])
def get_kpis_by_product(session: SessionDep):
    """Get KPI summary grouped by product"""
    query = select(
        MESData.product_id,
        MESData.product_name,
        func.avg(MESData.oee_score).label("avg_oee"),
        func.sum(MESData.good_units_produced).label("total_good"),
        func.sum(MESData.scrap_units_produced).label("total_scrap"),
        func.count().label("record_count")
    ).group_by(MESData.product_id, MESData.product_name)
    
    results = session.exec(query).all()
    
    return [
        {
            "product_id": r[0],
            "product_name": r[1],
            "avg_oee_score": r[2],
            "total_good_units": r[3],
            "total_scrap_units": r[4],
            "scrap_rate": (r[4] / (r[3] + r[4]) * 100) if (r[3] + r[4]) > 0 else 0,
            "record_count": r[5]
        }
        for r in results
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)