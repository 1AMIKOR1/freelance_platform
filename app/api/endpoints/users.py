from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from app.database.database import get_db
from app.models.users import UserModel
from app.schemas.user import User, UserCreate, UserUpdate
from app.api.dependencies import get_current_user, get_current_admin
from app.utils.security import get_password_hash, verify_password
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# GET /api/users/ - Получить всех пользователей (только админ)
@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=100, description="Лимит записей"),
    role_id: Optional[int] = Query(None, description="Фильтр по роли"),
    search: Optional[str] = Query(None, min_length=2, description="Поиск по имени или email"),
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(get_current_admin)  # Только админ
):
    """
    Получить список пользователей с пагинацией и фильтрацией.
    Требуются права администратора.
    """
    try:
        query = select(UserModel)
        
        # Применяем фильтры
        if role_id:
            query = query.where(UserModel.role_id == role_id)
        
        if search:
            query = query.where(
                (UserModel.name.ilike(f"%{search}%")) | 
                (UserModel.email.ilike(f"%{search}%"))
            )
        
        # Сортировка по ID
        query = query.order_by(UserModel.id)
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users
    
    except Exception as e:
        logger.error(f"Ошибка при получении пользователей: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

# GET /api/users/{user_id} - Получить пользователя по ID
@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Получить информацию о пользователе по ID.
    Пользователь может смотреть только свой профиль, если он не админ.
    """
    # Проверяем права доступа
    if current_user.id != user_id and not hasattr(current_user, 'is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этого профиля"
        )
    
    try:
        result = await db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

# GET /api/users/me - Получить текущего пользователя
@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Получить информацию о текущем аутентифицированном пользователе.
    """
    return current_user

# POST /api/users/ - Создать нового пользователя (регистрация)
@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать нового пользователя.
    Доступно всем (регистрация).
    """
    try:
        # Проверяем, существует ли пользователь с таким email
        result = await db.execute(
            select(UserModel).where(UserModel.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        # Хешируем пароль
        hashed_password = get_password_hash(user_data.password)
        
        # Создаем пользователя
        new_user = UserModel(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password,
            role_id=user_data.role_id
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"Создан новый пользователь: {new_user.email}")
        return new_user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать пользователя"
        )

# PUT /api/users/{user_id} - Обновить пользователя
@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Обновить информацию о пользователе.
    Пользователь может обновлять только свой профиль, админ - любой.
    """
    try:
        # Получаем пользователя для обновления
        result = await db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Проверяем права доступа
        is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
        if not is_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для редактирования этого профиля"
            )
        
        # Если обновляется email, проверяем его уникальность
        if user_data.email and user_data.email != user.email:
            result = await db.execute(
                select(UserModel).where(UserModel.email == user_data.email)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже существует"
                )
        
        # Обновляем только переданные поля
        update_data = user_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Обновлен пользователь ID: {user_id}")
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении пользователя {user_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить пользователя"
        )

# PATCH /api/users/{user_id}/password - Изменить пароль
@router.patch("/{user_id}/password")
async def change_password(
    user_id: int,
    passwords: dict,  # {"old_password": "...", "new_password": "..."}
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Изменить пароль пользователя.
    Требуется старый пароль для подтверждения.
    """
    try:
        # Проверяем права доступа
        is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
        if not is_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )
        
        # Получаем пользователя
        result = await db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Проверяем старый пароль (если не админ)
        if not is_admin:
            if "old_password" not in passwords:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Требуется старый пароль"
                )
            
            if not verify_password(passwords["old_password"], user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Неверный старый пароль"
                )
        
        # Проверяем новый пароль
        if "new_password" not in passwords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Требуется новый пароль"
            )
        
        if len(passwords["new_password"]) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Новый пароль должен содержать минимум 6 символов"
            )
        
        # Обновляем пароль
        user.hashed_password = get_password_hash(passwords["new_password"])
        await db.commit()
        
        logger.info(f"Изменен пароль пользователя ID: {user_id}")
        return {"message": "Пароль успешно изменен"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при изменении пароля: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить пароль"
        )

# DELETE /api/users/{user_id} - Удалить пользователя
@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Удалить пользователя.
    Пользователь может удалить только свой аккаунт, админ - любой.
    """
    try:
        # Проверяем права доступа
        is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
        if not is_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для удаления этого профиля"
            )
        
        # Не позволяем удалить самого себя (если не админ)
        if not is_admin and current_user.id == user_id:
            # Проверяем, не последний ли это пользователь
            result = await db.execute(select(UserModel))
            users_count = len(result.scalars().all())
            if users_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нельзя удалить последнего пользователя"
                )
        
        result = await db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        await db.delete(user)
        await db.commit()
        
        logger.info(f"Удален пользователь ID: {user_id}, Email: {user.email}")
        return {"message": "Пользователь успешно удален"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить пользователя"
        )