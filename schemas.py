from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MESDataResponse(BaseModel):
    id: int
    timestamp: datetime
    production_order_id: Optional[str] = None
    line_id: str
    equipment_id: str
    equipment_type: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    machine_status: str
    downtime_reason: Optional[str] = None
    good_units_produced: int
    scrap_units_produced: int
    target_rate_units_per_5min: int
    standard_cost_per_unit: float
    sale_price_per_unit: float
    availability_score: float
    performance_score: float
    quality_score: float
    oee_score: float
    
    class Config:
        from_attributes = True


class KPISummary(BaseModel):
    avg_oee_score: float
    avg_availability_score: float
    avg_performance_score: float
    avg_quality_score: float
    total_good_units: int
    total_scrap_units: int
    scrap_rate: float
    equipment_count: int
    
    
class PaginatedResponse(BaseModel):
    items: List[MESDataResponse]
    total: int
    page: int
    page_size: int
    total_pages: int