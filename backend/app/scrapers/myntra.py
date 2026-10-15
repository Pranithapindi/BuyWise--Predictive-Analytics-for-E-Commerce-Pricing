"""
Myntra Scraper — uses JSON-LD and meta tags since Myntra is heavily JS-rendered.
Falls back to static HTML parsing.
"""
import re
import json
from app.scrapers.base_scraper import BaseScraper, ScrapedProduct


class MyntraScraper(BaseScraper):
    site_name = "myntra"
    domains = ["myntra.com", "www.myntra.com"]

    def scrape(self, url: str) -> ScrapedProduct:
        result = ScrapedProduct(url=url, website=self.site_name)
        soup = self._fetch(url)
        if not soup:
            result.error = "Failed to fetch page"
            return result

        try:
            # Try JSON-LD first (most reliable)
            ld_tags = soup.find_all("script", type="application/ld+json")
            for tag in ld_tags:
                try:
                    data = json.loads(tag.string)
                    if isinstance(data, list):
                        data = data[0]
                    if data.get("@type") in ["Product", "IndividualProduct"]:
                        result.name = data.get("name")
                        result.brand = data.get("brand", {}).get("name") if isinstance(data.get("brand"), dict) else data.get("brand")
                        result.image_url = data.get("image", [None])[0] if isinstance(data.get("image"), list) else data.get("image")
                        offers = data.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0]
                        result.price = float(offers.get("price", 0)) or None
                        result.availability = offers.get("availability", "").replace("http://schema.org/", "")
                        agg = data.get("aggregateRating", {})
                        result.rating = float(agg.get("ratingValue", 0)) or None
                        result.review_count = int(agg.get("reviewCount", 0)) or None
                        break
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

            # Fallback: HTML selectors
            if not result.name:
                name_tag = soup.find("h1", class_="pdp-name") or soup.find("h1", class_="pdp-title")
                result.name = self._clean_text(name_tag.get_text()) if name_tag else None

            if not result.price:
                price_tag = soup.find("span", class_="pdp-price") or soup.find("strong", class_="pdp-mrp")
                result.price = self._clean_price(price_tag.get_text()) if price_tag else None

            # Original price
            orig_tag = soup.find("span", class_="pdp-mrp")
            if orig_tag:
                result.original_price = self._clean_price(orig_tag.get_text())

            # Discount
            disc_tag = soup.find("span", class_="pdp-discount")
            if disc_tag:
                disc_match = re.search(r"(\d+)%", disc_tag.get_text())
                result.discount_pct = float(disc_match.group(1)) if disc_match else None
            elif result.price and result.original_price:
                result.discount_pct = self._calculate_discount(result.price, result.original_price)

            if not result.image_url:
                img = soup.find("img", class_="image-grid-image")
                result.image_url = img.get("src") if img else None

            result.seller = "Myntra"
            result.delivery_charges = 0.0  # Myntra typically free above threshold
            result.success = result.price is not None or result.name is not None

        except Exception as e:
            result.error = f"Parse error: {str(e)}"

        return result
