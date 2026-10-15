"""
Analytics API Router — price stats, history, trends, charts, heatmap.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.dependencies import get_db, get_current_active_user
from app.database.models import User
from app.database.repositories.product_repo import ProductRepository
from app.database.repositories.price_history_repo import PriceHistoryRepository
from app.analytics.price_analytics import PriceAnalytics

router = APIRouter()


async def _get_product_or_404(product_id: str, user_id: str, db: AsyncSession):
    repo = ProductRepository(db)
    product = await repo.get_by_id_and_user(product_id, user_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.get("/{product_id}/summary")
async def get_summary(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """High-level price summary: current, highest, lowest, avg, drop%, volatility."""
    product = await _get_product_or_404(product_id, current_user.id, db)
    history_repo = PriceHistoryRepository(db)
    series = await history_repo.get_prices_as_series(product_id)
    prices = [s["price"] for s in series]

    summary = PriceAnalytics.get_summary(prices, float(product.current_price) if product.current_price else None)
    summary["product_id"] = product_id
    summary["total_data_points"] = len(prices)
    return summary


@router.get("/{product_id}/history")
async def get_history(
    product_id: str,
    limit: int = Query(200, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Raw price history records, most recent first."""
    await _get_product_or_404(product_id, current_user.id, db)
    history_repo = PriceHistoryRepository(db)
    records = await history_repo.get_by_product(product_id, limit=limit)
    return {
        "product_id": product_id,
        "count": len(records),
        "history": [
            {
                "id": r.id,
                "price": float(r.price),
                "original_price": float(r.original_price) if r.original_price else None,
                "discount_pct": float(r.discount_pct) if r.discount_pct else None,
                "rating": float(r.rating) if r.rating else None,
                "availability": r.availability,
                "scraped_at": r.scraped_at.isoformat(),
            }
            for r in records
        ],
    }


@router.get("/{product_id}/stats")
async def get_stats(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Statistical measures: mean, median, mode, std dev, moving averages, outliers."""
    await _get_product_or_404(product_id, current_user.id, db)
    history_repo = PriceHistoryRepository(db)
    series = await history_repo.get_prices_as_series(product_id)
    prices = [s["price"] for s in series]

    if len(prices) < 2:
        return {"product_id": product_id, "insufficient_data": True, "message": "Need at least 2 data points for statistics"}

    return {"product_id": product_id, **PriceAnalytics.get_stats(prices)}


@router.get("/{product_id}/trends")
async def get_trends(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Weekly, monthly, and seasonal price trends."""
    await _get_product_or_404(product_id, current_user.id, db)
    history_repo = PriceHistoryRepository(db)
    series = await history_repo.get_prices_as_series(product_id)

    return {"product_id": product_id, **PriceAnalytics.get_trends(series)}


@router.get("/{product_id}/chart")
async def get_chart_data(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Chart.js-ready price timeline with moving average overlay."""
    await _get_product_or_404(product_id, current_user.id, db)
    history_repo = PriceHistoryRepository(db)
    series = await history_repo.get_prices_as_series(product_id)

    return {"product_id": product_id, **PriceAnalytics.get_chart_data(series)}


@router.get("/{product_id}/heatmap")
async def get_heatmap(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Weekly price heatmap data (day-of-week × week-number)."""
    await _get_product_or_404(product_id, current_user.id, db)
    history_repo = PriceHistoryRepository(db)
    series = await history_repo.get_prices_as_series(product_id)

    return {"product_id": product_id, "heatmap": PriceAnalytics.get_heatmap_data(series)}


@router.get("/{product_id}/monthly")
async def get_monthly(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Monthly average/min/max price for the past 12 months."""
    await _get_product_or_404(product_id, current_user.id, db)
    history_repo = PriceHistoryRepository(db)
    monthly = await history_repo.get_monthly_data(product_id)
    return {"product_id": product_id, "monthly": monthly}
