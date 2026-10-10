"""Pydantic schemas for Scraping Jobs, Extracted Products, and Ingestion Batches."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractedProductDTO(BaseModel):
    """Structured extraction format returned by all scraper adapters."""

    external_id: str = Field(..., description="Marketplace listing identifier or SKU")
    title: str = Field(..., description="Raw listing title")
    url: str = Field(..., description="Canonical product URL on marketplace")
    price: Decimal = Field(..., gt=0, description="Normalized numeric price")
    currency_code: str = Field(..., min_length=3, max_length=3, description="ISO 4217 Currency code")
    shipping_price: Decimal = Field(default=Decimal("0.00"), description="Shipping price if available")
    discount_pct: Decimal = Field(default=Decimal("0.00"), description="Discount percentage")
    availability_status: str = Field(default="in_stock", description="in_stock, out_of_stock, or pre_order")
    rating: Optional[Decimal] = Field(default=None, description="Product review rating out of 5.0")
    review_count: Optional[int] = Field(default=None, description="Number of reviews")
    brand: Optional[str] = Field(default=None, description="Brand name if detected")
    category: Optional[str] = Field(default=None, description="Category name")
    image_url: Optional[str] = Field(default=None, description="Thumbnail or main product image")
    data_provenance: str = Field(default="live_scrape", description="Origin tag")
    raw_snippet: Optional[str] = Field(default=None, description="Debug snippet of raw price payload")


class ScrapingJobCreate(BaseModel):
    """Request payload to initiate a scraping job."""

    marketplace_id: str = Field(..., description="ID of target marketplace (e.g., 'books_to_scrape')")
    category: Optional[str] = Field(default=None, description="Specific category filter if supported")
    target_url: Optional[str] = Field(default=None, description="Direct target URL override")
    max_items: int = Field(default=20, ge=1, le=100, description="Maximum items to scrape")


class ScrapingJobResponse(BaseModel):
    """Response representation of a ScrapingJob."""

    id: str
    marketplace_id: str
    status: str
    target_category: Optional[str] = None
    target_url: Optional[str] = None
    items_discovered: int
    items_extracted: int
    error_count: int
    error_log: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class AdapterInfo(BaseModel):
    """Metadata describing an active scraping adapter."""

    adapter_name: str
    marketplace_id: str
    marketplace_name: str
    country_id: str
    base_url: str
    currency_code: str
    is_live_scraper: bool
    supports_categories: bool


class ImportSummaryResponse(BaseModel):
    """Execution summary returned by Data Ingestion Service."""

    batch_id: str
    source_name: str
    source_type: str
    record_count: int
    inserted_count: int
    duplicate_count: int
    rejected_count: int
    summary_log: Dict[str, Any]
    imported_at: datetime
