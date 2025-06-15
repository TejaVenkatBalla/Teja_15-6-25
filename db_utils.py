import logging
from typing import Dict, Tuple
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
from models import StoreStatus, BusinessHours, StoreTimezone, StatusObservation, BusinessHour
from collections import defaultdict

logger = logging.getLogger(__name__)

def get_db():
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from typing import Optional
from datetime import datetime

def get_store_data(db: Session, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Tuple[Dict, Dict, Dict]:
    """Load store data from database, optionally filtered by time range"""
    
    logger.info(f"Loading store data with time filter: start_time={start_time}, end_time={end_time}")
    
    query = db.query(StoreStatus)

    if start_time and end_time:
        query = query.filter(StoreStatus.timestamp_utc >= start_time, StoreStatus.timestamp_utc <= end_time)
    status_records = query.all()
    logger.info(f"Loaded {len(status_records)} status records")
    
    store_observations_map = defaultdict(list)
    store_ids = set()

    for record in status_records:
        obs = StatusObservation(
            store_id=record.store_id,
            timestamp_utc=record.timestamp_utc,
            status=record.status
        )
        store_observations_map[record.store_id].append(obs)
        store_ids.add(record.store_id)


    # Query business hours only for those stores
    business_hours_records = db.query(BusinessHours).filter(BusinessHours.store_id.in_(store_ids)).all()
    
    business_hours_by_store = {}
    for record in business_hours_records:
        if record.store_id not in business_hours_by_store:
            business_hours_by_store[record.store_id] = {}
        
        business_hours_by_store[record.store_id][record.day_of_week] = BusinessHour(
            day_of_week=record.day_of_week,
            start_time=record.start_time_local,
            end_time=record.end_time_local
        )
    
    #timezone_records = db.query(StoreTimezone).all()
    timezone_records = db.query(StoreTimezone).filter(StoreTimezone.store_id.in_(store_ids)).all()
    timezones = {record.store_id: record.timezone_str for record in timezone_records}
    
    logger.info(f"Loaded business hours for {len(business_hours_by_store)} stores and timezones for {len(timezones)} stores")
    
    return store_observations_map, business_hours_by_store, timezones ,store_ids

def load_csv_data():
    from database import SessionLocal
    session = SessionLocal()
    try:
 
        status_df = pd.read_csv("./store-monitoring-data/store_status.csv")
        status_df['timestamp_utc'] = pd.to_datetime(status_df['timestamp_utc'], utc=True)
        for _, row in status_df.iterrows():
            session.add(StoreStatus(
                store_id=row['store_id'],
                timestamp_utc=row['timestamp_utc'],
                status=row['status']
            ))

        bh_df = pd.read_csv("./store-monitoring-data/menu_hours.csv")
        for _, row in bh_df.iterrows():
            start_time = datetime.strptime(row['start_time_local'], "%H:%M:%S").time()
            end_time = datetime.strptime(row['end_time_local'], "%H:%M:%S").time()
            session.add(BusinessHours(
                store_id=row['store_id'],
                day_of_week=int(row['dayOfWeek']),
                start_time_local=start_time,
                end_time_local=end_time
            ))

        tz_df = pd.read_csv("./store-monitoring-data/timezones.csv")
        for _, row in tz_df.iterrows():
            session.add(StoreTimezone(
                store_id=row['store_id'],
                timezone_str=row['timezone_str']
            ))

        session.commit()
        print("Sample data loaded successfully!")
    finally:
        session.close()
