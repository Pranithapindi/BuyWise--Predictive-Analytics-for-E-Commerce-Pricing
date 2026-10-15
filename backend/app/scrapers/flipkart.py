"""
Flipkart Scraper
"""
import re
from app.scrapers.base_scraper import BaseScraper, ScrapedProduct


class FlipkartScraper(BaseScraper):
    site_name = "flipkart"
    domains = ["flipkart.com", "www.flipkart.com"]

    def scrape(self, url: str) -> ScrapedProduct:
        result = ScrapedProduct(url=url, website=self.site_name)
        soup = self._fetch(url)
        if not soup:
            result.error = "Failed to fetch page"
            return result

        try:
            # 1. Check JSON-LD Schema tags first (most reliable on Flipkart)
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
                        if not result.brand:
                            b = data.get("brand")
                            if isinstance(b, dict):
                                result.brand = b.get("name")
                            elif isinstance(b, str):
                                result.brand = b
                        offers = data.get("offers", {})
                        if isinstance(offers, list) and offers:
                            offers = offers[0]
                        if isinstance(offers, dict):
                            p = offers.get("price") or offers.get("lowPrice")
                            if p:
                                result.price = float(p)
                except Exception:
                    continue

            # 2. Product name — CSS & OpenGraph & title fallback
            if not result.name:
                name_tag = (
                    soup.find("span", class_="VU-ZEz")
                    or soup.find("h1", class_="_6NK-WV")
                    or soup.find("span", class_="B_NuCI")
                    or soup.find("h1", class_="yhB1nd")
                    or soup.find("h1")
                )
                result.name = self._clean_text(name_tag.get_text()) if name_tag else None

            if not result.name:
                og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
                if og_title and og_title.get("content"):
                    result.name = self._clean_text(re.sub(r"\s*[\|-]\s*Flipkart.*$", "", og_title["content"], flags=re.I))

            if result.name and any(b in result.name.lower() for b in ["access denied", "403 forbidden", "captcha", "blocked", "just a moment", "robot check"]):
                result.name = None

            # 3. Current Price — CSS & OpenGraph fallback
            if not result.price:
                price_tag = (
                    soup.find("div", class_="Nx9bqj _4b5WHp")
                    or soup.find("div", class_="Nx9bqj CxhGGd")
                    or soup.find("div", class_="Nx9bqj")
                    or soup.find("div", class_="_30jeq3 _16Jk6d")
                    or soup.find("div", class_="_30jeq3")
                    or soup.find("div", class_="hl52y2")
                    or soup.find("span", class_="_1vC4OE")
                )
                result.price = self._clean_price(price_tag.get_text()) if price_tag else None

            if not result.price:
                og_price = soup.find("meta", property="og:price:amount") or soup.find("meta", property="product:price:amount")
                if og_price and og_price.get("content"):
                    result.price = self._clean_price(og_price["content"])

            # 4. Original price (strikethrough)
            orig_tag = (
                soup.find("div", class_="yR50cZ")
                or soup.find("div", class_="_3I9_wc _2p6lqe")
                or soup.find("div", class_="_3I9_wc")
                or soup.find("div", class_="_3au_f4")
            )
            result.original_price = self._clean_price(orig_tag.get_text()) if orig_tag else None

            # 5. Discount
            disc_tag = (
                soup.find("div", class_="UkUFwK")
                or soup.find("div", class_="_3Ay6Sb _31Dcoz")
                or soup.find("div", class_="_3Ay6Sb")
            )
            if disc_tag:
                disc_match = re.search(r"(\d+)%", disc_tag.get_text())
                result.discount_pct = float(disc_match.group(1)) if disc_match else None
            elif result.price and result.original_price:
                result.discount_pct = self._calculate_discount(result.price, result.original_price)

            # 6. Rating
            rating_tag = soup.find("div", class_="_3LWZlK") or soup.find("div", class_="XD02Wh")
            if rating_tag:
                try:
                    result.rating = float(rating_tag.get_text().strip())
                except ValueError:
                    pass

            # 7. Image fallback
            if not result.image_url:
                img_tag = (
                    soup.find("img", class_="_396cs4 _2amPTt _3qGmMb")
                    or soup.find("img", class_="q6DClP")
                    or soup.find("img", class_="_2r_T1I")
                    or soup.find("img", class_="DBCP8X")
                )
                if img_tag:
                    result.image_url = img_tag.get("src") or img_tag.get("data-src")

            if not result.image_url:
                og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if og_img and og_img.get("content"):
                    result.image_url = og_img["content"]

            # Seller
            seller_tag = soup.find("div", id="sellerName") or soup.find("span", class_="_2mcZGG")
            result.seller = self._clean_text(seller_tag.get_text()) if seller_tag else "Flipkart"

            # Delivery
            delivery_tag = soup.find("span", class_="c3RnjR")
            if delivery_tag:
                result.delivery_charges = 0.0 if "free" in delivery_tag.get_text().lower() else None

            # Brand & category from breadcrumbs
            breadcrumbs = soup.find_all("a", class_="_2whKao")
            if breadcrumbs:
                result.category = self._clean_text(breadcrumbs[-1].get_text())

            # Brand from specs table
            spec_rows = soup.find_all("tr", class_="_1s_Smc")
            for row in spec_rows:
                key = row.find("td", class_="RmoJze")
                val = row.find("td", class_="WJdYP6")
                if key and val and "brand" in key.get_text().lower():
                    result.brand = self._clean_text(val.get_text())
                    break

            result.success = result.price is not None or result.name is not None

        except Exception as e:
            result.error = f"Parse error: {str(e)}"

        return result
