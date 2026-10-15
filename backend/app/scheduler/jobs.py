"""
APScheduler Jobs — automatic price scraping on configured intervals.
"""
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_scrape_job(interval_minutes: int):
    """
    Scrape all active products whose scrape_interval matches the given interval.
    Uses its own DB session per run to avoid connection leaks.
    """
    from app.database.session import AsyncSessionLocal
    from app.database.repositories.product_repo import ProductRepository
    from app.database.repositories.price_history_repo import PriceHistoryRepository
    from app.database.models import ScrapeLog, ScrapeStatus
    from app.scrapers.scraper_factory import scrape_product

    logger.info(f"⏰ Scrape job running for interval={interval_minutes}m")

    async with AsyncSessionLocal() as db:
        try:
            product_repo = ProductRepository(db)
            history_repo = PriceHistoryRepository(db)

            all_active = await product_repo.get_all_active()
            targets = [p for p in all_active if p.scrape_interval == interval_minutes]

            logger.info(f"Found {len(targets)} products to scrape at {interval_minutes}m interval")

            for product in targets:
                try:
                    result = scrape_product(product.url)

                    # Log the scrape attempt
                    status = ScrapeStatus.SUCCESS if result.success else (
                        ScrapeStatus.CAPTCHA if result.error and "captcha" in (result.error or "").lower()
                        else ScrapeStatus.FAILED
                    )
                    log = ScrapeLog(
                        product_id=product.id,
                        status=status,
                        error_message=result.error if not result.success else None,
                        response_time_ms=result.response_time_ms,
                    )
                    db.add(log)

                    if result.success and result.price:
                        # Save price history
                        await history_repo.add(
                            product_id=product.id,
                            price=result.price,
                            original_price=result.original_price,
                            discount_pct=result.discount_pct,
                            rating=result.rating,
                            review_count=result.review_count,
                            availability=result.availability,
                            seller=result.seller,
                            delivery_charges=result.delivery_charges,
                        )

                        # Update product current info
                        await product_repo.update(
                            product.id,
                            name=result.name or product.name,
                            brand=result.brand or product.brand,
                            category=result.category or product.category,
                            image_url=result.image_url or product.image_url,
                            current_price=result.price,
                            original_price=result.original_price,
                            current_discount=result.discount_pct,
                            current_rating=result.rating,
                            review_count=result.review_count,
                            availability=result.availability,
                            seller=result.seller,
                            delivery_charges=result.delivery_charges,
                            last_scraped_at=datetime.now(timezone.utc),
                        )

                        # Check alerts
                        await _check_alerts(db, product.id, result.price, result.discount_pct)

                except Exception as e:
                    logger.error(f"Error scraping product {product.id}: {e}")

            await db.commit()
            logger.info(f"✅ Scrape job complete for interval={interval_minutes}m")

        except Exception as e:
            await db.rollback()
            logger.error(f"Scrape job failed: {e}")


async def _check_alerts(db, product_id: str, current_price: float, discount_pct: float | None):
    """Check if any alerts should be triggered for this product."""
    from app.database.repositories.alert_repo import AlertRepository
    from app.services.email_service import send_price_alert_email
    from app.database.repositories.user_repo import UserRepository
    from datetime import datetime, timezone

    alert_repo = AlertRepository(db)
    alerts = await alert_repo.get_active_for_product(product_id)

    for alert in alerts:
        triggered = False
        if alert.target_price and current_price <= alert.target_price:
            triggered = True
        if alert.target_discount and discount_pct and discount_pct >= alert.target_discount:
            triggered = True
        if alert.max_budget and current_price <= alert.max_budget:
            triggered = True

        if triggered:
            await alert_repo.mark_triggered(alert.id)
            if alert.notify_email:
                user_repo = UserRepository(db)
                user = await user_repo.get_by_id(alert.user_id)
                if user:
                    await send_price_alert_email(
                        user.email,
                        product_id=product_id,
                        current_price=current_price,
                        target_price=alert.target_price,
                    )
            logger.info(f"🔔 Alert triggered: product={product_id} price={current_price}")


def setup_scraper_jobs():
    """Register all interval-based scrape jobs with APScheduler."""
    intervals = [30, 60, 360, 1440]

    for interval in intervals:
        scheduler.add_job(
            func=_run_scrape_job,
            args=[interval],
            trigger=IntervalTrigger(minutes=interval),
            id=f"scrape_{interval}m",
            name=f"Price Scrape ({interval}m)",
            replace_existing=True,
            misfire_grace_time=60,
        )
        logger.info(f"📅 Registered scrape job every {interval} minutes")


# Register jobs when module is imported
setup_scraper_jobs()
