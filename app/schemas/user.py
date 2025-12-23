# app/schemas/user.py - ПРАВИЛЬНАЯ ВЕРСИЯ
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: str  # Используем str вместо EmailStr, чтобы избежать зависимости

class UserCreate(UserBase):
    password: str
    role_id: int

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class User(UserBase):
    id: int
    role_id: int

    class Config:
        from_attributes = True  # Ранее называлось orm_mode = True


# Схемы для аутентификации и регистрации
class SUserAuth(BaseModel):
    email: str
    password: str


class SUserAddRequest(BaseModel):
    name: str
    email: str
    password: str
    role_id: int


class SUserAdd(BaseModel):
    name: str
    email: str
    hashed_password: str
    role_id: int


class SUserGet(User):
    pass  # Пока просто наследуем от User
