from fastapi import FastAPI, HTTPException, Depends
from schemas import RegisterRequest, TokenResponse
from models import User
from database import SessionLocal, get_db
from crud import hash_password, create_jwt_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from crud import SECRET_KEY
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

# Инициализация FastAPI
app = FastAPI()

# Определение алгоритма хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


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



@app.post("/auth/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # автоматическое получение данных из формы
    db: Session = Depends(get_db)  # сессия базы данных
):
    # Находим пользователя по email (username в форме — это email)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    # Проверяем, что введённый пароль совпадает с хранимым хэшем
    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    # Генерация JWT токена
    token_payload = {
        "user_id": user.id,  # идентификатор пользователя
        "email": user.email,  # email пользователя
        "exp": datetime.utcnow() + timedelta(hours=24)  # срок действия токена (24 часа)
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)  # подпись токена

    # Возвращаем токен клиенту
    return {"access_token": token, "token_type": "bearer"}

