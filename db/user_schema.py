def user_Schema(user) -> dict:
    return {
        "id": str(user["_id"]),  # Asegúrate de manejar el _id si existe
        "username": user["username"],
        "full_name": f"{user['first_name']} {user['last_name']}",
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "disabled": user["disabled"],
        "type": user["type"],
    }
