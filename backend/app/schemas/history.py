"""Pydantic schemas for Price History Tracking and Time-Series Analytics."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PricePointDTO(BaseModel):
    """Discrete historical price point formatted for charting."""

    observation_id: str
    observed_at: datetime
    listed_price: Decimal
    currency_code: str
    converted_price: Decimal
    reporting_currency: str
    shipping_price: Decimal
    availability_status: str
    discount_pct: Decimal
    data_provenance: str


class HistoricalStats(BaseModel):
    """Aggregate statistics for a price series."""

    current_price: Decimal
    min_price: Decimal
    max_price: Decimal
    avg_price: Decimal
    absolute_change: Decimal
    pct_change: Decimal
    volatility: Decimal  # Standard deviation
    observation_count: int
    first_observed_at: datetime
    last_observed_at: datetime
    freshness_status: str  # 'fresh' (<24h), 'stale' (24-72h), 'expired' (>72h)


class ListingHistorySummary(BaseModel):
    """Historical timeseries for a specific marketplace listing."""

    listing_id: str
    marketplace_id: str
    marketplace_name: str
    country_id: str
    listing_title: str
    listing_url: str
    currency_code: str
    stats: HistoricalStats
    price_points: List[PricePointDTO]


class ProductHistoryResponse(BaseModel):
    """Multi-marketplace consolidated price history for a canonical product."""

    product_id: str
    product_title: str
    product_sku: Optional[str] = None
    reporting_currency: str
    query_days: int
    overall_min_converted: Optional[Decimal] = None
    overall_max_converted: Optional[Decimal] = None
    overall_avg_converted: Optional[Decimal] = None
    marketplaces_tracked: int
    total_observations: int
    listings_history: List[ListingHistorySummary]
    timeline_series: List[Dict[str, Any]]  # Normalized chart points with keys per marketplace
