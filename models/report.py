from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class DeliveryStatus(str, Enum):
    active = "Activo"
    pending = "Pendiente"
    completed = "Finalizado"
    invoiced = "Facturado"

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        return handler.generate_schema(str)

class Operator(BaseModel):
    operator_id: str
    operator_name: str

class BdoOrder(BaseModel):
    id: Optional[str] | None = None
    creation_date: Optional[datetime] | None = None
    delivery_date: Optional[datetime] | None = None
    airline: str
    reference_number: int
    bdo_number: int
    delivery_zone: str
    operator: Optional[Operator] | None = None
    delivery_status: Optional[DeliveryStatus] | None = None