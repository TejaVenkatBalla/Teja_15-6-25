from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import io
import uuid
from datetime import datetime
from database import SessionLocal
from models import ReportResponse, ReportStatus
from report import run_report_generation


router = APIRouter()

@router.post("/trigger_report", response_model=ReportResponse)
async def trigger_report(background_tasks: BackgroundTasks):
    report_id = str(uuid.uuid4())
    
    db = SessionLocal()
    try:
        report_status = ReportStatus(
            report_id=report_id,
            status="Running"
        )
        db.add(report_status)
        db.commit()
        
        background_tasks.add_task(run_report_generation, report_id)
        
        return ReportResponse(report_id=report_id)
    
    finally:
        db.close()

@router.get("/get_report")
async def get_report(report_id: str):
    db = SessionLocal()
    try:
        report = db.query(ReportStatus).filter(ReportStatus.report_id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report.status == "Complete" and report.csv_data:
            return StreamingResponse(
                io.BytesIO(report.csv_data.encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"}
            )
        else:
            return {"status": report.status}
    
    finally:
        db.close()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


