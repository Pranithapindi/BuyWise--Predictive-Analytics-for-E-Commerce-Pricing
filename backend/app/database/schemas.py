"""
Pydantic Schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, HttpUrl, field_validator
from app.database.models import UserRole, ScrapeStatus


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class ProductTrackRequest(BaseModel):
    url: str
    scrape_interval: int = 60  # minutes: 30, 60, 360, 1440

    @field_validator("scrape_interval")
    @classmethod
    def valid_interval(cls, v: int) -> int:
        allowed = [30, 60, 360, 1440]
        if v not in allowed:
            raise ValueError(f"scrape_interval must be one of {allowed}")
        return v


class ProductUpdate(BaseModel):
    scrape_interval: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: str
    user_id: str
    url: str
    website: str
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    current_discount: Optional[float] = None
    current_rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    delivery_charges: Optional[float] = None
    scrape_interval: int
    is_active: bool
    last_scraped_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# PRICE HISTORY SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class PriceHistoryResponse(BaseModel):
    id: str
    product_id: str
    price: float
    original_price: Optional[float] = None
    discount_pct: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    delivery_charges: Optional[float] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class PriceSummaryResponse(BaseModel):
    product_id: str
    current_price: Optional[float]
    highest_price: Optional[float]
    lowest_price: Optional[float]
    average_price: Optional[float]
    median_price: Optional[float]
    price_drop_pct: Optional[float]
    price_increase_pct: Optional[float]
    volatility: Optional[float]
    total_data_points: int


class PriceStatsResponse(BaseModel):
    mean: float
    median: float
    mode: Optional[float]
    std_dev: float
    variance: float
    moving_average_7d: Optional[float]
    rolling_mean_30d: Optional[float]
    outliers: List[float]


class TrendResponse(BaseModel):
    weekly_trend: str   # "up", "down", "stable"
    monthly_trend: str
    seasonal_trend: Optional[str]
    festival_comparison: Optional[dict]


# ═══════════════════════════════════════════════════════════════════════════════
# ML SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class MLPredictionResponse(BaseModel):
    product_id: str
    model_comparison: dict       # {model_name: {mae, rmse, r2}}
    best_model: str
    next_7_days: List[dict]      # [{date, predicted_price}]
    next_30_days: List[dict]
    expected_best_buy_date: Optional[str]
    prediction_graph_data: dict


class RecommendationResponse(BaseModel):
    product_id: str
    recommendation: str          # "BUY_NOW", "WAIT", "PRICE_LIKELY_DECREASE", "PRICE_LIKELY_INCREASE"
    confidence: float            # 0.0 - 1.0
    reason: str
    best_time_to_buy: Optional[str]
    expected_price: Optional[float]


# ═══════════════════════════════════════════════════════════════════════════════
# ALERT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class AlertCreate(BaseModel):
    product_id: str
    target_price: Optional[float] = None
    target_discount: Optional[float] = None
    max_budget: Optional[float] = None
    notify_email: bool = True
    notify_sms: bool = False
    notify_browser: bool = True


class AlertUpdate(BaseModel):
    target_price: Optional[float] = None
    target_discount: Optional[float] = None
    max_budget: Optional[float] = None
    notify_email: Optional[bool] = None
    notify_sms: Optional[bool] = None
    notify_browser: Optional[bool] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    target_price: Optional[float] = None
    target_discount: Optional[float] = None
    max_budget: Optional[float] = None
    notify_email: bool
    notify_sms: bool
    notify_browser: bool
    is_triggered: bool
    triggered_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPE LOG SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class ScrapeLogResponse(BaseModel):
    id: str
    product_id: str
    status: ScrapeStatus
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class SearchFilters(BaseModel):
    q: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    min_discount: Optional[float] = None
    page: int = 1
    page_size: int = 20


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════
class AdminStatsResponse(BaseModel):
    total_users: int
    total_products: int
    total_scrapes_today: int
    failed_scrapes_today: int
    most_tracked_products: List[dict]
    website_statistics: dict


# ═══════════════════════════════════════════════════════════════════════════════
# GENERIC
# ═══════════════════════════════════════════════════════════════════════════════
class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
