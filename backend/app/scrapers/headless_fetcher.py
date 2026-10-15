"""
Headless Browser Fetcher — uses Selenium Headless Chrome to render JavaScript pages
and bypass CAPTCHA/anti-bot blocks on Amazon, Flipkart, Myntra, etc.
"""
import re
import json
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class HeadlessFetcher:
    """Renders JS web pages via Headless Chrome and returns clean BeautifulSoup + extracted metadata."""

    @staticmethod
    def fetch_page_soup(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
        """Render page in Headless Chrome and return BeautifulSoup DOM."""
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not installed. Skipping headless fetch.")
            return None

        driver = None
        try:
            logger.info(f"🌐 [Selenium] Rendering JS DOM for: {url}")
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(timeout)
            driver.get(url)

            html = driver.page_source
            driver.quit()

            soup = BeautifulSoup(html, "lxml")
            return soup

        except Exception as e:
            logger.warning(f"[Selenium] Headless fetch failed for {url}: {e}")
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            return None

    @staticmethod
    def extract_meta_and_jsonld(soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract title, price, brand, image from OpenGraph and JSON-LD schema tags."""
        result = {}

        if not soup:
            return result

        # 1. Check OpenGraph meta tags
        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if og_title and og_title.get("content"):
            result["name"] = og_title["content"].strip()

        og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if og_image and og_image.get("content"):
            result["image_url"] = og_image["content"].strip()

        og_price = soup.find("meta", property="og:price:amount") or soup.find("meta", property="product:price:amount")
        if og_price and og_price.get("content"):
            try:
                result["price"] = float(re.sub(r"[^\d.]", "", og_price["content"]))
            except ValueError:
                pass

        # 2. Check JSON-LD Schema tags
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, list):
                    data = data[0] if data else {}

                if data.get("@type") in ["Product", "IndividualProduct", "ItemPage"]:
                    if not result.get("name") and data.get("name"):
                        result["name"] = data["name"]

                    if not result.get("image_url"):
                        img = data.get("image")
                        if isinstance(img, list) and img:
                            result["image_url"] = img[0]
                        elif isinstance(img, str):
                            result["image_url"] = img

                    if not result.get("brand"):
                        b = data.get("brand")
                        if isinstance(b, dict):
                            result["brand"] = b.get("name")
                        elif isinstance(b, str):
                            result["brand"] = b

                    offers = data.get("offers", {})
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    if isinstance(offers, dict):
                        p = offers.get("price") or offers.get("lowPrice")
                        if p:
                            try:
                                result["price"] = float(p)
                            except ValueError:
                                pass
            except Exception:
                continue

        # 3. Title tag fallback
        if not result.get("name"):
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                title_str = title_tag.string.strip()
                cleaned_title = re.sub(r"\s*[\|-]\s*(Amazon|Flipkart|Myntra|AJIO|Reliance Digital|Croma|Snapdeal).*$", "", title_str, flags=re.I)
                if len(cleaned_title) > 5 and not any(b in cleaned_title.lower() for b in ["access denied", "403 forbidden", "captcha", "blocked", "just a moment", "robot check"]):
                    result["name"] = cleaned_title
        # 4. Direct HTML selector extraction (Amazon, Flipkart, Myntra, generic)
        if not result.get("price"):
            price_selectors = [
                ("span", {"class_": "a-price-whole"}),
                ("span", {"id": "priceblock_dealprice"}),
                ("span", {"id": "priceblock_ourprice"}),
                ("div", {"class_": "_30jeq3"}),
                ("div", {"class_": "_3I9_wc"}),
                ("span", {"class_": "pdp-price"}),
                ("span", {"class_": "price"}),
                ("span", {"class_": "selling-price"}),
                ("span", {"class_": "new-price"}),
                ("span", {"class_": "pdpPrice"}),
            ]
            for tag_name, attrs in price_selectors:
                el = soup.find(tag_name, **attrs)
                if el:
                    price_text = re.sub(r"[^\d.]", "", el.get_text())
                    if price_text:
                        try:
                            price_val = float(price_text)
                            if price_val > 0:
                                result["price"] = price_val
                                break
                        except ValueError:
                            continue

        if not result.get("name"):
            name_selectors = [
                ("span", {"id": "productTitle"}),
                ("span", {"class_": "B_NuCI"}),
                ("h1", {"class_": "pdp-name"}),
                ("h1", {"class_": "prod-name"}),
                ("h1", {}),
            ]
            for tag_name, attrs in name_selectors:
                el = soup.find(tag_name, **attrs)
                if el:
                    name_text = " ".join(el.get_text().strip().split())
                    if len(name_text) > 3:
                        result["name"] = name_text
                        break

        if not result.get("image_url"):
            img_selectors = [
                ("img", {"id": "landingImage"}),
                ("img", {"class_": "_396cs4"}),
                ("img", {"class_": "image-grid-image"}),
            ]
            for tag_name, attrs in img_selectors:
                el = soup.find(tag_name, **attrs)
                if el:
                    img_url = el.get("data-old-hires") or el.get("src")
                    if img_url and img_url.startswith("http"):
                        result["image_url"] = img_url
                        break

        if not result.get("brand"):
            brand_selectors = [
                ("a", {"id": "bylineInfo"}),
                ("span", {"class_": "G6XhRU"}),
                ("h1", {"class_": "pdp-title"}),
            ]
            for tag_name, attrs in brand_selectors:
                el = soup.find(tag_name, **attrs)
                if el:
                    brand_text = el.get_text().strip()
                    brand_text = re.sub(r"^(Visit the |Brand: )", "", brand_text, flags=re.I).replace(" Store", "").strip()
                    if len(brand_text) > 1:
                        result["brand"] = brand_text
                        break

        return result
