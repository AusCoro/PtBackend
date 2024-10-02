from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    # Este cambiara a un valor dado por la base de datos
    _id: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    first_name: str
    last_name: str
    type: str
    disabled: bool


class UserDB(User):
    password: str