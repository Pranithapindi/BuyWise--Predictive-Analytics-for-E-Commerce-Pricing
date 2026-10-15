"""
Scraper Factory — detects website from URL and returns the correct scraper.
To add a new website: import its scraper class and add an entry to SCRAPERS.
"""
from urllib.parse import urlparse
from typing import Optional
from loguru import logger

from app.scrapers.base_scraper import BaseScraper, ScrapedProduct
from app.scrapers.amazon import AmazonScraper
from app.scrapers.flipkart import FlipkartScraper
from app.scrapers.myntra import MyntraScraper
from app.scrapers.ajio import AjioScraper
from app.scrapers.reliancedigital import RelianceDigitalScraper
from app.scrapers.croma import CromaScraper
from app.scrapers.snapdeal import SnapdealScraper


# Registry: domain keyword → scraper class
_SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "amazon": AmazonScraper,
    "flipkart": FlipkartScraper,
    "myntra": MyntraScraper,
    "ajio": AjioScraper,
    "reliancedigital": RelianceDigitalScraper,
    "croma": CromaScraper,
    "snapdeal": SnapdealScraper,
}


def normalize_url(url: str) -> str:
    """Ensure URL has a valid http/https scheme."""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url


def detect_website(url: str) -> Optional[str]:
    """Extract the website name from a product URL (handles short links, subdomains, missing schemes)."""
    if not url:
        return None
    url_lower = normalize_url(url).lower()
    
    if "amazon" in url_lower or "amzn" in url_lower:
        return "amazon"
    if "flipkart" in url_lower:
        return "flipkart"
    if "myntra" in url_lower:
        return "myntra"
    if "ajio" in url_lower:
        return "ajio"
    if "reliance" in url_lower:
        return "reliancedigital"
    if "croma" in url_lower:
        return "croma"
    if "snapdeal" in url_lower:
        return "snapdeal"

    return None


def get_scraper(website: str) -> Optional[BaseScraper]:
    """Return an instantiated scraper for the given website name."""
    scraper_cls = _SCRAPER_REGISTRY.get(website)
    if scraper_cls:
        return scraper_cls()
    logger.warning(f"No scraper registered for website: {website}")
    return None


def scrape_product(url: str) -> ScrapedProduct:
    """
    Full pipeline: detect site → get scraper → scrape with retry.
    Returns a ScrapedProduct (check .success for result status).
    """
    website = detect_website(url)
    if not website:
        logger.error(f"Unsupported URL: {url}")
        return ScrapedProduct(url=url, website="unknown", success=False, error="Unsupported website")

    scraper = get_scraper(website)
    if not scraper:
        return ScrapedProduct(url=url, website=website, success=False, error="Scraper not found")

    return scraper.scrape_with_retry(url)


def list_supported_websites() -> list[str]:
    """Return all supported website names."""
    return list(_SCRAPER_REGISTRY.keys())
