from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.database.database import get_db
from app.models.proposals import ProposalModel
from app.models.projects import ProjectModel
from app.models.freelancers import FreelancerModel
from app.models.users import UserModel
from app.schemas.proposals import Proposal, ProposalCreate, ProposalUpdate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD для предложений ====================

# GET /api/proposals/ - Получить все предложения (с фильтрами)
@router.get("/", response_model=List[Proposal])
async def get_proposals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    freelancer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Получить список предложений с пагинацией и фильтрацией.
    """
    query = select(ProposalModel)
    
    if status:
        query = query.where(ProposalModel.status == status)
    
    if project_id:
        query = query.where(ProposalModel.project_id == project_id)
    
    if freelancer_id:
        query = query.where(ProposalModel.freelancer_id == freelancer_id)
    
    query = query.order_by(ProposalModel.submitted_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    proposals = result.scalars().all()
    return proposals

# GET /api/proposals/{proposal_id} - Получить предложение по ID
@router.get("/{proposal_id}", response_model=Proposal)
async def get_proposal(proposal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProposalModel).where(ProposalModel.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предложение не найден"
        )
    
    return proposal

# POST /api/proposals/ - Создать новое предложение
@router.post("/", response_model=Proposal, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    proposal: ProposalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Проверяем существование проекта
    result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == proposal.project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверяем существование фрилансера
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == proposal.freelancer_id)
    )
    freelancer = result.scalar_one_or_none()
    
    if not freelancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фрилансер не найден"
        )
    
    # Проверяем, что текущий пользователь - это фрилансер, который создает предложение
    if current_user.id != freelancer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете создавать предложения только от своего имени"
        )
    
    # Проверяем, не закрыт ли проект
    if project.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя оставлять предложения на закрытый проект"
        )
    
    # Проверяем, не оставлял ли уже этот фрилансер предложение на этот проект
    result = await db.execute(
        select(ProposalModel).where(
            and_(
                ProposalModel.project_id == proposal.project_id,
                ProposalModel.freelancer_id == proposal.freelancer_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже оставляли предложение на этот проект"
        )
    
    # Создаем предложение
    db_proposal = ProposalModel(**proposal.dict())
    db.add(db_proposal)
    await db.commit()
    await db.refresh(db_proposal)
    
    return db_proposal

# PUT /api/proposals/{proposal_id} - Обновить предложение
@router.put("/{proposal_id}", response_model=Proposal)
async def update_proposal(
    proposal_id: int,
    proposal_update: ProposalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    result = await db.execute(
        select(ProposalModel).where(ProposalModel.id == proposal_id)
    )
    db_proposal = result.scalar_one_or_none()
    
    if not db_proposal:
        raise HTTPException(status_code=404, detail="Предложение не найден")
    
    # Находим фрилансера, который оставил это предложение
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == db_proposal.freelancer_id)
    )
    freelancer = result.scalar_one_or_none()
    
    if not freelancer:
        raise HTTPException(status_code=404, detail="Фрилансер не найден")
    
    # Проверка прав: только фрилансер, создавший предложение, может его обновить
    if current_user.id != freelancer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этого предложения"
        )
    
    # Нельзя обновить принятое или отклоненное предложение
    if db_proposal.status in ["accepted", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя редактировать принятое или отклоненное предложение"
        )
    
    update_data = proposal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_proposal, field, value)
    
    await db.commit()
    await db.refresh(db_proposal)
    
    return db_proposal

# DELETE /api/proposals/{proposal_id} - Удалить предложение
@router.delete("/{proposal_id}")
async def delete_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    result = await db.execute(
        select(ProposalModel).where(ProposalModel.id == proposal_id)
    )
    db_proposal = result.scalar_one_or_none()
    
    if not db_proposal:
        raise HTTPException(status_code=404, detail="Предложение не найден")
    
    # Находим фрилансера, который оставил это предложение
    result = await db.execute(
        select(FreelancerModel).where(FreelancerModel.id == db_proposal.freelancer_id)
    )
    freelancer = result.scalar_one_or_none()
    
    if not freelancer:
        raise HTTPException(status_code=404, detail="Фрилансер не найден")
    
    # Проверка прав: только фрилансер, создавший предложение, может его удалить
    if current_user.id != freelancer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого предложения"
        )
    
    # Нельзя удалить принятое предложение
    if db_proposal.status == "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить принятое предложение"
        )
    
    await db.delete(db_proposal)
    await db.commit()
    
    return {"message": "Предложение удалено"}