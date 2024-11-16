from pydantic import BaseModel, EmailStr
from datetime import datetime


# Pydantic модель для запроса регистрации
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class ReferralCodeCreate(BaseModel):
    code: str  # сам реферальный код
    expiration_date: datetime  # дата истечения срока действия кода

    class Config:
        from_attributes = True
