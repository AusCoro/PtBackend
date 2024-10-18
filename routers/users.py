from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, time, timedelta, timezone
from bson import ObjectId

from models.user import User, UserDB, UserRole

from dotenv import load_dotenv
import os

from utils.auth import current_user
from utils.search import serch_user_db

from db.schema.user_schema import user_Schema
from db.client import db_client
from fastapi import Form


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

    #aqui se conecta y encuentra el nombre de usuario
    while db_client.users.find_one({"username": username}):
        username = initial_username + str(counter)
        counter += 1
    return username


#modificacion del endpoint para que busque en mi bd y no en mi lista local
@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):

    # Buscar el usuario directamente en la base de datos de MongoDB
    user = serch_user_db(form.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username"
        )

    # Verificar la contraseña
    if not crypt.verify(form.password, user.password):  # Usar claves del diccionario
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    # Configurar la expiración del token
    acces_token_expires = timedelta(minutes=ACCESS_TOKEN_DURATION)
    expire = datetime.now(timezone.utc) + acces_token_expires

    # Generar el token JWT
    acces_token = jwt.encode(
        {"sub": user.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM
    )
    
    # Devolver el token como respuesta
    return {"token": acces_token, "token_type": "bearer", "role": user.role}



@router.get("/me")
async def me(my_user: User = Depends(current_user)):
    return my_user


#cambio para que retorne directamente esa lista en mi bd.
@router.get("/all")
async def get_users(user: User = Depends(current_user)):
    users = db_client.users.find()  # Obtener todos los usuarios de MongoDB
    return [user_Schema(user) for user in users]  # Convertir cada documento al esquema de usuario



@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_db: UserDB, user: User = Depends(current_user)):
# async def create_user(user_db: UserDB):

    if user.role == UserRole.operator:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    username = generate_username(user_db.first_name, user_db.last_name)
    hashed_password = crypt.hash(user_db.password)

    new_user_dict = {
        "username": username,
        "full_name": f"{user_db.first_name} {user_db.last_name}",
        "first_name": user_db.first_name,
        "last_name": user_db.last_name,
        "disabled": False,
        "role": user_db.role,
        "zone": user_db.zone,
        "password": hashed_password
    }

    # Insertar el usuario en la base de datos
    user_id = db_client.users.insert_one(new_user_dict).inserted_id

    # Intentar recuperar el nuevo usuario creado desde la base de datos
    retries = 5
    new_user = None
    for _ in range(retries):
        new_user = db_client.users.find_one({"_id": user_id})
        if new_user:
            break
        time.sleep(0.1)  # Esperar un poco antes de intentar de nuevo

    if not new_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation failed")

    # Convertir el nuevo usuario a un esquema de usuario
    new_user = user_Schema(new_user)

    # Devolver el nuevo usuario como respuesta
    return User(**new_user)


#chequando si se permite modificar el rol de un usuario,
@router.put("/change-role/")
async def change_user_role(user_id: str, new_role: UserRole, current_user: User = Depends(current_user)): 

    # chequeando si el usuario autenticado tiene permisos para cambiar roles
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to change role")

    # Busqueando el usuario a modificar en la base de datos
    user_to_modify = db_client.users.find_one({"_id": ObjectId(user_id)})

    if not user_to_modify:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Actualizacion del rol del usuario en la base de datos
    db_client.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": new_role}})

    # reornamiento de una respuesta de éxito
    return {"message": f"User role updated to {new_role}"}


#cambio de contraseña
@router.put("/change-password/{user_id}")
async def change_password(user_id: str, password_request: str = Form(...), current_user: User = Depends(current_user)):
    # Verificar el rol del usuario que hace la solicitud (quien envía el token)
    if current_user.role == UserRole.operator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operators cannot change passwords")

    # Buscar el usuario al que se desea cambiar la contraseña por su ID
    user_to_modify = db_client.users.find_one({"_id": ObjectId(user_id)})

    if not user_to_modify:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verificar permisos del usuario (si es Supervisor, solo puede cambiar contraseñas de Operadores)
    if current_user.role == UserRole.supervisor and user_to_modify["role"] != UserRole.operator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Supervisors can only change Operator passwords")

    # Si todo está correcto, proceder con el cambio de contraseña
    hashed_password = crypt.hash(password_request)
    db_client.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})

    return {"message": f"Password updated for user with ID {user_id}"}

