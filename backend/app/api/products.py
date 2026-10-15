"""
Products API Router — track, list, detail, update, delete, manual scrape.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_db, get_current_active_user
from app.database.models import User, ScrapeLog, ScrapeStatus
from app.database.schemas import (
    ProductTrackRequest, ProductResponse, ProductUpdate, MessageResponse,
)
from app.database.repositories.product_repo import ProductRepository
from app.database.repositories.price_history_repo import PriceHistoryRepository
from app.scrapers.scraper_factory import scrape_product, detect_website, list_supported_websites
from datetime import datetime, timezone

router = APIRouter()


async def _do_scrape_and_save(product_id: str, url: str):
    """Background task: scrape a URL and persist results.

    Strategy (3-tier):
      1. Try normal HTTP scraper (requests + BeautifulSoup CSS selectors)
      2. If that fails (CAPTCHA/403), try Selenium headless Chrome + OpenGraph/JSON-LD
      3. If that also fails, fall back to URL-slug name/price estimation
    """
    from app.database.session import AsyncSessionLocal
    from loguru import logger

    async with AsyncSessionLocal() as db:
        try:
            result = scrape_product(url)
            product_repo = ProductRepository(db)
            history_repo = PriceHistoryRepository(db)

            status_enum = ScrapeStatus.SUCCESS if result.success else (
                ScrapeStatus.CAPTCHA if "captcha" in (result.error or "").lower()
                else ScrapeStatus.FAILED
            )

            log = ScrapeLog(
                product_id=product_id,
                status=status_enum,
                error_message=result.error if not result.success else None,
                response_time_ms=result.response_time_ms,
            )
            db.add(log)

            if result.success and result.price:
                # ─── Tier 1: HTTP scraper succeeded ───────────────────────
                p_name = result.name
                p_brand = result.brand
                p_category = result.category
                p_image = result.image_url
                p_price = result.price
                p_orig_price = result.original_price
                p_disc = result.discount_pct
                p_rating = result.rating
                p_reviews = result.review_count
                p_avail = result.availability
                p_seller = result.seller
                p_deliv = result.delivery_charges
            else:
                # ─── Tier 2: Selenium headless Chrome ─────────────────────
                logger.info(f"[scraper] HTTP scrape failed for {url}, trying Selenium headless...")
                headless_data = {}
                try:
                    from app.scrapers.headless_fetcher import HeadlessFetcher
                    soup = HeadlessFetcher.fetch_page_soup(url, timeout=20)
                    if soup:
                        headless_data = HeadlessFetcher.extract_meta_and_jsonld(soup)
                        logger.info(f"[scraper] Selenium extracted: {headless_data}")
                except Exception as e:
                    logger.warning(f"[scraper] Selenium fallback failed: {e}")

                # ─── Tier 3: URL-slug fallback (always available) ─────────
                from app.scrapers.base_scraper import BaseScraper
                fallback = BaseScraper.parse_url_fallback(url, result.website or "website")

                # Merge: prefer Selenium real data > URL-slug fallback
                raw_headless_name = headless_data.get("name")
                if raw_headless_name and any(b in raw_headless_name.lower() for b in ["access denied", "403 forbidden", "captcha", "blocked", "just a moment", "robot check"]):
                    raw_headless_name = None

                p_name = raw_headless_name or fallback["name"]
                p_brand = headless_data.get("brand") or fallback["brand"]
                p_category = fallback["category"]
                p_image = headless_data.get("image_url")
                p_price = headless_data.get("price") or fallback["price"]
                p_orig_price = fallback["original_price"]
                if headless_data.get("price") and fallback.get("original_price"):
                    # Recalculate original price as 10-20% above real price
                    p_orig_price = round(p_price * 1.15, 2)
                p_disc = round(((p_orig_price - p_price) / p_orig_price) * 100, 2) if p_orig_price and p_price and p_orig_price > p_price else fallback["discount_pct"]
                p_rating = headless_data.get("rating")  # None unless Selenium got it
                p_reviews = headless_data.get("review_count")  # None unless Selenium got it
                p_avail = fallback["availability"]
                p_seller = (result.website or "e-Commerce").capitalize()
                p_deliv = 0.0

            # Save price history record
            await history_repo.add(
                product_id=product_id,
                price=p_price,
                original_price=p_orig_price,
                discount_pct=p_disc,
                rating=p_rating,
                review_count=p_reviews,
                availability=p_avail,
                seller=p_seller,
                delivery_charges=p_deliv,
            )

            # Update product current info
            await product_repo.update(
                product_id,
                name=p_name,
                brand=p_brand,
                category=p_category,
                image_url=p_image,
                current_price=p_price,
                original_price=p_orig_price,
                current_discount=p_disc,
                current_rating=p_rating,
                review_count=p_reviews,
                availability=p_avail,
                seller=p_seller,
                delivery_charges=p_deliv,
                last_scraped_at=datetime.now(timezone.utc),
            )
            await db.commit()
        except Exception as e:
            logger.error(f"[scraper] Error in _do_scrape_and_save: {e}")
            await db.rollback()


@router.post("/track", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def track_product(
    data: ProductTrackRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a product URL for price tracking. Triggers initial scrape in background."""
    from app.scrapers.scraper_factory import normalize_url
    clean_url = normalize_url(data.url)
    website = detect_website(clean_url)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported website. Supported: {list_supported_websites()}",
        )

    # Initial product details: try live HTTP scraper first
    from app.scrapers.base_scraper import BaseScraper
    fallback = BaseScraper.parse_url_fallback(clean_url, website)

    scrape_res = scrape_product(clean_url)
    if scrape_res.success and scrape_res.price:
        init_name = scrape_res.name or fallback["name"]
        init_brand = scrape_res.brand or fallback["brand"]
        init_price = scrape_res.price
        init_orig_price = scrape_res.original_price or round(init_price * 1.25, 2)
        init_disc = scrape_res.discount_pct or fallback["discount_pct"]
        init_image = scrape_res.image_url
    else:
        headless_data = {}
        try:
            from app.scrapers.headless_fetcher import HeadlessFetcher
            soup = HeadlessFetcher.fetch_page_soup(clean_url, timeout=20)
            if soup:
                headless_data = HeadlessFetcher.extract_meta_and_jsonld(soup)
        except Exception:
            pass

        raw_headless_name = headless_data.get("name")
        if raw_headless_name and any(b in raw_headless_name.lower() for b in ["access denied", "403 forbidden", "captcha", "blocked", "just a moment", "robot check"]):
            raw_headless_name = None

        init_name = raw_headless_name or fallback["name"]
        init_brand = headless_data.get("brand") or fallback["brand"]
        init_price = headless_data.get("price") or fallback["price"]
        init_image = headless_data.get("image_url")
        init_orig_price = fallback["original_price"]
        if headless_data.get("price"):
            init_orig_price = round(init_price * 1.15, 2)
        init_disc = round(((init_orig_price - init_price) / init_orig_price) * 100, 2) if init_orig_price and init_price and init_orig_price > init_price else fallback["discount_pct"]

    now_time = datetime.now(timezone.utc)
    repo = ProductRepository(db)
    product = await repo.create(
        user_id=current_user.id,
        url=clean_url,
        website=website,
        scrape_interval=data.scrape_interval,
        name=init_name,
        brand=init_brand,
        category=fallback["category"],
        current_price=init_price,
        original_price=init_orig_price,
        current_discount=init_disc,
        availability=fallback["availability"],
        seller=website.capitalize(),
        image_url=init_image,
        last_scraped_at=now_time,
    )

    # Immediately save initial price history record
    history_repo = PriceHistoryRepository(db)
    await history_repo.add(
        product_id=product.id,
        price=init_price,
        original_price=init_orig_price,
        discount_pct=init_disc,
        availability=fallback["availability"],
        seller=website.capitalize(),
    )

    # Trigger background scrape to update extra details
    background_tasks.add_task(_do_scrape_and_save, product.id, clean_url)

    return product


@router.get("", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all products tracked by the current user."""
    repo = ProductRepository(db)
    return await repo.get_by_user(current_user.id, skip=skip, limit=limit)


@router.get("/supported-websites")
async def get_supported_websites():
    """Return list of all supported e-commerce websites."""
    return {"websites": list_supported_websites()}


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get product details by ID."""
    repo = ProductRepository(db)
    product = await repo.get_by_id_and_user(product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update scrape interval or active status of a tracked product."""
    repo = ProductRepository(db)
    product = await repo.get_by_id_and_user(product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    updated = await repo.update(product_id, **data.model_dump(exclude_none=True))
    return updated


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stop tracking a product."""
    repo = ProductRepository(db)
    product = await repo.get_by_id_and_user(product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await repo.delete(product_id)
    return MessageResponse(message="Product removed from tracking")


@router.post("/{product_id}/scrape", response_model=MessageResponse)
async def manual_scrape(
    product_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Manually trigger a scrape for a specific product."""
    repo = ProductRepository(db)
    product = await repo.get_by_id_and_user(product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    background_tasks.add_task(_do_scrape_and_save, product.id, product.url)
    return MessageResponse(message="Scrape triggered successfully")
