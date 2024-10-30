from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class ReportsData(BaseModel):
    delivery_date: Optional[datetime]
    creation_date: Optional[datetime]
    bdo_number: int
    airline: str
    delivery_status: str
    destination: str

class ReportCount(BaseModel):
    day: Optional[int]
    month: Optional[int | str]
    year: int
    total_count: int

class ReportCountResponse(BaseModel):
    reports: List[ReportCount]
    reports_data: Optional[List[ReportsData]] | None

class AverageCompletionTime(BaseModel):
    delivery_zone: str
    destination: str
    average_time: float

class AverageCompletionTimeResponse(BaseModel):
    completion_times: List[AverageCompletionTime]

class StatusPercentage(BaseModel):
    status: str
    percentage: float

class StatusPercentageResponse(BaseModel):
    statuses: List[StatusPercentage]

MONTHS_ES = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic"
}