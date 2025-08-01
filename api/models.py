from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class MESData(SQLModel, table=True):
    __tablename__ = "mes_data"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    production_order_id: Optional[str] = Field(default=None, index=True)
    line_id: str = Field(index=True)
    equipment_id: str = Field(index=True)
    equipment_type: str
    product_id: Optional[str] = Field(default=None, index=True)
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
    oee_score: float = Field(index=True)