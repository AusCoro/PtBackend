from fastapi import HTTPException, status

from db.users_db import users_db


def serch_user_db(username: str):
    user_data = next((user for user in users_db if user.username == username), None)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_data

def serch_user(username: str):
    user_data = next((user for user in users_db if user.username == username), None)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_data