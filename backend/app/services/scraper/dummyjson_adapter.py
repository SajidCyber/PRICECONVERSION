"""DummyJSON Public Catalog Feed Adapter."""

from decimal import Decimal
from typing import List, Optional
from app.core.exceptions import ScrapingError
from app.core.logging_config import logger
from app.schemas.scraper import ExtractedProductDTO
from app.services.scraper.base_adapter import BaseScraperAdapter


class DummyJsonAdapter(BaseScraperAdapter):
    """Adapter for ingesting public structured product data from DummyJSON API."""

    def __init__(self):
        super().__init__(
            marketplace_id="dummyjson_store",
            base_url="https://dummyjson.com",
            default_currency="USD",
        )

    @property
    def adapter_name(self) -> str:
        return "dummyjson"

    @property
    def is_live_scraper(self) -> bool:
        return False  # Structured API feed

    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        max_items: int = 20,
        custom_url: Optional[str] = None,
    ) -> List[ExtractedProductDTO]:
        """Pulls structured products from DummyJSON API."""
        if custom_url:
            url = custom_url
        elif category:
            url = f"{self.base_url}/products/category/{category}?limit={max_items}"
        else:
            url = f"{self.base_url}/products?limit={max_items}"

        logger.info("Fetching DummyJSON products from: %s", url)
        try:
            response = await self.http_client.get(url)
            if response.status_code != 200:
                raise ScrapingError(f"DummyJSON API returned HTTP {response.status_code}")
            data = response.json()
        except Exception as e:
            raise ScrapingError(f"Failed to fetch DummyJSON feed: {str(e)}")

        products_list = data.get("products", []) if isinstance(data, dict) else []
        return self.parse_json_products(products_list)

    def parse_json_products(self, products: list) -> List[ExtractedProductDTO]:
        """Maps DummyJSON item dictionaries to ExtractedProductDTO."""
        extracted = []
        for item in products:
            try:
                numeric_price = Decimal(str(item.get("price", 0)))
                if numeric_price <= 0:
                    continue

                discount = Decimal(str(item.get("discountPercentage", 0)))
                rating = Decimal(str(item.get("rating", 0))) if item.get("rating") else None
                stock = item.get("stock", 10)
                status = "in_stock" if stock > 0 else "out_of_stock"

                dto = ExtractedProductDTO(
                    external_id=f"DUMMY-{item.get('id')}",
                    title=item.get("title", "Untitled Product"),
                    url=f"https://dummyjson.com/products/{item.get('id')}",
                    price=numeric_price,
                    currency_code="USD",
                    shipping_price=Decimal("0.00"),
                    discount_pct=discount,
                    availability_status=status,
                    rating=rating,
                    review_count=item.get("stock", 25),
                    brand=item.get("brand") or "Generic",
                    category=item.get("category") or "General",
                    image_url=item.get("thumbnail") or (item.get("images", [None])[0] if item.get("images") else None),
                    data_provenance="demo_api",
                    raw_snippet=f"DummyJSON id={item.get('id')} price=${numeric_price}",
                )
                extracted.append(dto)
            except Exception as e:
                logger.warning("Failed to parse DummyJSON product item: %s", str(e))
                continue
        return extracted
