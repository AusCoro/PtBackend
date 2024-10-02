from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class DeliveryStatus(str, Enum):
    active = "Activo"
    pending = "Pendiente"
    completed = "Finalizado"

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        return handler.generate_schema(str)

class Operator(BaseModel):
    operator_id: str
    operator_name: str

class BdoOrder(BaseModel):
    order_id: str
    creation_date: datetime
    delivery_date: datetime
    airline: str
    baggage_quantity: int
    reference_number: int
    bdo_number: int
    delivery_zone: str
    operator: Operator
    delivery_status: DeliveryStatus