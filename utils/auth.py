import os
from dotenv import load_dotenv
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt

from models.user import User
from utils.search import serch_user

load_dotenv()

ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_DURATION = int(os.getenv("ACCESS_TOKEN_DURATION"))
SECRET_KEY = os.getenv("SECRET_KEY")

oauth2 = OAuth2PasswordBearer(tokenUrl="login")

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