from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.database.database import get_db
from app.models.messages import MessageModel
from app.models.users import UserModel
from app.schemas.messages import Message, MessageCreate, MessageUpdate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD операции ====================

@router.get("/", response_model=List[Message])
async def get_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    sender_id: Optional[int] = None,
    recipient_id: Optional[int] = None,
    unread_only: Optional[bool] = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Получить список сообщений"""
    query = select(MessageModel).where(
        (MessageModel.sender_id == current_user.id) |
        (MessageModel.recipient_id == current_user.id)
    )
    
    if sender_id:
        query = query.where(MessageModel.sender_id == sender_id)
    
    if recipient_id:
        query = query.where(MessageModel.recipient_id == recipient_id)
    
    if unread_only:
        query = query.where(MessageModel.is_read == False)
    
    query = query.order_by(MessageModel.timestamp.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    return messages

@router.get("/{message_id}", response_model=Message)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Получить сообщение по ID"""
    result = await db.execute(
        select(MessageModel).where(MessageModel.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено"
        )
    
    # Проверяем права доступа
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этого сообщения"
        )
    
    return message

@router.post("/", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Отправить новое сообщение"""
    # Проверяем существование получателя
    result = await db.execute(
        select(UserModel).where(UserModel.id == message.recipient_id)
    )
    recipient = result.scalar_one_or_none()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Получатель не найден"
        )
    
    # Нельзя отправлять сообщение самому себе
    if current_user.id == message.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя отправлять сообщение самому себе"
        )
    
    db_message = MessageModel(
        content=message.content,
        sender_id=current_user.id,
        recipient_id=message.recipient_id
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    
    return db_message

@router.put("/{message_id}", response_model=Message)
async def update_message(
    message_id: int,
    message_update: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Обновить сообщение"""
    result = await db.execute(
        select(MessageModel).where(MessageModel.id == message_id)
    )
    db_message = result.scalar_one_or_none()
    
    if not db_message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    # Проверка прав: только отправитель может обновлять сообщение
    if current_user.id != db_message.sender_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этого сообщения"
        )
    
    update_data = message_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_message, field, value)
    
    await db.commit()
    await db.refresh(db_message)
    
    return db_message

@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Удалить сообщение"""
    result = await db.execute(
        select(MessageModel).where(MessageModel.id == message_id)
    )
    db_message = result.scalar_one_or_none()
    
    if not db_message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    # Проверка прав: только отправитель или получатель могут удалить сообщение
    if current_user.id != db_message.sender_id and current_user.id != db_message.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого сообщения"
        )
    
    await db.delete(db_message)
    await db.commit()
    
    return {"message": "Сообщение удалено"}