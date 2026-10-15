"""
SQLAlchemy ORM Models — Users, Products, PriceHistory, Alerts, ScrapeLogs, Wishlist
"""
import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Text, Boolean, Integer, Numeric, DateTime,
    ForeignKey, Enum as SAEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow():
    return datetime.now(timezone.utc)


# ─── Enums ────────────────────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class ScrapeStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    CAPTCHA = "captcha"
    UNAVAILABLE = "unavailable"


class ScrapeInterval(int, enum.Enum):
    THIRTY_MIN = 30
    ONE_HOUR = 60
    SIX_HOURS = 360
    DAILY = 1440


# ─── User ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    products: Mapped[List["Product"]] = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    wishlist: Mapped[List["Wishlist"]] = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")


# ─── Product ──────────────────────────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[str] = mapped_column(String(50), nullable=False)  # amazon, flipkart, etc.
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    original_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    current_discount: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    current_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    availability: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    seller: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_charges: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    scrape_interval: Mapped[int] = mapped_column(Integer, default=60)  # minutes
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="products")
    price_history: Mapped[List["PriceHistory"]] = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="product", cascade="all, delete-orphan")
    scrape_logs: Mapped[List["ScrapeLog"]] = relationship("ScrapeLog", back_populates="product", cascade="all, delete-orphan")
    wishlist: Mapped[List["Wishlist"]] = relationship("Wishlist", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_products_user_id", "user_id"),
        Index("ix_products_website", "website"),
    )


# ─── PriceHistory ─────────────────────────────────────────────────────────────
class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    original_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    discount_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    availability: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    seller: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_charges: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    # Relationship
    product: Mapped["Product"] = relationship("Product", back_populates="price_history")

    __table_args__ = (
        Index("ix_ph_product_id_scraped_at", "product_id", "scraped_at"),
    )


# ─── Alert ────────────────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    target_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    target_discount: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    max_budget: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_browser: Mapped[bool] = mapped_column(Boolean, default=True)
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    product: Mapped["Product"] = relationship("Product", back_populates="alerts")


# ─── ScrapeLog ────────────────────────────────────────────────────────────────
class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ScrapeStatus] = mapped_column(SAEnum(ScrapeStatus), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationship
    product: Mapped["Product"] = relationship("Product", back_populates="scrape_logs")


# ─── Wishlist ─────────────────────────────────────────────────────────────────
class Wishlist(Base):
    __tablename__ = "wishlist"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wishlist")
    product: Mapped["Product"] = relationship("Product", back_populates="wishlist")
