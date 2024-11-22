from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query

from models.dash import MONTHS_ES, AverageCompletionTime, AverageCompletionTimeResponse, ReportCount, ReportCountResponse, ReportsData, StatusPercentage, StatusPercentageResponse
from models.report import DeliveryStatus
from models.user import User, UserRole
from utils.auth import current_user
from db.client import db_client

router = APIRouter(
    prefix="/dash", tags=["dash"], responses={404: {"message": "Not found"}}
)

@router.get("/", response_model=ReportCountResponse)
async def get_reports_count(
    user: User = Depends(current_user),
    filter: str = Query(
        ...,
        description="Filter reports by '15 days', 'monthly', 'year', or 'all years'",
    ),
    month: int = Query(None, description="Specify the month for 'monthly' filter"),
    year: int = Query(None, description="Specify the year for 'year' filter"),
    operator_id: str = Query(
        None, description="Specify the operator ID to filter reports by operator"
    ),
    airline: str = Query(
        None, description="Specify the airline to filter reports by airline"
    ),
    delivery_status: str = Query(
        None, description="Specify the status to filter reports by status"
    ),
):
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    match_conditions = {}

    if delivery_status:
        match_conditions["delivery_status"] = delivery_status
    else:
        match_conditions["delivery_status"] = {
            "$in": [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]
        }

    if operator_id:
        match_conditions["operator.operator_id"] = operator_id

        operator_reports_count = db_client.reports.count_documents(match_conditions)
        if operator_reports_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The operator has no reports with the specified status",
            )

    if airline and airline != "Todas":
        match_conditions["airline"] = airline

    now = datetime.now()

    if filter == "15 days":
        start_date = now - timedelta(days=15)
        if delivery_status in [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]:
            match_conditions["delivery_date"] = {"$gte": start_date}
        else:
            match_conditions["creation_date"] = {"$gte": start_date}
        group_by = {
            "day": {"$dayOfMonth": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
            "month": {"$month": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
            "year": {"$year": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
        }
        sort_by = {"_id.year": 1, "_id.month": 1, "_id.day": 1}
    elif filter == "monthly":
        if month is not None and year is not None:
            start_date = datetime(year, month, 1)
            end_date = (start_date + timedelta(days=31)).replace(day=1)
            if delivery_status in [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]:
                match_conditions["delivery_date"] = {"$gte": start_date, "$lt": end_date}
            else:
                match_conditions["creation_date"] = {"$gte": start_date, "$lt": end_date}
        else:
            start_date = now.replace(day=1)
            end_date = (start_date + timedelta(days=31)).replace(day=1)
            if delivery_status in [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]:
                match_conditions["delivery_date"] = {"$gte": start_date, "$lt": end_date}
            else:
                match_conditions["creation_date"] = {"$gte": start_date, "$lt": end_date}
        group_by = {
            "day": {"$dayOfMonth": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
            "month": {"$month": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
            "year": {"$year": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
        }
        sort_by = {"_id.year": 1, "_id.month": 1, "_id.day": 1}
    elif filter == "year":
        if year is not None:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            if delivery_status in [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]:
                match_conditions["delivery_date"] = {"$gte": start_date, "$lt": end_date}
            else:
                match_conditions["creation_date"] = {"$gte": start_date, "$lt": end_date}
        else:
            start_date = now.replace(month=1, day=1)
            if delivery_status in [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]:
                match_conditions["delivery_date"] = {"$gte": start_date}
            else:
                match_conditions["creation_date"] = {"$gte": start_date}
        group_by = {
            "month": {"$month": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
            "year": {"$year": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"},
        }
        sort_by = {"_id.year": 1, "_id.month": 1}
    elif filter == "all years":
        group_by = {"year": {"$year": "$delivery_date" if "delivery_date" in match_conditions else "$creation_date"}}
        sort_by = {"_id.year": 1}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filter value"
        )

    pipeline = [
        {"$match": match_conditions},
        {
            "$group": {
                "_id": group_by,
                "total_count": {"$sum": 1},
                "reports_data": {
                    "$push": {
                        "delivery_date": "$delivery_date",
                        "creation_date": "$creation_date",
                        "bdo_number": "$bdo_number",
                        "airline": "$airline",
                        "delivery_status": "$delivery_status",
                        "destination": "$destination",
                    }
                },
            }
        },
        {"$sort": sort_by},
    ]

    reports = list(db_client.reports.aggregate(pipeline))

    if not reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reports found for the specified filter",
        )

    response = ReportCountResponse(
        reports=[
            ReportCount(
                day=report["_id"].get("day"),
                month=MONTHS_ES.get(report["_id"].get("month")),
                year=report["_id"]["year"],
                total_count=report["total_count"],
            )
            for report in reports
        ],
        reports_data=[
            ReportsData(
                delivery_date=data.get("delivery_date"),
                creation_date=data.get("creation_date"),
                bdo_number=data["bdo_number"],
                airline=data["airline"],
                delivery_status=data["delivery_status"],
                destination=data["destination"],
            )
            for report in reports
            for data in report["reports_data"]
        ] if filter in ["15 days", "monthly"] else []
    )

    return response

@router.get("/average-completion-times")
async def get_average_completion_times(delivery_zone: str, user: User = Depends(current_user)):
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    pipeline = [
        {
            "$match": {
                "delivery_zone": delivery_zone,
                "delivery_status": {"$in": [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]},
            }
        },
        {
            "$project": {
                "delivery_zone": 1,
                "destination": 1,
                "time_to_complete": {
                    "$divide": [
                        {"$subtract": ["$delivery_date", "$creation_date"]},
                        1000 * 60 * 60  # Convert milliseconds to hours
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "delivery_zone": "$delivery_zone",
                    "destination": "$destination"
                },
                "average_time": {"$avg": "$time_to_complete"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "delivery_zone": "$_id.delivery_zone",
                "destination": "$_id.destination",
                "average_time": {"$round": ["$average_time", 2]}
            }
        }
    ]

    result = list(db_client.reports.aggregate(pipeline))

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No completed reports found for the given delivery zone"
        )
    
    response = AverageCompletionTimeResponse(
        completion_times=[
            AverageCompletionTime(
                delivery_zone=item["delivery_zone"],
                destination=item["destination"],
                average_time=item["average_time"]
            )
            for item in result
        ]
    )

    return response

@router.get("/status-percentages", response_model=StatusPercentageResponse)
async def get_status_percentages(
    user: User = Depends(current_user),
    operator_id: str = Query(None, description="Specify the operator ID to filter reports by operator")
):
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    match_conditions = {}
    if operator_id:
        match_conditions["operator.operator_id"] = operator_id

    pipeline = [
        {"$match": match_conditions},
        {
            "$group": {
                "_id": "$delivery_status",
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "status": "$_id",
                "count": 1
            }
        }
    ]

    result = list(db_client.reports.aggregate(pipeline))

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No reports found"
        )

    total_count = sum(item["count"] for item in result)
    status_percentages = [
        StatusPercentage(
            status=item["status"],
            percentage=int((item["count"] / total_count) * 100)
        )
        for item in result
    ]

    response = StatusPercentageResponse(statuses=status_percentages)
    return response