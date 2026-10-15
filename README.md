# 🛒 Product Price Scraping & Analysis

> **AI-powered price intelligence platform** — track prices from 7 major Indian e-commerce sites, get ML-predicted price trends, receive smart alerts, and know the perfect time to buy.

![Tech Stack](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18.3-61dafb?style=flat-square&logo=react)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ **Multi-site Scraping** | Amazon, Flipkart, Myntra, AJIO, Reliance Digital, Croma, Snapdeal |
| 📊 **Price Analytics** | Mean, Median, Std Dev, Moving Average, Outliers, Trends |
| 🤖 **ML Predictions** | Linear Regression + Random Forest + XGBoost with MAE/RMSE/R² |
| 💡 **AI Recommendations** | Buy Now / Wait with confidence scores and explanations |
| 🔔 **Smart Alerts** | Email + Browser notifications on price drops |
| ⏰ **Auto Scheduling** | 30 min / 1h / 6h / daily APScheduler jobs |
| 📤 **Export** | CSV, Excel (styled), PDF with charts |
| 🔐 **JWT Auth** | Register, Login, Role-based (Admin/User) |
| 🌙 **Dark Mode** | Full dark/light toggle |
| 🐳 **Docker** | One-command deployment with Docker Compose |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         React 18 + Vite + Tailwind CSS       │
│  Dashboard · Products · Analytics · Alerts   │
└──────────────────┬──────────────────────────┘
                   │ REST API / Axios
┌──────────────────▼──────────────────────────┐
│           FastAPI (Python 3.11)              │
│  Auth · Products · Analytics · ML · Admin   │
└──┬─────────────┬──────────────┬─────────────┘
   │             │              │
┌──▼──┐    ┌────▼────┐   ┌─────▼──────────┐
│ PG  │    │  Redis  │   │  APScheduler   │
│ DB  │    │  Cache  │   │  (4 intervals) │
└─────┘    └─────────┘   └────────────────┘
```

---

## 📁 Project Structure

```
product-price-tracker/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (auth, products, analytics, ml, alerts, search, export, admin)
│   │   ├── core/          # Config, security (JWT/bcrypt), dependencies (DI)
│   │   ├── database/      # SQLAlchemy models, Pydantic schemas, repositories
│   │   ├── scrapers/      # BaseScraper + 7 site implementations + factory
│   │   ├── analytics/     # Statistical analysis engine
│   │   ├── ml/            # ML pipeline (LR/RF/XGBoost) + AI recommender
│   │   ├── scheduler/     # APScheduler jobs
│   │   ├── services/      # Email service
│   │   └── utils/
│   ├── tests/             # pytest test suite
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/    # Layout, Sidebar, Navbar, ProductCard, Charts
│   │   ├── pages/         # Dashboard, Products, ProductDetail, Analytics, Alerts, Search, Profile, Admin
│   │   ├── context/       # AuthContext, ThemeContext
│   │   ├── services/      # Axios API client
│   │   └── utils/         # Formatters
│   ├── index.html
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone/enter the project
cd product-price-tracker

# 2. Copy environment file
cp .env.example .env
# Edit .env with your database password and SMTP credentials

# 3. Start everything
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Local Development

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env: set DATABASE_URL to your local PostgreSQL

# Start PostgreSQL and Redis locally, then:
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## 📚 API Documentation

Interactive Swagger UI available at: **http://localhost:8000/api/docs**

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| POST | `/api/v1/products/track` | Add product URL |
| GET | `/api/v1/products` | List tracked products |
| GET | `/api/v1/analytics/{id}/summary` | Price summary stats |
| GET | `/api/v1/analytics/{id}/stats` | Full statistical analysis |
| GET | `/api/v1/analytics/{id}/trends` | Weekly/monthly trends |
| GET | `/api/v1/ml/{id}/predict` | ML price predictions |
| GET | `/api/v1/ml/{id}/recommendation` | AI buy/wait advice |
| GET | `/api/v1/export/{id}?format=csv` | Export price history |
| POST | `/api/v1/alerts` | Create price alert |
| GET | `/api/v1/search?q=laptop&website=amazon` | Search products |
| GET | `/api/v1/admin/stats` | Admin dashboard stats |

---

## 🕷️ Scraper Architecture

Adding a new website requires **only one new file**:

```python
# backend/app/scrapers/newsite.py
from app.scrapers.base_scraper import BaseScraper, ScrapedProduct

class NewSiteScraper(BaseScraper):
    site_name = "newsite"
    domains = ["newsite.com", "www.newsite.com"]

    def scrape(self, url: str) -> ScrapedProduct:
        result = ScrapedProduct(url=url, website=self.site_name)
        soup = self._fetch(url)
        # ... parse your fields ...
        result.success = True
        return result
```

Then register in `scraper_factory.py`:
```python
from app.scrapers.newsite import NewSiteScraper
_SCRAPER_REGISTRY["newsite"] = NewSiteScraper
```

---

## 🤖 ML Pipeline

```
Price History → Feature Engineering → Train 3 Models → Compare → Best Model → Predict
     ↑                                                                            ↓
  DB store ←────────────────── APScheduler scrape ──────────────────────── Recommendation
```

**Features engineered:** day_of_week, month, day_of_year, week_of_year, lag_1, lag_7, lag_30, rolling_mean_7/30, rolling_std_7

**Models:** Linear Regression · Random Forest · XGBoost  
**Metrics:** MAE · RMSE · R²

---

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `users` | Auth & profile |
| `products` | Tracked product URLs |
| `price_history` | Every scraped price with timestamp |
| `alerts` | User-configured price alerts |
| `scrape_logs` | Success/failure/captcha logs |
| `wishlist` | User favorites |

---

## 🧪 Running Tests

```bash
cd backend
pip install pytest pytest-asyncio aiosqlite
pytest tests/ -v
```

---

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | React app (nginx) |
| `backend` | 8000 | FastAPI server |
| `db` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 cache |

---

## 🔑 Environment Variables

See [`.env.example`](.env.example) for all required variables.

Critical variables:
- `SECRET_KEY` — JWT signing secret (change in production!)
- `DATABASE_URL` — PostgreSQL connection string
- `SMTP_USER` / `SMTP_PASSWORD` — Gmail app password for alerts

---

## 📊 Supported Websites

| Website | Status | Notes |
|---------|--------|-------|
| Amazon India | ✅ | BeautifulSoup |
| Flipkart | ✅ | BeautifulSoup |
| Myntra | ✅ | JSON-LD + HTML |
| AJIO | ✅ | JSON-LD + HTML |
| Reliance Digital | ✅ | JSON-LD + HTML |
| Croma | ✅ | JSON-LD + HTML |
| Snapdeal | ✅ | JSON-LD + HTML |

> ⚠️ Real e-commerce sites actively fight bots. Scrapers use realistic headers, random delays, and retry logic. Results may vary depending on site's anti-bot measures.

---

## 📝 License

MIT License. Built for educational purposes.
