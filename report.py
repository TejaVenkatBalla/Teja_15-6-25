import logging
from datetime import datetime, timedelta
import io
import csv
from database import SessionLocal
from models import StoreStatus, ReportStatus
from db_utils import get_store_data
from calculator import calculate_uptime_downtime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_comprehensive_report(db):
    """Generate report with proper extrapolation logic"""
    logger.info("Starting report generation")
    
    #  hard coded the current timestamp to be the max timestamp among all the observations in the first CSV. 
    max_timestamp_result = db.query(StoreStatus.timestamp_utc).order_by(
        StoreStatus.timestamp_utc.desc()
    ).first()
    #current_time = max_timestamp_result[0] if max_timestamp_result else datetime.utcnow()
    current_time = max_timestamp_result[0]
    logger.info(f"Current time for report: {current_time}")
    
    last_hour_start = current_time - timedelta(hours=1)
    last_day_start = current_time - timedelta(days=1)
    last_week_start = current_time - timedelta(weeks=1)
    
    #fetching store's lastweeks polling data and their repecitive business hours and timezones of stores from the database.
    logger.info("Fetching store data from database")
    store_observations_map, business_hours_by_store, timezones, store_ids = get_store_data(db, start_time=last_week_start, end_time=current_time)
    
    report_data = []
    
    for store_id in store_ids:
        store_business_hours = business_hours_by_store.get(store_id, {})
        store_timezone = timezones.get(store_id, "America/Chicago")
        store_observations = store_observations_map.get(store_id, [])
        
        hour_result = calculate_uptime_downtime(
            store_id=store_id,
            start_time=last_hour_start,
            end_time=current_time,
            store_observations=store_observations,
            business_hours=store_business_hours,
            timezone_str=store_timezone
        )
        
        day_result = calculate_uptime_downtime(
            store_id=store_id,
            start_time=last_day_start,
            end_time=current_time,
            store_observations=store_observations,
            business_hours=store_business_hours,
            timezone_str=store_timezone
        )
        
        week_result = calculate_uptime_downtime(
            store_id=store_id,
            start_time=last_week_start,
            end_time=current_time,
            store_observations=store_observations,
            business_hours=store_business_hours,
            timezone_str=store_timezone
        )
        
        report_data.append({
            "store_id": store_id,
            "uptime_last_hour": round(hour_result.uptime_minutes, 2),
            "uptime_last_day": round(day_result.uptime_minutes / 60, 2),
            "uptime_last_week": round(week_result.uptime_minutes / 60, 2),
            "downtime_last_hour": round(hour_result.downtime_minutes, 2),
            "downtime_last_day": round(day_result.downtime_minutes / 60, 2),
            "downtime_last_week": round(week_result.downtime_minutes / 60, 2),
        })
    
    output = io.StringIO()
    fieldnames = [
        "store_id", "uptime_last_hour", "uptime_last_day", "uptime_last_week",
        "downtime_last_hour", "downtime_last_day", "downtime_last_week"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(report_data)
    
    logger.info("Report generation completed")
    return output.getvalue()

def run_report_generation(report_id: str):
    """Background task for report generation"""
    logger.info(f"Starting background report generation for report_id={report_id}")
    db = SessionLocal()
    try:
        csv_data = generate_comprehensive_report(db)
        
        report = db.query(ReportStatus).filter(ReportStatus.report_id == report_id).first()
        if report:
            report.status = "Complete"
            report.completed_at = datetime.utcnow()
            report.csv_data = csv_data
            db.commit()
            logger.info(f"Report {report_id} generation completed successfully")
            
    except Exception as e:
        logger.error(f"Error during report generation for report_id={report_id}: {e}")
        report = db.query(ReportStatus).filter(ReportStatus.report_id == report_id).first()
        if report:
            report.status = f"Error: {str(e)}"
            db.commit()
    finally:
        db.close()
