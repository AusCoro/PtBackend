from models.user import User


def user_Schema(user: User) -> dict:
    return {
        "id": str(user["_id"]),  # Asegúrate de manejar el _id si existe
        "username": user["username"],
        "full_name": f"{user['first_name']} {user['last_name']}",
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "disabled": user["disabled"],
        "zone": user["zone"],
        "role": user["role"],
    }
