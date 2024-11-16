from passlib.hash import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from models import User
from sqlalchemy.orm import Session
from typing import Optional


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


# Функция для проверки пароля
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



# Функция для получения пользователя по email
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()
