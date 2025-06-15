from sqlalchemy import Column, Integer, String, DateTime, Time, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, time
from dataclasses import dataclass
from pydantic import BaseModel

Base = declarative_base()

# SQLAlchemy ORM models
class StoreStatus(Base):
    __tablename__ = "store_status"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    timestamp_utc = Column(DateTime, index=True)
    status = Column(String)

    __table_args__ = (
        Index('idx_store_status_store_time', 'store_id', 'timestamp_utc'),
    )

class BusinessHours(Base):
    __tablename__ = "business_hours"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time_local = Column(Time)
    end_time_local = Column(Time)

    __table_args__ = (
        Index('idx_business_hours_store_day', 'store_id', 'day_of_week'),
    )

class StoreTimezone(Base):
    __tablename__ = "store_timezone"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True, unique=True)
    timezone_str = Column(String)

class ReportStatus(Base):
    __tablename__ = "report_status"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True, index=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    csv_data = Column(String, nullable=True)

# Dataclasses for extrapolation logic
@dataclass
class StatusObservation:
    store_id: str
    timestamp_utc: datetime
    status: str

@dataclass
class BusinessHour:
    day_of_week: int
    start_time: time
    end_time: time

@dataclass
class UptimeDowntimeResult:
    uptime_minutes: float
    downtime_minutes: float
    total_business_minutes: float
    observations_count: int

# Pydantic models
class ReportResponse(BaseModel):
    report_id: str
