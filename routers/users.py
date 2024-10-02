from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from db.users_db import users_db
from models.user import User, UserDB

from dotenv import load_dotenv
import os

from utils.auth import current_user
from utils.search import serch_user_db

load_dotenv()

ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_DURATION = int(os.getenv("ACCESS_TOKEN_DURATION"))
SECRET_KEY = os.getenv("SECRET_KEY")

router = APIRouter(
    prefix="/users", tags=["users"], responses={404: {"message": "Not found"}}
)

oauth2 = OAuth2PasswordBearer(tokenUrl="login")

crypt = CryptContext(schemes=["bcrypt"])


def generate_username(first_name: str, last_name: str) -> str:
    username = ''.join([name[0].upper() for name in first_name.split() + last_name.split()])

    # Asegurarse de que el username sea único
    initial_username = username
    counter = 1
    while username in users_db:
        username = initial_username + str(counter)
        counter += 1
        
    return username

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user_db = next((user for user in users_db if user.username == form.username), None)
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

@router.get("/all")
async def get_users(user: User = Depends(current_user)):
    return users_db

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_db: UserDB, user: User = Depends(current_user)): 

    # Generar username a partir de las iniciales
    username = generate_username(user_db.first_name, user_db.last_name)

    # Hash the password
    hashed_password = crypt.hash(user_db.password)

    # Create a new user object
    new_user = UserDB(
        # Este cambiara a un valor dado por la base de datos
        _id=str(len(users_db) + 1),
        username= username,
        full_name=user_db.first_name + " " + user_db.last_name,
        first_name=user_db.first_name,
        last_name=user_db.last_name,
        disabled=user_db.disabled,
        type=user_db.type,
        password=hashed_password,
    )

    # Add the new user to the users_db dictionary
    users_db.append(new_user)

    return new_user