"""
Amazon India Scraper
"""
import re
from typing import Optional
from app.scrapers.base_scraper import BaseScraper, ScrapedProduct


class AmazonScraper(BaseScraper):
    site_name = "amazon"
    domains = ["amazon.in", "www.amazon.in", "amazon.com"]

    def scrape(self, url: str) -> ScrapedProduct:
        result = ScrapedProduct(url=url, website=self.site_name)
        soup = self._fetch(url)
        if not soup:
            result.error = "Failed to fetch page or CAPTCHA detected"
            return result

        try:
            # 1. Check JSON-LD Schema first
            import json
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "{}")
                    if isinstance(data, list) and data:
                        data = data[0]
                    if isinstance(data, dict):
                        if not result.name and data.get("name"):
                            result.name = data["name"]
                        if not result.image_url:
                            img = data.get("image")
                            if isinstance(img, list) and img:
                                result.image_url = img[0]
                            elif isinstance(img, str):
                                result.image_url = img
                        offers = data.get("offers", {})
                        if isinstance(offers, list) and offers:
                            offers = offers[0]
                        if isinstance(offers, dict):
                            p = offers.get("price") or offers.get("lowPrice")
                            if p:
                                result.price = float(p)
                except Exception:
                    continue

            # Product name
            if not result.name:
                name_tag = soup.find("span", id="productTitle")
                result.name = self._clean_text(name_tag.get_text()) if name_tag else None

            # Brand
            brand_tag = soup.find("a", id="bylineInfo")
            if not brand_tag:
                brand_tag = soup.find("span", class_="a-size-base po-break-word")
            result.brand = self._clean_text(brand_tag.get_text().replace("Brand:", "").replace("Visit the", "").replace("Store", "")) if brand_tag else None

            # Current price
            if not result.price:
                price_tag = (
                    soup.find("span", class_="a-price-whole")
                    or soup.find("span", {"id": "priceblock_dealprice"})
                    or soup.find("span", {"id": "priceblock_ourprice"})
                    or soup.find("span", class_="a-color-price")
                )
                result.price = self._clean_price(price_tag.get_text()) if price_tag else None

            if not result.price:
                og_price = soup.find("meta", property="og:price:amount") or soup.find("meta", property="product:price:amount")
                if og_price and og_price.get("content"):
                    result.price = self._clean_price(og_price["content"])

            # Original price (strikethrough)
            orig_tag = soup.find("span", class_="a-price a-text-price")
            if orig_tag:
                orig_whole = orig_tag.find("span", class_="a-offscreen")
                result.original_price = self._clean_price(orig_whole.get_text()) if orig_whole else None

            # Discount
            discount_tag = soup.find("span", class_="savingsPercentage")
            if discount_tag:
                result.discount_pct = self._clean_price(discount_tag.get_text().replace("-", "").replace("%", ""))
            elif result.price and result.original_price:
                result.discount_pct = self._calculate_discount(result.price, result.original_price)

            # Rating
            rating_tag = soup.find("span", class_="a-icon-alt")
            if rating_tag:
                rating_text = rating_tag.get_text()
                rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                if rating_match:
                    result.rating = float(rating_match.group(1))

            # Review count
            review_tag = soup.find("span", id="acrCustomerReviewText")
            if review_tag:
                count_match = re.search(r"[\d,]+", review_tag.get_text())
                if count_match:
                    result.review_count = int(count_match.group().replace(",", ""))

            # Availability
            avail_tag = soup.find("div", id="availability")
            if avail_tag:
                result.availability = self._clean_text(avail_tag.get_text())
            else:
                result.availability = "In Stock" if result.price else "Out of Stock"

            # Image
            img_tag = soup.find("img", id="landingImage") or soup.find("img", id="imgBlkFront")
            if img_tag:
                result.image_url = img_tag.get("data-old-hires") or img_tag.get("src")

            # Seller
            seller_tag = soup.find("a", id="sellerProfileTriggerId")
            result.seller = self._clean_text(seller_tag.get_text()) if seller_tag else "Amazon"

            # Delivery
            delivery_tag = soup.find("span", class_="a-color-success") or soup.find("div", id="deliveryBlockMessage")
            if delivery_tag:
                delivery_text = delivery_tag.get_text().lower()
                result.delivery_charges = 0.0 if "free" in delivery_text else None

            # Category
            breadcrumb = soup.find("div", id="wayfinding-breadcrumbs_feature_div")
            if breadcrumb:
                crumbs = breadcrumb.find_all("a")
                if crumbs:
                    result.category = self._clean_text(crumbs[-1].get_text())

            result.success = result.price is not None or result.name is not None

        except Exception as e:
            result.error = f"Parse error: {str(e)}"

        return result
