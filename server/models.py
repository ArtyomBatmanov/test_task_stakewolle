from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


# Модель данных пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    referral_codes = relationship("ReferralCode", back_populates="user")


class ReferralCode(Base):
    __tablename__ = 'referral_codes'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="referral_codes")

    # Метод для проверки, истек ли срок действия реферального кода
    def is_active(self):
        return self.expiration_date > datetime.utcnow()
