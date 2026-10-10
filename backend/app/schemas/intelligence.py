"""Pydantic schemas for Market Positioning Intelligence and Arbitrage Analytics."""

from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PriceAnomalyDTO(BaseModel):
    """Detected price anomaly or sudden volatility event."""

    listing_id: str
    marketplace_id: str
    marketplace_name: str
    product_id: str
    product_title: str
    previous_price: Decimal
    current_price: Decimal
    pct_change: Decimal
    anomaly_type: str  # 'price_drop', 'price_spike'
    detected_at: datetime
    severity: str  # 'medium', 'high', 'critical'


class MarketplacePositionDTO(BaseModel):
    """Positioning ranking and landed cost metric for an individual listing."""

    listing_id: str
    marketplace_id: str
    marketplace_name: str
    country_id: str
    original_price: Decimal
    original_currency: str
    landed_cost: Decimal
    reporting_currency: str
    rank: int
    price_gap_vs_our_product_pct: Optional[Decimal] = None
    position_tier: str  # 'cheapest', 'competitive', 'premium', 'overpriced'
    is_our_product: bool = False
    is_cheapest: bool = False


class ProductPositioningResponse(BaseModel):
    """Comprehensive market positioning and strategy analysis for a canonical product."""

    product_id: str
    product_title: str
    destination_country: str
    reporting_currency: str
    our_target_landed_cost: Optional[Decimal] = None
    competitor_median_landed_cost: Optional[Decimal] = None
    competitor_min_landed_cost: Optional[Decimal] = None
    competitor_max_landed_cost: Optional[Decimal] = None
    price_gap_vs_median_pct: Optional[Decimal] = None
    positioning_index: Optional[Decimal] = None
    market_competitiveness: str  # 'dominant', 'highly_competitive', 'moderately_competitive', 'uncompetitive'
    strategic_recommendation: str
    recommendation_reasoning: str
    total_competitors: int
    rankings: List[MarketplacePositionDTO]
    anomalies: List[PriceAnomalyDTO]


class ExportOpportunityDTO(BaseModel):
    """Identified cross-border price arbitrage and export opportunity."""

    product_id: str
    product_title: str
    source_marketplace: str
    source_country: str
    source_currency: str
    source_price: Decimal
    target_marketplace: str
    target_country: str
    target_currency: str
    target_market_price: Decimal
    landed_cost_in_target: Decimal
    reporting_currency: str
    net_profit_margin: Decimal
    net_margin_pct: Decimal
    opportunity_score: float
    feasibility_rating: str  # 'high', 'medium', 'low'


class ExportOpportunitiesResponse(BaseModel):
    """Consolidated list of cross-border export opportunities."""

    reporting_currency: str
    min_margin_pct_filter: Decimal
    total_opportunities_found: int
    opportunities: List[ExportOpportunityDTO]
