from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database.database import get_db
from app.models.skills import SkillModel
from app.models.users import UserModel
from app.schemas.skills import Skill, SkillCreate, SkillUpdate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD операции ====================

@router.get("/", response_model=List[Skill])
async def get_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """Получить список навыков"""
    query = select(SkillModel)
    
    if search:
        query = query.where(SkillModel.name.ilike(f"%{search}%"))
    
    query = query.order_by(SkillModel.name)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    skills = result.scalars().all()
    return skills

@router.get("/{skill_id}", response_model=Skill)
async def get_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    """Получить навык по ID"""
    result = await db.execute(
        select(SkillModel).where(SkillModel.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Навык не найден"
        )
    
    return skill

@router.post("/", response_model=Skill, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Создать новый навык"""
    # Проверяем, существует ли уже навык с таким названием
    result = await db.execute(
        select(SkillModel).where(SkillModel.name == skill.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Навык с таким названием уже существует"
        )
    
    db_skill = SkillModel(**skill.dict())
    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)
    
    return db_skill

@router.put("/{skill_id}", response_model=Skill)
async def update_skill(
    skill_id: int,
    skill_update: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Обновить навык"""
    result = await db.execute(
        select(SkillModel).where(SkillModel.id == skill_id)
    )
    db_skill = result.scalar_one_or_none()
    
    if not db_skill:
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    update_data = skill_update.dict(exclude_unset=True)
    
    # Если обновляется название, проверяем уникальность
    if "name" in update_data and update_data["name"] != db_skill.name:
        result = await db.execute(
            select(SkillModel).where(SkillModel.name == update_data["name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Навык с таким названием уже существует"
            )
    
    for field, value in update_data.items():
        setattr(db_skill, field, value)
    
    await db.commit()
    await db.refresh(db_skill)
    
    return db_skill

@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить навык"""
    result = await db.execute(
        select(SkillModel).where(SkillModel.id == skill_id)
    )
    db_skill = result.scalar_one_or_none()
    
    if not db_skill:
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    await db.delete(db_skill)
    await db.commit()
    
    return {"message": "Навык удален"}