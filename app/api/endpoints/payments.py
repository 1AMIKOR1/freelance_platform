from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.database.database import get_db
from app.models.payments import PaymentModel
from app.models.proposals import ProposalModel
from app.models.users import UserModel
from app.schemas.payments import Payment, PaymentCreate, PaymentUpdate
from app.api.dependencies import get_current_user

router = APIRouter()

# ==================== CRUD операции ====================

@router.get("/", response_model=List[Payment])
async def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    proposal_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Получить список платежей"""
    query = select(PaymentModel)
    
    if status:
        query = query.where(PaymentModel.status == status)
    
    if proposal_id:
        query = query.where(PaymentModel.proposal_id == proposal_id)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    payments = result.scalars().all()
    return payments

@router.get("/{payment_id}", response_model=Payment)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    """Получить платеж по ID"""
    result = await db.execute(
        select(PaymentModel).where(PaymentModel.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Платеж не найден"
        )
    
    return payment

@router.post("/", response_model=Payment, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый платеж"""
    # Проверяем существование предложения
    result = await db.execute(
        select(ProposalModel).where(ProposalModel.id == payment.proposal_id)
    )
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предложение не найдено"
        )
    
    db_payment = PaymentModel(**payment.dict())
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    
    return db_payment

@router.put("/{payment_id}", response_model=Payment)
async def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить платеж"""
    result = await db.execute(
        select(PaymentModel).where(PaymentModel.id == payment_id)
    )
    db_payment = result.scalar_one_or_none()
    
    if not db_payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    
    update_data = payment_update.dict(exclude_unset=True)
    
    # Если статус меняется на "completed", устанавливаем дату платежа
    if update_data.get("status") == "completed" and not db_payment.payment_date:
        update_data["payment_date"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_payment, field, value)
    
    await db.commit()
    await db.refresh(db_payment)
    
    return db_payment

@router.delete("/{payment_id}")
async def delete_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить платеж"""
    result = await db.execute(
        select(PaymentModel).where(PaymentModel.id == payment_id)
    )
    db_payment = result.scalar_one_or_none()
    
    if not db_payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    
    await db.delete(db_payment)
    await db.commit()
    
    return {"message": "Платеж удален"}