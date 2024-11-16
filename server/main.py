from fastapi import FastAPI, HTTPException, Depends
from schemas import RegisterRequest, LoginRequest, Token
from models import User
from database import SessionLocal, get_db
from crud import hash_password, create_jwt_token, verify_password, get_user_by_email
from sqlalchemy.orm import Session

# Инициализация FastAPI
app = FastAPI()

# Определение алгоритма хэширования паролей
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


@app.post("/auth/login", response_model=Token)
def login(
    login_request: LoginRequest,  # Используем схему LoginRequest для валидации
    db: Session = Depends(get_db)  # Сессия базы данных
):
    # Находим пользователя по email
    user = get_user_by_email(db, login_request.email)
    if not user:
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    # Проверяем, что введённый пароль совпадает с хранимым хэшем
    if not verify_password(login_request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    # Генерация JWT токена
    token = create_jwt_token(user.id, user.email)

    # Возвращаем токен
    return {"access_token": token, "token_type": "bearer"}


