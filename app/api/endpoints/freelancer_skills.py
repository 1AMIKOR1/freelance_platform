from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.database.database import get_db
from app.models.freelancer_skills import FreelancerSkillModel
from app.models.freelancers import FreelancerModel
from app.models.skills import SkillModel
from app.models.users import UserModel
from app.schemas.freelancer_skills import FreelancerSkill, FreelancerSkillCreate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD операции ====================

@router.get("/", response_model=List[FreelancerSkill])
async def get_freelancer_skills(
    freelancer_id: Optional[int] = Query(None),
    skill_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Получить список связей фрилансер-навык"""
    query = select(FreelancerSkillModel)
    
    if freelancer_id:
        query = query.where(FreelancerSkillModel.freelancer_id == freelancer_id)
    
    if skill_id:
        query = query.where(FreelancerSkillModel.skill_id == skill_id)
    
    result = await db.execute(query)
    freelancer_skills = result.scalars().all()
    return freelancer_skills

@router.post("/", response_model=FreelancerSkill, status_code=status.HTTP_201_CREATED)
async def create_freelancer_skill(
    freelancer_skill: FreelancerSkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Добавить навык фрилансеру"""
    # Проверяем существование фрилансера
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == freelancer_skill.freelancer_id)
    )
    freelancer = result.scalar_one_or_none()
    
    if not freelancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фрилансер не найден"
        )
    
    # Проверяем существование навыка
    result = await db.execute(
        select(SkillModel).where(SkillModel.id == freelancer_skill.skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Навык не найден"
        )
    
    # Проверяем права: только сам фрилансер может добавлять себе навыки
    if current_user.id != freelancer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для добавления навыков этому фрилансеру"
        )
    
    # Проверяем, не добавлен ли уже этот навык
    result = await db.execute(
        select(FreelancerSkillModel).where(
            and_(
                FreelancerSkillModel.freelancer_id == freelancer_skill.freelancer_id,
                FreelancerSkillModel.skill_id == freelancer_skill.skill_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот навык уже добавлен фрилансеру"
        )
    
    db_freelancer_skill = FreelancerSkillModel(**freelancer_skill.dict())
    db.add(db_freelancer_skill)
    await db.commit()
    await db.refresh(db_freelancer_skill)
    
    return db_freelancer_skill

@router.delete("/")
async def delete_freelancer_skill(
    freelancer_id: int,
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Удалить связь фрилансер-навык"""
    result = await db.execute(
        select(FreelancerSkillModel).where(
            and_(
                FreelancerSkillModel.freelancer_id == freelancer_id,
                FreelancerSkillModel.skill_id == skill_id
            )
        )
    )
    db_freelancer_skill = result.scalar_one_or_none()
    
    if not db_freelancer_skill:
        raise HTTPException(status_code=404, detail="Связь не найдена")
    
    # Проверяем существование фрилансера
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == freelancer_id)
    )
    freelancer = result.scalar_one_or_none()
    
    if not freelancer:
        raise HTTPException(status_code=404, detail="Фрилансер не найден")
    
    # Проверяем права: только сам фрилансер может удалять свои навыки
    if current_user.id != freelancer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления навыков у этого фрилансера"
        )
    
    await db.delete(db_freelancer_skill)
    await db.commit()
    
    return {"message": "Связь фрилансер-навык удалена"}