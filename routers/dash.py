from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from pydantic import BaseModel

from models.dash import ReportCount, ReportCountResponse
from models.report import DeliveryStatus
from models.user import User, UserRole
from utils.auth import current_user
from db.client import db_client


router = APIRouter(
    prefix="/dash", tags=["dash"], responses={404: {"message": "Not found"}}
)

class StatusPercentage(BaseModel):
    status: str
    percentage: float

class StatusPercentageResponse(BaseModel):
    statuses: List[StatusPercentage]

"""
Endpoint to retrieve monthly reports based on various filters.
Args:
    user (User): The current user, injected by dependency.
    filter (str): Filter reports by '15 days', 'monthly', 'year', or 'all years'.
    month (int, optional): Specify the month for 'monthly' filter.
    year (int, optional): Specify the year for 'year' filter.
    operator_id (str, optional): Specify the operator ID to filter reports by operator.
Raises:
    HTTPException: If the user does not have admin permissions.
    HTTPException: If the operator has no completed or invoiced reports.
    HTTPException: If the filter value is invalid.
    HTTPException: If no reports are found for the specified filter.
Returns:
    list: A list of reports matching the specified filter.
"""
@router.get("/", response_model=ReportCountResponse)
async def get_reports_count(
    user: User = Depends(current_user),
    filter: str = Query(..., description="Filter reports by '15 days', 'monthly', 'year', or 'all years'"),
    month: int = Query(None, description="Specify the month for 'monthly' filter"),
    year: int = Query(None, description="Specify the year for 'year' filter"),
    operator_id: str = Query(None, description="Specify the operator ID to filter reports by operator")
):
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    match_conditions = {
        "delivery_status": {"$in": [DeliveryStatus.completed.value, DeliveryStatus.invoiced.value]},
        "delivery_date": {"$exists": True}
    }

    if operator_id:
        match_conditions["operator.operator_id"] = operator_id

        # Check if the operator has any completed or invoiced reports
        operator_reports_count = db_client.reports.count_documents(match_conditions)
        if operator_reports_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The operator has no completed or invoiced reports")

    now = datetime.now()

    if filter == "15 days":
        start_date = now - timedelta(days=15)
        match_conditions["delivery_date"] = {"$gte": start_date}
        group_by = {"day": {"$dayOfMonth": "$delivery_date"}, "month": {"$month": "$delivery_date"}, "year": {"$year": "$delivery_date"}}
        sort_by = {"_id.year": 1, "_id.month": 1, "_id.day": 1}
    elif filter == "monthly":
        if month is not None and year is not None:
            start_date = datetime(year, month, 1)
            end_date = (start_date + timedelta(days=31)).replace(day=1)
            match_conditions["delivery_date"] = {"$gte": start_date, "$lt": end_date}
        else:
            start_date = now.replace(day=1)
            end_date = (start_date + timedelta(days=31)).replace(day=1)
            match_conditions["delivery_date"] = {"$gte": start_date, "$lt": end_date}
        group_by = {"day": {"$dayOfMonth": "$delivery_date"}, "month": {"$month": "$delivery_date"}, "year": {"$year": "$delivery_date"}}
        sort_by = {"_id.year": 1, "_id.month": 1, "_id.day": 1}
    elif filter == "year":
        if year is not None:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            match_conditions["delivery_date"] = {"$gte": start_date, "$lt": end_date}
        else:
            start_date = now.replace(month=1, day=1)
            match_conditions["delivery_date"] = {"$gte": start_date}
        group_by = {"month": {"$month": "$delivery_date"}, "year": {"$year": "$delivery_date"}}
        sort_by = {"_id.year": 1, "_id.month": 1}
    elif filter == "all years":
        group_by = {"year": {"$year": "$delivery_date"}}
        sort_by = {"_id.year": 1}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filter value")

    pipeline = [
        {"$match": match_conditions},
        {
            "$group": {
                "_id": group_by,
                "total_count": {"$sum": 1},
            }
        },
        {"$sort": sort_by},
    ]

    reports = list(db_client.reports.aggregate(pipeline))

    if not reports:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reports found for the specified filter")

    # Transform the reports to match the Pydantic model
    response = ReportCountResponse(
        reports=[
            ReportCount(
                day=report["_id"].get("day"),
                month=report["_id"].get("month"),
                year=report["_id"]["year"],
                total_count=report["total_count"]
            )
            for report in reports
        ]
    )

    return response

"""
Endpoint to get average completion times for deliveries in a specific delivery zone.
Args:
    delivery_zone (str): The delivery zone to filter the reports.
    user (User, optional): The current authenticated user. Defaults to Depends(current_user).
Raises:
    HTTPException: If the user does not have admin permissions.
    HTTPException: If no completed reports are found for the given delivery zone.
Returns:
    list: A list of dictionaries containing the delivery zone, destination, and average completion time in hours.
"""
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
                "average_time": 1
            }
        }
    ]

    result = list(db_client.reports.aggregate(pipeline))

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No completed reports found for the given delivery zone"
        )

    return result

"""
Endpoint to get status percentages of reports.
This endpoint retrieves the percentage distribution of different delivery statuses
from the reports. It filters the reports by the specified operator ID if provided.
Args:
    user (User): The current authenticated user, injected by dependency.
    operator_id (str, optional): The operator ID to filter reports by operator. Defaults to None.
Raises:
    HTTPException: If the user does not have admin permissions.
    HTTPException: If no reports are found.
Returns:
    StatusPercentageResponse: A response object containing the status percentages.
"""
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
            percentage=(item["count"] / total_count) * 100
        )
        for item in result
    ]

    response = StatusPercentageResponse(statuses=status_percentages)
    return response