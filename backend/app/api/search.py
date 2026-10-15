"""
Search API Router — full-text product search with filters.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from app.core.dependencies import get_db, get_current_active_user
from app.database.models import User
from app.database.repositories.product_repo import ProductRepository

router = APIRouter()


@router.get("")
async def search_products(
    q: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    website: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    min_discount: Optional[float] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Search and filter tracked products."""
    repo = ProductRepository(db)
    skip = (page - 1) * page_size

    products, total = await repo.search(
        q=q,
        brand=brand,
        category=category,
        website=website,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        min_discount=min_discount,
        skip=skip,
        limit=page_size,
    )

    return {
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "website": p.website,
                "current_price": float(p.current_price) if p.current_price else None,
                "current_discount": float(p.current_discount) if p.current_discount else None,
                "current_rating": float(p.current_rating) if p.current_rating else None,
                "image_url": p.image_url,
                "availability": p.availability,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size),
    }
