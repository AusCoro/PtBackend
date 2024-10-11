from fastapi import HTTPException, status
from db.client import db_client

def serch_user_db(username: str):
    # Buscar en MongoDB
    user_data = db_client.local.users.find_one({"username": username})
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_data



def serch_user(username: str):
    # Similar a serch_user_db, puedes decidir mantenerlo o no
    user_data = db_client.local.users.find_one({"username": username})
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_data
