"""
Seed Script — populates database with 5 popular products and 30 days of realistic
historical price data, stats, alerts, and trains ML prediction models for immediate demo visibility!
"""
import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta

from app.database.session import AsyncSessionLocal, engine, Base
from app.database.models import User, Product, PriceHistory, Alert, ScrapeLog, ScrapeStatus, UserRole
from app.core.security import hash_password
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.product_repo import ProductRepository
from app.database.repositories.price_history_repo import PriceHistoryRepository
from app.ml.pipeline import PricePredictor

DEMO_PRODUCTS = [
    {
        "url": "https://www.amazon.in/dp/B0CHX1W1XY",
        "website": "amazon",
        "name": "Apple iPhone 15 (128 GB) - Blue",
        "brand": "Apple",
        "category": "Electronics",
        "image_url": "https://m.media-amazon.com/images/I/71d7rfSl0wL._SL1500_.jpg",
        "start_price": 79900.0,
        "end_price": 71990.0,
        "original_price": 79900.0,
        "rating": 4.6,
        "review_count": 14250,
        "seller": "Appario Retail Private Ltd",
    },
    {
        "url": "https://www.flipkart.com/apple-macbook-air-m2-8gb-256gb-ssd/p/itm12345",
        "website": "flipkart",
        "name": "Apple MacBook Air M2 (8GB / 256GB SSD) - Starlight",
        "brand": "Apple",
        "category": "Laptops",
        "image_url": "https://m.media-amazon.com/images/I/71f5Eu5lJSL._SL1500_.jpg",
        "start_price": 114900.0,
        "end_price": 94990.0,
        "original_price": 119900.0,
        "rating": 4.7,
        "review_count": 8920,
        "seller": "SuperComNet",
    },
    {
        "url": "https://www.amazon.in/dp/B0863TXGM3",
        "website": "amazon",
        "name": "Sony WH-1000XM4 Wireless Noise Cancelling Headphones",
        "brand": "Sony",
        "category": "Audio",
        "image_url": "https://m.media-amazon.com/images/I/61D4Z3yKPAL._SL1500_.jpg",
        "start_price": 29990.0,
        "end_price": 22990.0,
        "original_price": 29990.0,
        "rating": 4.5,
        "review_count": 32100,
        "seller": "Amazon Retail",
    },
    {
        "url": "https://www.myntra.com/shoes/nike/nike-air-max-270/123456",
        "website": "myntra",
        "name": "Nike Air Max 270 Running Shoes for Men",
        "brand": "Nike",
        "category": "Footwear",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800",
        "start_price": 11995.0,
        "end_price": 13995.0,
        "original_price": 14995.0,
        "rating": 4.3,
        "review_count": 4520,
        "seller": "Nike India",
    },
    {
        "url": "https://www.reliancedigital.in/samsung-galaxy-s24-ultra/p/49435123",
        "website": "reliancedigital",
        "name": "Samsung Galaxy S24 Ultra 5G (12GB RAM, 256GB)",
        "brand": "Samsung",
        "category": "Smartphones",
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800",
        "start_price": 134999.0,
        "end_price": 124999.0,
        "original_price": 134999.0,
        "rating": 4.8,
        "review_count": 5100,
        "seller": "Reliance Digital",
    },
]

async def seed_data():
    print("Starting database seeding...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        
        # 1. Create Demo Admin User if not exists
        admin = await user_repo.get_by_email("admin@demo.com")
        if not admin:
            admin = await user_repo.create("admin@demo.com", "AdminUser", "admin123", role="admin")
            print("Created demo admin user: admin@demo.com / admin123")

        # 2. Create Regular User if not exists
        user = await user_repo.get_by_email("user@test.com")
        if not user:
            user = await user_repo.create("user@test.com", "testuser", "password123", role="user")
            print("Created test user: user@test.com / password123")

        target_user = admin

        # 3. Add products and 30-day price history
        now = datetime.now(timezone.utc)

        for p_data in DEMO_PRODUCTS:
            product = Product(
                user_id=target_user.id,
                url=p_data["url"],
                website=p_data["website"],
                name=p_data["name"],
                brand=p_data["brand"],
                category=p_data["category"],
                image_url=p_data["image_url"],
                current_price=p_data["end_price"],
                original_price=p_data["original_price"],
                current_discount=round(((p_data["original_price"] - p_data["end_price"]) / p_data["original_price"]) * 100, 2),
                current_rating=p_data["rating"],
                review_count=p_data["review_count"],
                availability="In Stock",
                seller=p_data["seller"],
                delivery_charges=0.0,
                scrape_interval=60,
                is_active=True,
                last_scraped_at=now,
            )
            db.add(product)
            await db.flush()

            print(f"Created product: {product.name}")

            # Generate 30 days of price history points
            start_price = p_data["start_price"]
            end_price = p_data["end_price"]

            for day in range(30, -1, -1):
                timestamp = now - timedelta(days=day)
                progress = (30 - day) / 30.0
                interpolated = start_price + (end_price - start_price) * progress
                noise = random.uniform(-0.015, 0.015)
                daily_price = round(interpolated * (1 + noise), 2)
                disc = round(((p_data["original_price"] - daily_price) / p_data["original_price"]) * 100, 2)

                ph = PriceHistory(
                    product_id=product.id,
                    price=daily_price,
                    original_price=p_data["original_price"],
                    discount_pct=disc,
                    rating=p_data["rating"],
                    review_count=p_data["review_count"] - day * 10,
                    availability="In Stock",
                    seller=p_data["seller"],
                    delivery_charges=0.0,
                    scraped_at=timestamp,
                )
                db.add(ph)

                log = ScrapeLog(
                    product_id=product.id,
                    status=ScrapeStatus.SUCCESS,
                    response_time_ms=random.randint(450, 1200),
                    scraped_at=timestamp,
                )
                db.add(log)

            target_p = round(end_price * 0.95, 2)
            alert = Alert(
                user_id=target_user.id,
                product_id=product.id,
                target_price=target_p,
                notify_email=True,
                notify_browser=True,
                is_active=True,
            )
            db.add(alert)

            await db.flush()

            # 4. Train ML model for product
            history_repo = PriceHistoryRepository(db)
            series = await history_repo.get_prices_as_series(product.id)
            if len(series) >= 5:
                predictor = PricePredictor(product.id)
                predictor.train_and_evaluate(series)
                print(f"Trained ML models for {product.name[:30]}...")

        await db.commit()
        print("Seeding complete! 5 products, 150+ price records, alerts, and ML models created.")

if __name__ == "__main__":
    asyncio.run(seed_data())
