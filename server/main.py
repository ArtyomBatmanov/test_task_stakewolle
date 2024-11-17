from fastapi import FastAPI, HTTPException, Depends
from schemas import RegisterRequest, LoginRequest, Token, ReferralCodeCreate, ReferralCodeResponse, RegisterWithReferralCodeRequest
from models import User
from database import SessionLocal, get_db
from crud import password_hash, create_jwt_token, verify_password, get_user_by_email, create_referral_code, \
    delete_referral_code, get_current_user, get_referral_code_by_email, get_valid_referral_code, create_user_with_referral
from sqlalchemy.orm import Session

# Инициализация FastAPI
app = FastAPI()


# Определение алгоритма хэширования паролей


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
        password_hash=password_hash(request.password)
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


@app.post("/referral-code/create")
def create_referral(
        referral_data: ReferralCodeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Получаем текущего пользователя
):
    # Логика создания реферального кода
    referral_code = create_referral_code(
        db,
        current_user.id,
        referral_data.code,
        referral_data.expiration_date
    )
    return {"message": "Реферальный код успешно создан", "code": referral_code.code,
            "expiration_date": referral_code.expiration_date}


# Эндпоинт для удаления реферального кода
@app.delete("/referral-code/delete")
def delete_referral(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Получаем текущего пользователя
):
    # Логика удаления реферального кода
    return delete_referral_code(db, current_user.id)


@app.get("/referral-code/{email}", response_model=ReferralCodeResponse)
def get_referral_code(email: str, db: Session = Depends(get_db)):
    # Получаем реферальный код по email
    referral_code = get_referral_code_by_email(db, email)
    if not referral_code:
        raise HTTPException(status_code=404, detail="Реферальный код не найден")

    # Возвращаем найденный реферальный код
    return {
        "code": referral_code.code,
        "expiration_date": referral_code.expiration_date.date()
    }


@app.post("/register-with-referral")
def register_with_referral(request: RegisterWithReferralCodeRequest, db: Session = Depends(get_db)):
    # Проверяем реферальный код, если он указан
    referrer_id = None
    if request.referral_code:
        referral = get_valid_referral_code(db, request.referral_code)
        if not referral:
            raise HTTPException(status_code=400, detail="Недействительный или истекший реферальный код")
        referrer_id = referral.user_id  # ID пользователя, связанного с реферальным кодом

    # Регистрируем пользователя
    new_user = create_user_with_referral(
        db=db,
        email=request.email,
        password=request.password,
        referrer_id=referrer_id
    )

    return {"message": "Регистрация успешна", "user_id": new_user.id}
