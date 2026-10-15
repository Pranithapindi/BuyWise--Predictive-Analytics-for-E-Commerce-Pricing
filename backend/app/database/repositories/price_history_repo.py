"""
Price History Repository — store and query historical price data.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PriceHistory


class PriceHistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        product_id: str,
        price: float,
        original_price: Optional[float] = None,
        discount_pct: Optional[float] = None,
        rating: Optional[float] = None,
        review_count: Optional[int] = None,
        availability: Optional[str] = None,
        seller: Optional[str] = None,
        delivery_charges: Optional[float] = None,
    ) -> PriceHistory:
        record = PriceHistory(
            product_id=product_id,
            price=price,
            original_price=original_price,
            discount_pct=discount_pct,
            rating=rating,
            review_count=review_count,
            availability=availability,
            seller=seller,
            delivery_charges=delivery_charges,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get_by_product(
        self,
        product_id: str,
        limit: int = 200,
        since: Optional[datetime] = None,
    ) -> List[PriceHistory]:
        query = select(PriceHistory).where(PriceHistory.product_id == product_id)
        if since:
            query = query.where(PriceHistory.scraped_at >= since)
        query = query.order_by(desc(PriceHistory.scraped_at)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stats(self, product_id: str) -> dict:
        """Aggregate price stats: min, max, avg."""
        result = await self.db.execute(
            select(
                func.min(PriceHistory.price).label("min_price"),
                func.max(PriceHistory.price).label("max_price"),
                func.avg(PriceHistory.price).label("avg_price"),
                func.count(PriceHistory.id).label("count"),
            ).where(PriceHistory.product_id == product_id)
        )
        row = result.one()
        return {
            "min_price": float(row.min_price) if row.min_price else None,
            "max_price": float(row.max_price) if row.max_price else None,
            "avg_price": float(row.avg_price) if row.avg_price else None,
            "count": row.count,
        }

    async def get_monthly_data(self, product_id: str) -> List[dict]:
        """Monthly average price for the last 12 months."""
        since = datetime.now(timezone.utc) - timedelta(days=365)
        records = await self.get_by_product(product_id, limit=5000, since=since)
        # Group by month
        monthly: dict = {}
        for r in records:
            key = r.scraped_at.strftime("%Y-%m")
            if key not in monthly:
                monthly[key] = []
            monthly[key].append(float(r.price))
        return [
            {"month": k, "avg_price": sum(v) / len(v), "min_price": min(v), "max_price": max(v)}
            for k, v in sorted(monthly.items())
        ]

    async def get_prices_as_series(self, product_id: str, limit: int = 365) -> List[dict]:
        """Return chronological price series for ML input."""
        records = await self.get_by_product(product_id, limit=limit)
        records.reverse()  # Oldest first
        return [
            {"date": r.scraped_at.isoformat(), "price": float(r.price)}
            for r in records
        ]
