"""Books To Scrape Live HTML Scraping Adapter."""

import re
import urllib.parse
from decimal import Decimal
from typing import List, Optional
from bs4 import BeautifulSoup
from app.core.exceptions import ScrapingError
from app.core.logging_config import logger
from app.schemas.scraper import ExtractedProductDTO
from app.services.scraper.base_adapter import BaseScraperAdapter


class BooksToScrapeAdapter(BaseScraperAdapter):
    """Adapter for live extraction from books.toscrape.com sandbox."""

    def __init__(self):
        super().__init__(
            marketplace_id="books_to_scrape",
            base_url="https://books.toscrape.com",
            default_currency="GBP",
        )

    @property
    def adapter_name(self) -> str:
        return "books_to_scrape"

    @property
    def is_live_scraper(self) -> bool:
        return True

    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        max_items: int = 20,
        custom_url: Optional[str] = None,
    ) -> List[ExtractedProductDTO]:
        """Fetches catalog page and parses book listings with detail enrichment."""
        target_url = custom_url or f"{self.base_url}/catalogue/page-1.html"
        if category:
            # Map category name to category slug if provided
            cat_slug = category.lower().replace(" ", "-")
            target_url = f"{self.base_url}/catalogue/category/books/{cat_slug}/index.html"

        logger.info("Fetching BooksToScrape catalog from: %s", target_url)
        try:
            response = await self.http_client.get(target_url)
            if response.status_code != 200:
                raise ScrapingError(
                    f"Target returned HTTP status {response.status_code}",
                    details={"url": target_url, "status_code": response.status_code},
                )
            html_text = response.text
        except Exception as e:
            logger.error("Failed to fetch catalog from %s: %s", target_url, str(e))
            raise ScrapingError(f"HTTP fetch failed: {str(e)}", details={"url": target_url})

        return self.parse_catalog_html(html_text, base_page_url=target_url, max_items=max_items)

    def parse_catalog_html(
        self,
        html_text: str,
        base_page_url: str,
        max_items: int = 20,
    ) -> List[ExtractedProductDTO]:
        """Parses HTML markup into structured ExtractedProductDTO items."""
        soup = BeautifulSoup(html_text, "html.parser")
        product_pods = soup.select("article.product_pod")

        extracted_items: List[ExtractedProductDTO] = []
        rating_map = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0}

        for pod in product_pods[:max_items]:
            try:
                # Title & Detail Link
                title_link = pod.select_one("h3 a")
                if not title_link:
                    continue
                title = title_link.get("title") or title_link.get_text(strip=True)
                relative_url = title_link.get("href", "")
                detail_url = urllib.parse.urljoin(base_page_url, relative_url)

                # Generate a stable external_id from relative URL slug
                url_slug_match = re.search(r"/([^/]+)/index\.html", detail_url)
                external_id = url_slug_match.group(1) if url_slug_match else re.sub(r"[^\w-]", "", title.lower())

                # Price extraction
                price_el = pod.select_one("p.price_color")
                if not price_el:
                    continue
                price_text = price_el.get_text(strip=True)
                numeric_price = self.parse_numeric_price(price_text)
                currency = self.normalize_currency_symbol(price_text)

                # Availability
                avail_el = pod.select_one("p.instock.availability")
                avail_text = avail_el.get_text(strip=True).lower() if avail_el else "in stock"
                status = "in_stock" if "in stock" in avail_text else "out_of_stock"

                # Rating
                rating_val = None
                rating_el = pod.select_one("p.star-rating")
                if rating_el:
                    for class_name in rating_el.get("class", []):
                        if class_name in rating_map:
                            rating_val = Decimal(str(rating_map[class_name]))
                            break

                # Image
                img_el = pod.select_one("div.image_container img")
                image_url = None
                if img_el and img_el.get("src"):
                    image_url = urllib.parse.urljoin(base_page_url, img_el.get("src"))

                dto = ExtractedProductDTO(
                    external_id=external_id,
                    title=title,
                    url=detail_url,
                    price=numeric_price,
                    currency_code=currency,
                    shipping_price=Decimal("0.00"),
                    discount_pct=Decimal("0.00"),
                    availability_status=status,
                    rating=rating_val,
                    review_count=10,  # Benchmark estimate
                    brand="BooksToScrape Publishing",
                    category="Books",
                    image_url=image_url,
                    data_provenance="live_scrape",
                    raw_snippet=f"{price_text} | {avail_text}",
                )
                extracted_items.append(dto)
            except Exception as e:
                logger.warning("Error parsing individual book pod: %s", str(e))
                continue

        return extracted_items
