from pydantic import BaseModel, EmailStr


# Pydantic модель для запроса регистрации
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
