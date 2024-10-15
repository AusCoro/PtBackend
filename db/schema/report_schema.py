from models.report import BdoOrder

def report_Schema(report: BdoOrder) -> dict:
    return {
        "id": str(report["_id"]),
        "creation_date": report.get("creation_date"),  # Usar get para evitar KeyError
        "delivery_date": report.get("delivery_date"),  # Usar get para evitar KeyError
        "airline": report.get("airline"),
        "reference_number": report.get("reference_number"),
        "bdo_number": report.get("bdo_number"),
        "delivery_zone": report.get("delivery_zone"),
        "operator": report.get("operator"),
        "delivery_status": report.get("delivery_status")
    }