from passlib.hash import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")


# Функция для хеширования пароля
def hash_password(password: str) -> str:
    return bcrypt.hash(password)


# Функция для генерации JWT токена
def create_jwt_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24)  # токен на 24 часа
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
