"""
Scraper Unit Tests.
"""
import pytest
from app.scrapers.scraper_factory import detect_website, list_supported_websites


def test_detect_amazon():
    assert detect_website("https://www.amazon.in/dp/B08L5TNJHG") == "amazon"


def test_detect_flipkart():
    assert detect_website("https://www.flipkart.com/product/p/item") == "flipkart"


def test_detect_myntra():
    assert detect_website("https://www.myntra.com/shoes/12345") == "myntra"


def test_detect_ajio():
    assert detect_website("https://www.ajio.com/product/RS12345") == "ajio"


def test_detect_snapdeal():
    assert detect_website("https://www.snapdeal.com/product/item") == "snapdeal"


def test_detect_unknown():
    assert detect_website("https://www.example.com/product") is None


def test_detect_invalid_url():
    assert detect_website("not-a-url") is None


def test_supported_websites():
    sites = list_supported_websites()
    assert "amazon" in sites
    assert "flipkart" in sites
    assert "myntra" in sites
    assert len(sites) == 7


def test_clean_price():
    from app.scrapers.base_scraper import BaseScraper
    assert BaseScraper._clean_price("₹1,23,456.00") == 123456.0
    assert BaseScraper._clean_price("₹999") == 999.0
    assert BaseScraper._clean_price(None) is None
    assert BaseScraper._clean_price("") is None


def test_calculate_discount():
    from app.scrapers.base_scraper import BaseScraper
    assert BaseScraper._calculate_discount(800, 1000) == 20.0
    assert BaseScraper._calculate_discount(1000, 1000) is None
    assert BaseScraper._calculate_discount(None, 1000) is None
