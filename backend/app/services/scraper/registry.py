"""Scraper Adapter Registry and Discovery."""

from typing import Dict, List, Optional
from app.core.exceptions import ScrapingError
from app.schemas.scraper import AdapterInfo
from app.services.scraper.base_adapter import BaseScraperAdapter
from app.services.scraper.books_adapter import BooksToScrapeAdapter
from app.services.scraper.dummyjson_adapter import DummyJsonAdapter
from app.services.scraper.fakestore_adapter import FakeStoreAdapter


class ScraperRegistry:
    """Registry maintaining active scraper and feed adapters."""

    def __init__(self):
        self._adapters: Dict[str, BaseScraperAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Registers system default scraper adapters."""
        self.register(BooksToScrapeAdapter())
        self.register(DummyJsonAdapter())
        self.register(FakeStoreAdapter())

    def register(self, adapter: BaseScraperAdapter) -> None:
        """Registers a new adapter instance."""
        self._adapters[adapter.marketplace_id] = adapter

    def get_adapter(self, marketplace_id: str) -> BaseScraperAdapter:
        """Retrieves adapter by marketplace identifier."""
        if marketplace_id not in self._adapters:
            raise ScrapingError(
                f"No scraper adapter registered for marketplace '{marketplace_id}'. "
                f"Available adapters: {list(self._adapters.keys())}"
            )
        return self._adapters[marketplace_id]

    def list_adapters(self) -> List[AdapterInfo]:
        """Returns metadata list of all registered adapters."""
        results = []
        for marketplace_id, adapter in self._adapters.items():
            results.append(
                AdapterInfo(
                    adapter_name=adapter.adapter_name,
                    marketplace_id=marketplace_id,
                    marketplace_name=marketplace_id.replace("_", " ").title(),
                    country_id="GB" if "uk" in marketplace_id or "books" in marketplace_id else ("IN" if "in" in marketplace_id else "US"),
                    base_url=adapter.base_url,
                    currency_code=adapter.default_currency,
                    is_live_scraper=adapter.is_live_scraper,
                    supports_categories=adapter.supports_categories,
                )
            )
        return results


scraper_registry = ScraperRegistry()
