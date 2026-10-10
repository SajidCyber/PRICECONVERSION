"""FakeStore Public API Catalog Adapter."""

from decimal import Decimal
from typing import List, Optional
from app.core.exceptions import ScrapingError
from app.core.logging_config import logger
from app.schemas.scraper import ExtractedProductDTO
from app.services.scraper.base_adapter import BaseScraperAdapter


class FakeStoreAdapter(BaseScraperAdapter):
    """Adapter for ingesting public product data from FakeStoreAPI."""

    def __init__(self):
        super().__init__(
            marketplace_id="fakestore",
            base_url="https://fakestoreapi.com",
            default_currency="USD",
        )

    @property
    def adapter_name(self) -> str:
        return "fakestore"

    @property
    def is_live_scraper(self) -> bool:
        return False

    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        max_items: int = 20,
        custom_url: Optional[str] = None,
    ) -> List[ExtractedProductDTO]:
        """Pulls structured products from FakeStore API."""
        if custom_url:
            url = custom_url
        elif category:
            url = f"{self.base_url}/products/category/{category}?limit={max_items}"
        else:
            url = f"{self.base_url}/products?limit={max_items}"

        logger.info("Fetching FakeStore products from: %s", url)
        try:
            response = await self.http_client.get(url)
            if response.status_code != 200:
                raise ScrapingError(f"FakeStore API returned HTTP {response.status_code}")
            data = response.json()
        except Exception as e:
            raise ScrapingError(f"Failed to fetch FakeStore feed: {str(e)}")

        products_list = data if isinstance(data, list) else []
        return self.parse_fakestore_products(products_list)

    def parse_fakestore_products(self, products: list) -> List[ExtractedProductDTO]:
        """Maps FakeStore items to ExtractedProductDTO."""
        extracted = []
        for item in products:
            try:
                numeric_price = Decimal(str(item.get("price", 0)))
                if numeric_price <= 0:
                    continue

                rating_data = item.get("rating", {})
                rating_val = Decimal(str(rating_data.get("rate", 0))) if isinstance(rating_data, dict) else None
                review_cnt = rating_data.get("count", 100) if isinstance(rating_data, dict) else 100

                dto = ExtractedProductDTO(
                    external_id=f"FAKESTORE-{item.get('id')}",
                    title=item.get("title", "Untitled Product"),
                    url=f"https://fakestoreapi.com/products/{item.get('id')}",
                    price=numeric_price,
                    currency_code="USD",
                    shipping_price=Decimal("0.00"),
                    discount_pct=Decimal("0.00"),
                    availability_status="in_stock",
                    rating=rating_val,
                    review_count=review_cnt,
                    brand="FakeStore Direct",
                    category=item.get("category", "General").capitalize(),
                    image_url=item.get("image"),
                    data_provenance="demo_api",
                    raw_snippet=f"FakeStore id={item.get('id')} price=${numeric_price}",
                )
                extracted.append(dto)
            except Exception as e:
                logger.warning("Failed to parse FakeStore product item: %s", str(e))
                continue
        return extracted
