from datetime import time, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from db.schema.report_schema import report_Schema
from models.report import BdoOrder, DeliveryStatus
from models.user import User
from utils.auth import current_user
from db.client import db_client

router = APIRouter(
    prefix="/reports", tags=["reports"], responses={404: {"message": "Not found"}}
)

@router.get("/")
async def get_reports(user: User = Depends(current_user)):
    reports = db_client.reports.find()
    return [report_Schema(report) for report in reports]

@router.post("/", response_model=BdoOrder, status_code=status.HTTP_201_CREATED)
async def create_report(report: BdoOrder, user: User = Depends(current_user)):    
    new_report = {
        "creation_date": datetime.now(),
        "airline": report.airline,
        "reference_number": report.reference_number,
        "bdo_number": report.bdo_number,
        "delivery_zone": report.delivery_zone,
        "operator": {
            "operator_id": user.id,
            "operator_name": user.full_name
        },
        "delivery_status": DeliveryStatus.pending
    }

    report_id = db_client.reports.insert_one(new_report).inserted_id
    
    retries = 5
    new_report = None
    for _ in range(retries):
        new_report = db_client.reports.find_one({"_id": report_id})
        if new_report:
            break
        time.sleep(0.1)  # Esperar un poco antes de intentar de nuevo

    if not new_report:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report creation failed")

    new_report = report_Schema(new_report)

    return BdoOrder(**new_report)