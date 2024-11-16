from pydantic import BaseModel, EmailStr


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
