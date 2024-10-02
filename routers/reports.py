from datetime import timedelta
from fastapi import APIRouter, Depends
from models.report import *
from models.user import User
from utils.auth import current_user

router = APIRouter(
    prefix="/reports", tags=["reports"], responses={404: {"message": "Not found"}}
)

ordenBDO_lista = [
    BdoOrder(
        order_id="1",
        creation_date=datetime.now(),
        delivery_date=datetime.now() + timedelta(days=1),
        airline="AerolineaX",
        baggage_quantity=2,
        reference_number=12345,
        bdo_number=54321,
        delivery_zone="Zone 1",
        operator=Operator(operator_id="1", operator_name="Operator 1"),
        delivery_status=DeliveryStatus.active
    ),
    BdoOrder(
        order_id="2",
        creation_date=datetime.now(),
        delivery_date=datetime.now() + timedelta(days=2),
        airline="AerolineaY",
        baggage_quantity=2,
        reference_number=12345,
        bdo_number=54321,
        delivery_zone="Zone 1",
        operator=Operator(operator_id="1", operator_name="Operator 2"),
        delivery_status=DeliveryStatus.pending
    ),
    BdoOrder(
        order_id="3",
        creation_date=datetime.now(),
        delivery_date=datetime.now() + timedelta(days=3),
        airline="AerolineaZ",
        baggage_quantity=2,
        reference_number=12345,
        bdo_number=54321,
        delivery_zone="Zone 1",
        operator=Operator(operator_id="1", operator_name="Operator 2"),
        delivery_status=DeliveryStatus.completed
    ),
]

@router.get("/")
async def get_reports(user: User = Depends(current_user)):
    return ordenBDO_lista

@router.post("/")
async def create_report(report: BdoOrder, user: User = Depends(current_user)):
    ordenBDO_lista.append(report)
    return ordenBDO_lista