"""Abstract Base Scraper Adapter."""

import re
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.core.logging_config import logger
from app.core.security import SafeHttpClient
from app.schemas.scraper import ExtractedProductDTO


class BaseScraperAdapter(ABC):
    """Abstract Strategy interface for all e-commerce scraper adapters."""

    def __init__(self, marketplace_id: str, base_url: str, default_currency: str = "USD"):
        self.marketplace_id = marketplace_id
        self.base_url = base_url.rstrip("/")
        self.default_currency = default_currency
        self.http_client = SafeHttpClient()

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Unique identifier for this adapter."""
        pass

    @property
    def is_live_scraper(self) -> bool:
        """True if adapter performs live HTTP scraping against external web targets."""
        return True

    @property
    def supports_categories(self) -> bool:
        """True if adapter supports category filtering."""
        return True

    @abstractmethod
    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        max_items: int = 20,
        custom_url: Optional[str] = None,
    ) -> List[ExtractedProductDTO]:
        """Extracts a list of product listings from the target source."""
        pass

    def parse_numeric_price(self, raw_price_text: str) -> Decimal:
        """Extracts clean numeric Decimal price from raw formatted string."""
        if not raw_price_text:
            raise ValueError("Empty price string")

        # Strip currency symbols (£, $, €, ₹, etc.) and non-numeric characters except period and comma
        clean = re.sub(r"[^\d.,]", "", raw_price_text.strip())
        if not clean:
            raise ValueError(f"No numeric characters found in price: '{raw_price_text}'")

        # Handle European decimal formatting (e.g. 1.299,50 -> 1299.50)
        if "," in clean and "." in clean:
            if clean.find(",") > clean.find("."):  # German/French format (1.234,56)
                clean = clean.replace(".", "").replace(",", ".")
            else:  # US/UK format (1,234.56)
                clean = clean.replace(",", "")
        elif "," in clean and "." not in clean:
            # Check if comma is decimal separator (e.g. 49,99)
            if len(clean.split(",")[-1]) == 2:
                clean = clean.replace(",", ".")
            else:
                clean = clean.replace(",", "")

        val = Decimal(clean)
        if val <= 0:
            raise ValueError(f"Price must be positive, got {val}")
        return val

    def normalize_currency_symbol(self, raw_text: str) -> str:
        """Infers ISO currency code from currency symbols or text."""
        if "£" in raw_text or "GBP" in raw_text:
            return "GBP"
        elif "€" in raw_text or "EUR" in raw_text:
            return "EUR"
        elif "₹" in raw_text or "INR" in raw_text or "Rs" in raw_text:
            return "INR"
        elif "¥" in raw_text or "JPY" in raw_text:
            return "JPY"
        elif "$" in raw_text or "USD" in raw_text:
            return "USD"
        return self.default_currency
