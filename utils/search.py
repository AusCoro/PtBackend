from fastapi import HTTPException, status
from db.client import db_client
from models.user import User, UserDB

def serch_user_db(username: str):
    # Buscar en MongoDB
    user_data = db_client.users.find_one({"username": username})
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Convertir el diccionario user_data en una instancia del modelo User
    user_data["id"] = str(user_data["_id"])  # Asegurarse de que el campo id esté presente y sea un string
    user = UserDB(**user_data)
    
    return user



def serch_user(username: str):
    # Buscar el usuario en la base de datos
    user_data = db_client.users.find_one({"username": username})
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Convertir el diccionario user_data en una instancia del modelo User
    user_data["id"] = str(user_data["_id"])  # Asegurarse de que el campo id esté presente y sea un string
    user = User(**user_data)

    return user
