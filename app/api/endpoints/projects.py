from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.database.database import get_db
from app.models.projects import ProjectModel
from app.models.users import UserModel
from app.schemas.projects import Project, ProjectCreate, ProjectUpdate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD для проектов ====================

# GET /api/projects/ - Получить все проекты
@router.get("/", response_model=List[Project])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    min_budget: Optional[float] = Query(None, ge=0),
    max_budget: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None, min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Получить список проектов с пагинацией и фильтрацией.
    """
    query = select(ProjectModel)
    
    if status:
        query = query.where(ProjectModel.status == status)
    
    if min_budget is not None:
        query = query.where(ProjectModel.budget >= min_budget)
    
    if max_budget is not None:
        query = query.where(ProjectModel.budget <= max_budget)
    
    if search:
        query = query.where(
            (ProjectModel.title.ilike(f"%{search}%")) | 
            (ProjectModel.description.ilike(f"%{search}%"))
        )
    
    # Показываем сначала открытые проекты
    query = query.order_by(ProjectModel.status, ProjectModel.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    projects = result.scalars().all()
    return projects

# GET /api/projects/{project_id} - Получить проект по ID
@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    return project

# POST /api/projects/ - Создать новый проект
@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Проверяем, что пользователь существует и является клиентом
    result = await db.execute(
        select(UserModel).where(UserModel.id == project.client_id)
    )
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден"
        )
    
    # Проверяем, что текущий пользователь - это клиент, который создает проект
    if current_user.id != project.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете создавать проекты только от своего имени"
        )
    
    # Создаем проект
    db_project = ProjectModel(**project.dict())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    
    return db_project

# PUT /api/projects/{project_id} - Обновить проект
@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    db_project = result.scalar_one_or_none()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    
    # Проверка прав: только клиент, создавший проект, может его обновлять
    if current_user.id != db_project.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этого проекта"
        )
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    await db.commit()
    await db.refresh(db_project)
    
    return db_project

# DELETE /api/projects/{project_id} - Удалить проект
@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    db_project = result.scalar_one_or_none()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    
    # Проверка прав: только клиент, создавший проект, может его удалить
    if current_user.id != db_project.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого проекта"
        )
    
    await db.delete(db_project)
    await db.commit()
    
    return {"message": "Проект удален"}