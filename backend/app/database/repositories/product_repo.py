"""
Product Repository — CRUD operations for the products table.
"""
from typing import Optional, List
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Product


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, url: str, website: str, scrape_interval: int = 60, **kwargs) -> Product:
        product = Product(user_id=user_id, url=url, website=website, scrape_interval=scrape_interval, **kwargs)
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def get_by_id(self, product_id: str) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user(self, product_id: str, user_id: str) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(
                and_(Product.id == product_id, Product.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Product]:
        result = await self.db.execute(
            select(Product)
            .where(Product.user_id == user_id)
            .order_by(Product.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_active(self) -> List[Product]:
        """Get all active products for the scheduler."""
        result = await self.db.execute(
            select(Product).where(Product.is_active == True)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Product).where(Product.user_id == user_id)
        )
        return result.scalar_one()

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Product))
        return result.scalar_one()

    async def update(self, product_id: str, **kwargs) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        for key, value in kwargs.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete(self, product_id: str) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False
        await self.db.delete(product)
        await self.db.flush()
        return True

    async def search(
        self,
        q: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        website: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        min_discount: Optional[float] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Product], int]:
        query = select(Product).where(Product.is_active == True)

        if q:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{q}%"),
                    Product.brand.ilike(f"%{q}%"),
                    Product.category.ilike(f"%{q}%"),
                )
            )
        if brand:
            query = query.where(Product.brand.ilike(f"%{brand}%"))
        if category:
            query = query.where(Product.category.ilike(f"%{category}%"))
        if website:
            query = query.where(Product.website == website)
        if min_price is not None:
            query = query.where(Product.current_price >= min_price)
        if max_price is not None:
            query = query.where(Product.current_price <= max_price)
        if min_rating is not None:
            query = query.where(Product.current_rating >= min_rating)
        if min_discount is not None:
            query = query.where(Product.current_discount >= min_discount)

        # Count
        count_q = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_q)
        total = total_result.scalar_one()

        # Paginated results
        result = await self.db.execute(
            query.order_by(Product.current_discount.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_most_tracked(self, limit: int = 10) -> List[dict]:
        """Products tracked by most users."""
        result = await self.db.execute(
            select(Product.name, Product.website, func.count(Product.id).label("track_count"))
            .group_by(Product.name, Product.website)
            .order_by(func.count(Product.id).desc())
            .limit(limit)
        )
        rows = result.all()
        return [{"name": r.name, "website": r.website, "track_count": r.track_count} for r in rows]
