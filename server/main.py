from typing import List
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, HTTPException, Depends
from schemas import RegisterRequest, LoginRequest, Token, ReferralCodeCreate, ReferralCodeResponse, \
    RegisterWithReferralCodeRequest, UserBase
from models import User
from database import SessionLocal, get_db
from crud import password_hash, create_jwt_token, verify_password, get_user_by_email, create_referral_code, \
    delete_referral_code, get_current_user, get_referral_code_by_email, get_valid_referral_code, \
    create_user_with_referral, get_referrals_by_referrer_id
from sqlalchemy.orm import Session

# Инициализация FastAPI
app = FastAPI()


# Кастомное OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Stakewolle API",
        version="1.0.0",
        description="Документация для API тестового задания.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Endpoint для регистрации пользователя
@app.post("/auth/register", tags=["Authentication"], summary="Регистрация пользователя")
async def register_user(request: RegisterRequest):
    """
    Регистрирует нового пользователя.

    - **email**: Электронная почта пользователя.
    - **password**: Пароль пользователя.
    """
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


@app.post("/auth/login", response_model=Token, tags=["Authentication"], summary="Вход в систему")
async def login(
        login_request: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Авторизует пользователя и возвращает JWT токен.

    - **email**: Электронная почта пользователя.
    - **password**: Пароль пользователя.
    """
    user = get_user_by_email(db, login_request.email)
    if not user:
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    if not verify_password(login_request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    token = create_jwt_token(user.id, user.email)

    return {"access_token": token, "token_type": "bearer"}


@app.post("/referral-code/create", tags=["Referrals"], summary="Создать реферальный код")
async def create_referral(
        referral_data: ReferralCodeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Создает новый реферальный код для текущего пользователя.

    - **code**: Уникальный код.
    - **expiration_date**: Дата истечения срока действия кода.
    """
    referral_code = create_referral_code(
        db,
        current_user.id,
        referral_data.code,
        referral_data.expiration_date
    )
    return {"message": "Реферальный код успешно создан", "code": referral_code.code,
            "expiration_date": referral_code.expiration_date}


@app.delete("/referral-code/delete", tags=["Referrals"], summary="Удалить реферальный код")
async def delete_referral(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Удаляет реферальный код текущего пользователя.
    """
    return delete_referral_code(db, current_user.id)


@app.get("/referral-code/{email}", response_model=ReferralCodeResponse, tags=["Referrals"],
         summary="Получить реферальный код")
async def get_referral_code(email: str, db: Session = Depends(get_db)):
    """
    Возвращает реферальный код по указанному email.

    - **email**: Электронная почта пользователя.
    """
    referral_code = get_referral_code_by_email(db, email)
    if not referral_code:
        raise HTTPException(status_code=404, detail="Реферальный код не найден")

    return {
        "code": referral_code.code,
        "expiration_date": referral_code.expiration_date.date()
    }


@app.post("/register-with-referral", tags=["Referrals"], summary="Регистрация с реферальным кодом")
async def register_with_referral(request: RegisterWithReferralCodeRequest, db: Session = Depends(get_db)):
    """
    Регистрирует пользователя по реферальному коду.

    - **email**: Электронная почта пользователя.
    - **password**: Пароль пользователя.
    - **referral_code**: Код реферала (опционально).
    """
    referrer_id = None
    if request.referral_code:
        referral = get_valid_referral_code(db, request.referral_code)
        if not referral:
            raise HTTPException(status_code=400, detail="Недействительный или истекший реферальный код")
        referrer_id = referral.user_id

    new_user = create_user_with_referral(
        db=db,
        email=request.email,
        password=request.password,
        referrer_id=referrer_id
    )

    return {"message": "Регистрация успешна", "user_id": new_user.id}


@app.get("/referrals/{referrer_id}", response_model=List[UserBase], tags=["Referrals"], summary="Получить рефералов")
async def get_referrals(referrer_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список пользователей, которые зарегистрировались по реферальному коду указанного пользователя.

    - **referrer_id**: ID реферера.
    """
    referrals = get_referrals_by_referrer_id(db, referrer_id)
    if not referrals:
        raise HTTPException(status_code=404, detail="Рефералы не найдены")
    return referrals
