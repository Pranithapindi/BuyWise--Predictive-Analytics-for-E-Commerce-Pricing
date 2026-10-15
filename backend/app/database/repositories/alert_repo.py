"""
Alert Repository — CRUD for price alerts.
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Alert


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, product_id: str, **kwargs) -> Alert:
        alert = Alert(user_id=user_id, product_id=product_id, **kwargs)
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: str) -> Optional[Alert]:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str) -> List[Alert]:
        result = await self.db.execute(
            select(Alert).where(Alert.user_id == user_id).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_for_product(self, product_id: str) -> List[Alert]:
        result = await self.db.execute(
            select(Alert).where(
                and_(Alert.product_id == product_id, Alert.is_active == True, Alert.is_triggered == False)
            )
        )
        return list(result.scalars().all())

    async def update(self, alert_id: str, **kwargs) -> Optional[Alert]:
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None
        for key, value in kwargs.items():
            if hasattr(alert, key) and value is not None:
                setattr(alert, key, value)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def mark_triggered(self, alert_id: str) -> bool:
        alert = await self.get_by_id(alert_id)
        if not alert:
            return False
        alert.is_triggered = True
        alert.triggered_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def delete(self, alert_id: str) -> bool:
        alert = await self.get_by_id(alert_id)
        if not alert:
            return False
        await self.db.delete(alert)
        await self.db.flush()
        return True
