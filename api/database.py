from typing import Annotated, Generator
import pandas as pd
from datetime import datetime
from sqlmodel import create_engine, SQLModel, Session
from fastapi import Depends

from models import MESData

sqlite_file_name = "../data/mes_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def import_csv_data():
    """Import data from CSV file into the database"""
    df = pd.read_csv("../data/mes_data_with_kpis.csv")
    
    with Session(engine) as session:
        # Check if data already exists
        existing = session.query(MESData).first()
        if existing:
            print("Data already imported, skipping...")
            return
        
        # Convert DataFrame to MESData objects
        for _, row in df.iterrows():
            mes_data = MESData(
                timestamp=datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S'),
                production_order_id=row['ProductionOrderID'] if pd.notna(row['ProductionOrderID']) else None,
                line_id=str(row['LineID']),
                equipment_id=row['EquipmentID'],
                equipment_type=row['EquipmentType'],
                product_id=row['ProductID'] if pd.notna(row['ProductID']) else None,
                product_name=row['ProductName'] if pd.notna(row['ProductName']) else None,
                machine_status=row['MachineStatus'],
                downtime_reason=row['DowntimeReason'] if pd.notna(row['DowntimeReason']) else None,
                good_units_produced=int(row['GoodUnitsProduced']),
                scrap_units_produced=int(row['ScrapUnitsProduced']),
                target_rate_units_per_5min=int(row['TargetRate_units_per_5min']),
                standard_cost_per_unit=float(row['StandardCost_per_unit']),
                sale_price_per_unit=float(row['SalePrice_per_unit']),
                availability_score=float(row['Availability_Score']),
                performance_score=float(row['Performance_Score']),
                quality_score=float(row['Quality_Score']),
                oee_score=float(row['OEE_Score'])
            )
            session.add(mes_data)
        
        session.commit()
        print(f"Imported {len(df)} records from CSV")