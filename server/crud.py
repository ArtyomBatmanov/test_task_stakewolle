from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from models import User, ReferralCode
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from jose import JWTError, jwt

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Функция для получения текущего пользователя
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Извлекает и проверяет JWT токен, возвращает текущего пользователя.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Получаем пользователя из базы данных
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


# Функция для хеширования пароля
def password_hash(password: str) -> str:
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
def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


# Функция для получения пользователя по email
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_active_referral_code(db: Session, user_id: int):
    # Проверка, есть ли у пользователя активный реферальный код
    return db.query(ReferralCode).filter(
        ReferralCode.user_id == user_id,
        ReferralCode.expiration_date > datetime.utcnow()
    ).first()


def create_referral_code(db: Session, user_id: int, code: str, expiration_date: datetime):
    # Проверка на наличие активного реферального кода
    active_code = get_active_referral_code(db, user_id)
    if active_code:
        raise HTTPException(status_code=400, detail="У пользователя уже есть активный реферальный код")

    # Создание нового реферального кода
    new_code = ReferralCode(
        code=code,
        expiration_date=expiration_date,
        user_id=user_id
    )
    db.add(new_code)
    db.commit()
    db.refresh(new_code)
    return new_code


def delete_referral_code(db: Session, user_id: int):
    # Находим активный реферальный код пользователя
    active_code = get_active_referral_code(db, user_id)
    if not active_code:
        raise HTTPException(status_code=404, detail="Нет активного реферального кода")

    # Удаляем реферальный код
    db.delete(active_code)
    db.commit()
    return {"message": "Реферальный код успешно удалён"}


def get_referral_code_by_email(db: Session, email: str):
    # Найти пользователя по email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None  # Если пользователя нет, возвращаем None

    # Найти активный реферальный код для найденного пользователя
    referral_code = db.query(ReferralCode).filter(ReferralCode.user_id == user.id).first()
    return referral_code


def get_valid_referral_code(db: Session, code: str) -> ReferralCode:
    return db.query(ReferralCode).filter(
        ReferralCode.code == code,
        ReferralCode.expiration_date >= datetime.utcnow()
    ).first()


def create_user_with_referral(db: Session, email: str, password: str, referrer_id: Optional[int] = None) -> User:
    new_user = User(
        email=email,
        password_hash=password_hash(password),
        referrer_id=referrer_id  # Указание реферера
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_referrals_by_referrer_id(db: Session, referrer_id: int):
    referrals = db.query(User).filter(User.referrer_id == referrer_id).all()
    return referrals
