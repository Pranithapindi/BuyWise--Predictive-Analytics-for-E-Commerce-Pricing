"""
Admin API Router — admin-only views for users, logs, system stats.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from typing import List

from app.core.dependencies import get_db, get_admin_user
from app.database.models import User, Product, ScrapeLog, ScrapeStatus
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.product_repo import ProductRepository
from app.database.schemas import UserResponse, ScrapeLogResponse

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
):
    """List all registered users."""
    repo = UserRepository(db)
    return await repo.get_all(skip=skip, limit=limit)


@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
):
    """System-wide statistics for admin dashboard."""
    user_repo = UserRepository(db)
    product_repo = ProductRepository(db)

    total_users = await user_repo.count()
    total_products = await product_repo.count_all()
    most_tracked = await product_repo.get_most_tracked(10)

    # Today's scrape stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_today = await db.execute(
        select(func.count(ScrapeLog.id)).where(ScrapeLog.scraped_at >= today_start)
    )
    failed_today = await db.execute(
        select(func.count(ScrapeLog.id)).where(
            and_(ScrapeLog.scraped_at >= today_start, ScrapeLog.status == ScrapeStatus.FAILED)
        )
    )

    # Website distribution
    website_dist = await db.execute(
        select(Product.website, func.count(Product.id).label("count"))
        .group_by(Product.website)
        .order_by(func.count(Product.id).desc())
    )
    website_stats = {row.website: row.count for row in website_dist.all()}

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_scrapes_today": total_today.scalar_one(),
        "failed_scrapes_today": failed_today.scalar_one(),
        "most_tracked_products": most_tracked,
        "website_statistics": website_stats,
    }


@router.get("/logs")
async def get_scrape_logs(
    limit: int = Query(100, le=500),
    status_filter: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
):
    """Get recent scrape logs, optionally filtered by status."""
    query = select(ScrapeLog).order_by(ScrapeLog.scraped_at.desc()).limit(limit)
    if status_filter:
        try:
            status_enum = ScrapeStatus(status_filter)
            query = query.where(ScrapeLog.status == status_enum)
        except ValueError:
            pass

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "product_id": l.product_id,
                "status": l.status.value,
                "error_message": l.error_message,
                "response_time_ms": l.response_time_ms,
                "scraped_at": l.scraped_at.isoformat(),
            }
            for l in logs
        ],
    }


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
):
    """Deactivate a user account."""
    repo = UserRepository(db)
    success = await repo.deactivate(user_id)
    if not success:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": f"User {user_id} deactivated"}
