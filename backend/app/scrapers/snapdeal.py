"""
Snapdeal Scraper
"""
import re
import json
from app.scrapers.base_scraper import BaseScraper, ScrapedProduct


class SnapdealScraper(BaseScraper):
    site_name = "snapdeal"
    domains = ["snapdeal.com", "www.snapdeal.com"]

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
                        agg = data.get("aggregateRating", {})
                        result.rating = float(agg.get("ratingValue", 0)) or None
                        result.review_count = int(agg.get("reviewCount", 0)) or None
                        break
                except Exception:
                    continue

            if not result.name:
                name_tag = soup.find("h1", attrs={"itemprop": "name"})
                result.name = self._clean_text(name_tag.get_text()) if name_tag else None

            if not result.price:
                price_tag = soup.find("span", id="selling-price-id") or soup.find("span", class_="payBlkBig")
                result.price = self._clean_price(price_tag.get_text()) if price_tag else None

            orig_tag = soup.find("span", class_="seeAllMrpPrice") or soup.find("span", id="mrp-price-id")
            result.original_price = self._clean_price(orig_tag.get_text()) if orig_tag else None

            disc_tag = soup.find("div", class_="discount-percent")
            if disc_tag:
                disc_match = re.search(r"(\d+)%", disc_tag.get_text())
                result.discount_pct = float(disc_match.group(1)) if disc_match else None
            elif result.price and result.original_price:
                result.discount_pct = self._calculate_discount(result.price, result.original_price)

            if not result.image_url:
                img_tag = soup.find("img", id="product-image-main")
                result.image_url = img_tag.get("src") if img_tag else None

            result.seller = "Snapdeal"
            result.availability = "In Stock" if result.price else "Out of Stock"
            result.success = result.price is not None or result.name is not None

        except Exception as e:
            result.error = f"Parse error: {str(e)}"

        return result
