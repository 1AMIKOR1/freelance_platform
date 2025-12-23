from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.database.database import get_db
from app.models.freelancers import FreelancerModel
from app.models.users import UserModel
from app.schemas.freelancers import Freelancer, FreelancerCreate, FreelancerUpdate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD для фрилансеров ====================

# GET /api/freelancers/ - Получить всех фрилансеров
@router.get("/", response_model=List[Freelancer])
async def get_freelancers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    min_rate: Optional[float] = Query(None, ge=0),
    max_rate: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None, min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список фрилансеров с пагинацией и фильтрацией.
    """
    # Начинаем запрос с join таблицы пользователей, чтобы можно было искать по имени
    query = select(FreelancerModel).join(UserModel)
    
    if min_rate is not None:
        query = query.where(FreelancerModel.hourly_rate >= min_rate)
    
    if max_rate is not None:
        query = query.where(FreelancerModel.hourly_rate <= max_rate)
    
    if search:
        query = query.where(
            UserModel.name.ilike(f"%{search}%") | 
            FreelancerModel.bio.ilike(f"%{search}%")
        )
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    freelancers = result.scalars().all()
    return freelancers

# GET /api/freelancers/{freelancer_id} - Получить фрилансера по ID
@router.get("/{freelancer_id}", response_model=Freelancer)
async def get_freelancer(freelancer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == freelancer_id)
    )
    freelancer = result.scalar_one_or_none()
    
    if not freelancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фрилансер не найден"
        )
    
    return freelancer

# POST /api/freelancers/ - Создать профиль фрилансера
@router.post("/", response_model=Freelancer, status_code=status.HTTP_201_CREATED)
async def create_freelancer(
    freelancer: FreelancerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Проверяем, существует ли пользователь с таким user_id
    result = await db.execute(
        select(UserModel).where(UserModel.id == freelancer.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверяем, есть ли уже профиль фрилансера у этого пользователя
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.user_id == freelancer.user_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Профиль фрилансера для этого пользователя уже существует"
        )
    
    # Создаем профиль фрилансера
    db_freelancer = FreelancerModel(**freelancer.dict())
    db.add(db_freelancer)
    await db.commit()
    await db.refresh(db_freelancer)
    
    return db_freelancer

# PUT /api/freelancers/{freelancer_id} - Обновить профиль фрилансера
@router.put("/{freelancer_id}", response_model=Freelancer)
async def update_freelancer(
    freelancer_id: int,
    freelancer_update: FreelancerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == freelancer_id)
    )
    db_freelancer = result.scalar_one_or_none()
    
    if not db_freelancer:
        raise HTTPException(status_code=404, detail="Фрилансер не найден")
    
    # Проверка прав: только сам фрилансер может обновлять свой профиль
    # (предполагаем, что в токене есть ID пользователя, а у фрилансера есть user_id)
    if current_user.id != db_freelancer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этого профиля"
        )
    
    update_data = freelancer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_freelancer, field, value)
    
    await db.commit()
    await db.refresh(db_freelancer)
    
    return db_freelancer

# DELETE /api/freelancers/{freelancer_id} - Удалить профиль фрилансера
@router.delete("/{freelancer_id}")
async def delete_freelancer(
    freelancer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == freelancer_id)
    )
    db_freelancer = result.scalar_one_or_none()
    
    if not db_freelancer:
        raise HTTPException(status_code=404, detail="Фрилансер не найден")
    
    # Проверка прав: только сам фрилансер может удалить свой профиль
    if current_user.id != db_freelancer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого профиля"
        )
    
    await db.delete(db_freelancer)
    await db.commit()
    
    return {"message": "Профиль фрилансера удален"}