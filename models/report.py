from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class DeliveryStatus(str, Enum):
    active = "Activo"
    pending = "Pendiente"
    completed = "Finalizado"
    invoiced = "Facturado"

    def __lt__(self, other):
        order = ["Facturado", "Finalizado", "Activo", "Pendiente"]
        if self.__class__ is other.__class__:
            return order.index(self.value) > order.index(other.value)
        return NotImplemented

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other
    

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