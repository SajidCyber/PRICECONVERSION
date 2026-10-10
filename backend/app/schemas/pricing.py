"""Pydantic schemas for FX Rates, Landed Cost Calculations, and Cross-Border Comparisons."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExchangeRateResponse(BaseModel):
    """Foreign exchange rate snapshot."""

    base_currency: str
    target_currency: str
    rate: Decimal
    source: str
    is_fallback: bool
    fetched_at: datetime


class LandedCostBreakdown(BaseModel):
    """Detailed itemized breakdown of landed cost components."""

    original_price: Decimal
    original_currency: str
    destination_currency: str
    fx_rate: Decimal
    fx_source: str
    is_fx_fallback: bool

    converted_price: Decimal
    freight_fee: Decimal
    insurance_fee: Decimal
    cif_value: Decimal

    de_minimis_threshold: Decimal
    is_duty_exempt: bool
    customs_duty_rate: Decimal
    customs_duty_amount: Decimal

    tax_base_value: Decimal
    import_tax_rate: Decimal
    import_tax_amount: Decimal

    handling_fee: Decimal
    total_landed_cost: Decimal
    effective_markup_pct: Decimal
    assumptions_log: Dict[str, Any]


class LandedCostSimulationRequest(BaseModel):
    """Request payload for interactive landed-cost scenario simulation."""

    price: Decimal = Field(..., gt=0, description="Product price in source currency")
    source_currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 Currency code (e.g. 'USD')")
    destination_country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 (e.g. 'GB', 'IN', 'US')")
    reporting_currency: Optional[str] = Field(None, description="Optional override of output currency")
    product_category: Optional[str] = Field("*", description="Product category for tariff classification")

    # Optional manual overrides for sensitivity testing
    override_freight: Optional[Decimal] = Field(None, ge=0)
    override_duty_rate: Optional[Decimal] = Field(None, ge=0, le=1.0)
    override_tax_rate: Optional[Decimal] = Field(None, ge=0, le=1.0)
    override_insurance_rate: Optional[Decimal] = Field(None, ge=0, le=1.0)
    override_handling_fee: Optional[Decimal] = Field(None, ge=0)


class ListingComparisonItem(BaseModel):
    """Cross-border pricing item in comparison matrix."""

    listing_id: str
    marketplace_id: str
    marketplace_name: str
    country_id: str
    country_name: str
    listing_title: str
    listing_url: str
    seller_name: Optional[str] = None
    availability_status: str
    rating: Optional[Decimal] = None
    data_provenance: str
    last_observed_at: datetime

    original_price: Decimal
    original_currency: str
    breakdown: LandedCostBreakdown

    is_cheapest_sticker: bool
    is_cheapest_landed: bool
    price_gap_vs_benchmark_pct: Optional[Decimal] = None


class ProductComparisonMatrixResponse(BaseModel):
    """Comprehensive cross-border comparison matrix for a canonical product."""

    product_id: str
    product_sku: Optional[str] = None
    product_title: str
    product_brand: Optional[str] = None
    product_category: str
    image_url: Optional[str] = None
    target_base_price: Optional[Decimal] = None
    base_currency: str

    destination_country: str
    reporting_currency: str
    total_marketplaces_tracked: int
    cheapest_marketplace: Optional[str] = None
    lowest_landed_cost: Optional[Decimal] = None
    highest_landed_cost: Optional[Decimal] = None
    landed_cost_spread_pct: Optional[Decimal] = None

    listings: List[ListingComparisonItem]


class LandedCostConfigDTO(BaseModel):
    """Trade tariff and tax parameter configuration for a country."""

    id: str
    country_id: str
    country_name: str
    category: str
    customs_duty_rate: Decimal
    import_tax_rate: Decimal
    de_minimis_threshold: Decimal
    default_freight: Decimal
    insurance_rate: Decimal
    handling_fee: Decimal
    updated_at: datetime


class LandedCostConfigUpdate(BaseModel):
    """Payload to update trade and tariff assumptions."""

    customs_duty_rate: Optional[Decimal] = Field(None, ge=0, le=1.0)
    import_tax_rate: Optional[Decimal] = Field(None, ge=0, le=1.0)
    de_minimis_threshold: Optional[Decimal] = Field(None, ge=0)
    default_freight: Optional[Decimal] = Field(None, ge=0)
    insurance_rate: Optional[Decimal] = Field(None, ge=0, le=1.0)
    handling_fee: Optional[Decimal] = Field(None, ge=0)


class ProductCatalogItem(BaseModel):
    """Canonical product summary item for catalog selectors."""

    id: str
    sku: Optional[str] = None
    title: str
    brand: Optional[str] = None
    category: str
    image_url: Optional[str] = None
    target_base_price: Optional[Decimal] = None
    base_currency: str = "USD"
    listings_count: int = 0

