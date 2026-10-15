"""
Alerts API Router — CRUD for price alerts.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_db, get_current_active_user
from app.database.models import User
from app.database.schemas import AlertCreate, AlertUpdate, AlertResponse, MessageResponse
from app.database.repositories.alert_repo import AlertRepository
from app.database.repositories.product_repo import ProductRepository

router = APIRouter()


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new price alert for a tracked product."""
    # Verify product ownership
    product_repo = ProductRepository(db)
    product = await product_repo.get_by_id_and_user(data.product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if not data.target_price and not data.target_discount and not data.max_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of target_price, target_discount, or max_budget is required",
        )

    repo = AlertRepository(db)
    alert = await repo.create(
        user_id=current_user.id,
        product_id=data.product_id,
        target_price=data.target_price,
        target_discount=data.target_discount,
        max_budget=data.max_budget,
        notify_email=data.notify_email,
        notify_sms=data.notify_sms,
        notify_browser=data.notify_browser,
    )
    return alert


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all alerts for the current user."""
    repo = AlertRepository(db)
    return await repo.get_by_user(current_user.id)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing alert."""
    repo = AlertRepository(db)
    alert = await repo.get_by_id(alert_id)
    if not alert or alert.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    updated = await repo.update(alert_id, **data.model_dump(exclude_none=True))
    return updated


@router.delete("/{alert_id}", response_model=MessageResponse)
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a price alert."""
    repo = AlertRepository(db)
    alert = await repo.get_by_id(alert_id)
    if not alert or alert.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await repo.delete(alert_id)
    return MessageResponse(message="Alert deleted")
