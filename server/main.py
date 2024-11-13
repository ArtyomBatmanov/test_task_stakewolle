from fastapi import FastAPI, HTTPException, Depends
from schemas import RegisterRequest
from models import User
import os
from dotenv import load_dotenv
from database import SessionLocal
from crud import hash_password, create_jwt_token

# Инициализация FastAPI
app = FastAPI()

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")


# Endpoint для регистрации пользователя
@app.post("/auth/register")
async def register_user(request: RegisterRequest):
    session = SessionLocal()
    user = session.query(User).filter(User.email == request.email).first()

    if user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # Хешируем пароль и создаем пользователя
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Создаем JWT токен
    token = create_jwt_token(new_user.id, new_user.email)

    return {"access_token": token, "token_type": "bearer"}
