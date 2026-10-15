"""
Croma Scraper
"""
import re
import json
from app.scrapers.base_scraper import BaseScraper, ScrapedProduct


class CromaScraper(BaseScraper):
    site_name = "croma"
    domains = ["croma.com", "www.croma.com"]

    def scrape(self, url: str) -> ScrapedProduct:
        result = ScrapedProduct(url=url, website=self.site_name)
        soup = self._fetch(url)
        if not soup:
            result.error = "Failed to fetch page"
            return result

        try:
            # JSON-LD
            ld_tags = soup.find_all("script", type="application/ld+json")
            for tag in ld_tags:
                try:
                    data = json.loads(tag.string)
                    if isinstance(data, list):
                        data = data[0]
                    if data.get("@type") == "Product":
                        result.name = data.get("name")
                        result.brand = data.get("brand", {}).get("name") if isinstance(data.get("brand"), dict) else None
                        result.image_url = data.get("image")
                        offers = data.get("offers", {})
                        result.price = float(offers.get("price", 0)) or None
                        break
                except Exception:
                    continue

            if not result.name:
                name_tag = soup.find("h1", class_="pdpProductTitle")
                result.name = self._clean_text(name_tag.get_text()) if name_tag else None

            if not result.price:
                price_tag = soup.find("span", class_="pdpPrice")
                result.price = self._clean_price(price_tag.get_text()) if price_tag else None

            orig_tag = soup.find("span", class_="pdpMrpPrice")
            result.original_price = self._clean_price(orig_tag.get_text()) if orig_tag else None

            if result.price and result.original_price:
                result.discount_pct = self._calculate_discount(result.price, result.original_price)

            rating_tag = soup.find("span", class_="ratingCount")
            if rating_tag:
                try:
                    result.rating = float(rating_tag.get_text().strip())
                except ValueError:
                    pass

            result.seller = "Croma"
            result.availability = "In Stock" if result.price else "Out of Stock"
            result.success = result.price is not None or result.name is not None

        except Exception as e:
            result.error = f"Parse error: {str(e)}"

        return result
