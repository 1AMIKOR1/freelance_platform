from typing import Annotated

from fastapi import Depends, Request
from pydantic import BaseModel, Field

from app.database.database import async_session_maker, get_db
from app.exceptions.auth import (
    InvalidJWTTokenError,
    InvalidTokenHTTPError,
    NoAccessTokenHTTPError,
)
from app.services.auth import AuthService
from app.database.db_manager import DBManager
from app.models.users import UserModel
from app.models.roles import RoleModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status


class PaginationParams(BaseModel):
    page: int | None = Field(default=1, ge=1)
    per_page: int | None = Field(default=5, ge=1, le=30)


PaginationDep = Annotated[PaginationParams, Depends()]


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token", None)
    if token is None:
        raise NoAccessTokenHTTPError
    return token


def get_current_user_id(token: str = Depends(get_token)) -> int:
    try:
        data = AuthService.decode_token(token)
    except InvalidJWTTokenError:
        raise InvalidTokenHTTPError
    return data["user_id"]


UserIdDep = Annotated[int, Depends(get_current_user_id)]


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    return user


async def get_current_admin(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    # Проверяем, что пользователь админ
    result = await db.execute(
        select(RoleModel).where(RoleModel.id == user.role_id)
    )
    role = result.scalar_one_or_none()
    if not role or role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав администратора"
        )
    return user


async def get_db():
    async with DBManager(session_factory=async_session_maker) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]