from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    _id: Optional[str] | None = None
    username: Optional[str] | None = None
    full_name: Optional[str] | None = None
    first_name: str
    last_name: str
    type: str
    disabled: bool


class UserDB(User):
    password: str