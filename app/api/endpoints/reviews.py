from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.database.database import get_db
from app.models.reviews import ReviewModel
from app.models.projects import ProjectModel
from app.models.freelancers import FreelancerModel
from app.models.users import UserModel
from app.schemas.reviews import Review, ReviewCreate, ReviewUpdate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD операции ====================

@router.get("/", response_model=List[Review])
async def get_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    project_id: Optional[int] = None,
    freelancer_id: Optional[int] = None,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """Получить список отзывов"""
    query = select(ReviewModel)
    
    if project_id:
        query = query.where(ReviewModel.project_id == project_id)
    
    if freelancer_id:
        query = query.where(ReviewModel.freelancer_id == freelancer_id)
    
    if min_rating:
        query = query.where(ReviewModel.rating >= min_rating)
    
    query = query.order_by(ReviewModel.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    return reviews

@router.get("/{review_id}", response_model=Review)
async def get_review(review_id: int, db: AsyncSession = Depends(get_db)):
    """Получить отзыв по ID"""
    result = await db.execute(
        select(ReviewModel).where(ReviewModel.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    return review

@router.post("/", response_model=Review, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Создать новый отзыв"""
    # Проверяем существование проекта
    result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == review.project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверяем существование фрилансера
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == review.freelancer_id)
    )
    freelancer = result.scalar_one_or_none()
    
    if not freelancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фрилансер не найден"
        )
    
    # Проверяем, является ли пользователь автором отзыва
    if current_user.id != review.reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете оставлять отзывы только от своего имени"
        )
    
    # Проверяем, не оставлял ли уже пользователь отзыв на этот проект
    result = await db.execute(
        select(ReviewModel).where(
            and_(
                ReviewModel.project_id == review.project_id,
                ReviewModel.reviewer_id == review.reviewer_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже оставляли отзыв на этот проект"
        )
    
    db_review = ReviewModel(**review.dict())
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    
    return db_review

@router.put("/{review_id}", response_model=Review)
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Обновить отзыв"""
    result = await db.execute(
        select(ReviewModel).where(ReviewModel.id == review_id)
    )
    db_review = result.scalar_one_or_none()
    
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    # Проверка прав: только автор отзыва может его обновить
    if current_user.id != db_review.reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этого отзыва"
        )
    
    update_data = review_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)
    
    await db.commit()
    await db.refresh(db_review)
    
    return db_review

@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Удалить отзыв"""
    result = await db.execute(
        select(ReviewModel).where(ReviewModel.id == review_id)
    )
    db_review = result.scalar_one_or_none()
    
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    if current_user.id != db_review.reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого отзыва"
        )
    
    await db.delete(db_review)
    await db.commit()
    
    return {"message": "Отзыв удален"}