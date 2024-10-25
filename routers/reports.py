from datetime import time, datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from db.schema.report_schema import report_Schema
from models.report import BdoOrder, DeliveryStatus
from models.user import User, UserRole
from utils.auth import current_user
from db.client import db_client

router = APIRouter(
    prefix="/reports", tags=["reports"], responses={404: {"message": "Not found"}}
)


def status_checker(current_status: DeliveryStatus, new_status: DeliveryStatus):
    if new_status <= current_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update to the same or lower status",
        )

    if (
        current_status == DeliveryStatus.pending
        and new_status == DeliveryStatus.completed
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update directly from pending to completed",
        )

    if (
        current_status == DeliveryStatus.pending
        and new_status == DeliveryStatus.invoiced
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update directly from pending to invoiced",
        )


@router.get("/")
async def get_reports(user: User = Depends(current_user)):
    if user.role == UserRole.admin:
        reports = db_client.reports.find()
        return [report_Schema(report) for report in reports]
    else:
        reports = db_client.reports.find({"delivery_zone": user.zone})
        return [report_Schema(report) for report in reports]


@router.post("/", response_model=BdoOrder, status_code=status.HTTP_201_CREATED)
async def create_report(report: BdoOrder, user: User = Depends(current_user)):
    new_report = {
        "creation_date": datetime.now(),
        "airline": report.airline,
        "reference_number": report.reference_number,
        "bdo_number": report.bdo_number,
        "delivery_zone": report.delivery_zone,
        "destination": report.destination,
        "operator": {"operator_id": user.id, "operator_name": user.full_name},
        "delivery_status": DeliveryStatus.pending,
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Report creation failed"
        )

    new_report = report_Schema(new_report)

    return BdoOrder(**new_report)


@router.put("/", response_model=BdoOrder, status_code=status.HTTP_200_OK)
async def update_report_status(
    report_id: str, delivery_status: str, user: User = Depends(current_user)
):
    report = db_client.reports.find_one({"_id": ObjectId(report_id)})

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    try:
        current_status = DeliveryStatus(report["delivery_status"])
        new_status = DeliveryStatus(delivery_status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid delivery status: {e}",
        )

    status_checker(current_status, new_status)

    if new_status == DeliveryStatus.completed:
        db_client.reports.update_one(
            {"_id": ObjectId(report_id)},
            {
                "$set": {
                    "delivery_status": delivery_status,
                    "delivery_date": datetime.now(),
                }
            },
        )
    else:
        db_client.reports.update_one(
            {"_id": ObjectId(report_id)}, {"$set": {"delivery_status": delivery_status}}
        )

    updated_report = db_client.reports.find_one({"_id": ObjectId(report_id)})
    updated_report = report_Schema(updated_report)

    return BdoOrder(**updated_report)