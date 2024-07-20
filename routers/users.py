from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = 1
SECRET_KEY = "9103666a0a35d46a90d693216b4bc8c4325de896aca45c6b5c02dfde5b67d3bd"

router = APIRouter(
    prefix="/users", tags=["users"], responses={404: {"message": "Not found"}}
)

oauth2 = OAuth2PasswordBearer(tokenUrl="login")

crypt = CryptContext(schemes=["bcrypt"])


class User(BaseModel):
    username: str
    email: str
    full_name: str
    disabled: bool


class UserDB(User):
    password: str


users_db = {
    "raz": {
        "username": "raz",
        "email": "raz@mail.com",
        "full_name": "Carlos Yair",
        "disabled": False,
        "password": "$2a$12$InI9NYsjLWSnjELL.cTDguV/HIv23tuESGmHIHjxuH6.LuEB3ugLy",
    },
    "jose": {
        "username": "jose",
        "email": "jose@mail.com",
        "full_name": "Jose Perez",
        "disabled": True,
        "password": "$2a$12$5oOIm5763y4TeiYEP61MtOO5VyLo9kYJ6.rPMmlG5lVggadgJJCXS",
    },
}


def serch_user_db(username: str):
    if username in users_db:
        return UserDB(**users_db[username])


def serch_user(username: str):
    if username in users_db:
        return User(**users_db[username])


async def auth_user(token: str = Depends(oauth2)):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        username = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
        if username is None:
            raise exception

    except JWTError:
        raise exception

    return serch_user(username)


async def current_user(user: User = Depends(auth_user)):
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return user


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user_db = users_db.get(form.username)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username"
        )

    user = serch_user_db(form.username)

    if not crypt.verify(form.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    acces_token_expires = timedelta(minutes=ACCESS_TOKEN_DURATION)

    expire = datetime.now(timezone.utc) + acces_token_expires

    acces_token = jwt.encode(
        {"sub": user.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM
    )

    return {"access_token": acces_token, "token_type": "bearer"}


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return user
