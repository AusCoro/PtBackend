from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    full_name: str
    disabled: bool


class UserDB(User):
    password: str