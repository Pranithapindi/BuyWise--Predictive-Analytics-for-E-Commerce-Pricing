"""
Product Price Tracker - FastAPI Main Entry Point
"""
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.database.session import engine, Base
from app.api import auth, products, analytics, alerts, admin, search, export, ml
from app.scheduler.jobs import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("🚀 Starting Product Price Tracker API...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created/verified")

    # Seed demo admin user if not exists
    from app.database.session import AsyncSessionLocal
    from app.database.repositories.user_repo import UserRepository
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        existing = await user_repo.get_by_email("admin@demo.com")
        if not existing:
            await user_repo.create("admin@demo.com", "AdminUser", "admin123", role="admin")
            await db.commit()
            logger.info("👤 Seeded demo admin user: admin@demo.com / admin123")

    # Start scheduler
    scheduler.start()
    logger.info("✅ APScheduler started")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("🛑 Scheduler stopped")
    logger.info("🛑 Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Product Price Scraping, Analysis & Prediction Platform",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router,     prefix=f"{API_PREFIX}/auth",     tags=["Authentication"])
app.include_router(products.router, prefix=f"{API_PREFIX}/products",  tags=["Products"])
app.include_router(analytics.router,prefix=f"{API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(ml.router,       prefix=f"{API_PREFIX}/ml",        tags=["Machine Learning"])
app.include_router(alerts.router,   prefix=f"{API_PREFIX}/alerts",    tags=["Alerts"])
app.include_router(search.router,   prefix=f"{API_PREFIX}/search",    tags=["Search"])
app.include_router(export.router,   prefix=f"{API_PREFIX}/export",    tags=["Export"])
app.include_router(admin.router,    prefix=f"{API_PREFIX}/admin",     tags=["Admin"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Product Price Tracker API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
