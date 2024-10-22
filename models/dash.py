from pydantic import BaseModel
from typing import List, Optional

class ReportCount(BaseModel):
    day: Optional[int]
    month: Optional[int]
    year: int
    total_count: int

class ReportCountResponse(BaseModel):
    reports: List[ReportCount]