from enum import Enum
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: Optional[str] | None = None
    username: Optional[str] | None = None
    full_name: Optional[str] | None = None
    first_name: str
    last_name: str
    role: str
    zone: str
    disabled: Optional[bool] | None = None


class UserDB(User):
    password: str

class UserRole(str, Enum):
    admin = "Admin"
    supervisor = "Supervisor"
    operator = "Operador"

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        return handler.generate_schema(str)
    
