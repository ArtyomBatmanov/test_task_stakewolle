from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional


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


class ReferralCodeResponse(BaseModel):
    code: str
    expiration_date: date

    class Config:
        from_attributes = True


class RegisterWithReferralCodeRequest(BaseModel):
    email: EmailStr
    password: str
    referral_code: Optional[str]  # Поле для ввода реферального кода


class UserBase(BaseModel):
    id: int
    email: str
    referrer_id: Optional[int]

    class Config:
        from_attributes = True
