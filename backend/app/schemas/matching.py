"""Pydantic schemas for Product Cross-Listing Matching and Review."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchEvidence(BaseModel):
    """Breakdown of matching signals and similarity metrics."""

    brand_match: bool = Field(..., description="Whether brand names aligned")
    exact_sku_match: bool = Field(default=False, description="Exact SKU/GTIN match")
    model_number_overlap: List[str] = Field(default_factory=list, description="Extracted overlapping model codes")
    token_jaccard_score: float = Field(default=0.0, description="Token set overlap ratio (0.0 - 1.0)")
    levenshtein_similarity: float = Field(default=0.0, description="Fuzzy string similarity (0.0 - 1.0)")
    matched_tokens: List[str] = Field(default_factory=list, description="Tokens found in common")


class ProductMatchResponse(BaseModel):
    """Representation of a product-listing match relationship."""

    id: str
    product_id: str
    product_title: str
    product_brand: Optional[str] = None
    product_category: str
    listing_id: str
    listing_title: str
    marketplace_id: str
    marketplace_name: str
    currency_code: str
    confidence_score: Decimal
    match_type: str
    match_evidence: Dict[str, Any]
    status: str  # 'confirmed', 'probable', 'uncertain', 'rejected'
    created_at: datetime


class MatchReviewUpdate(BaseModel):
    """Payload to review or update match status."""

    status: str = Field(..., description="'confirmed', 'probable', 'uncertain', or 'rejected'")
    notes: Optional[str] = Field(default=None, description="Optional reviewer notes")


class BatchMatchResponse(BaseModel):
    """Summary of batch matching execution."""

    total_listings_inspected: int
    new_matches_found: int
    confirmed_count: int
    probable_count: int
    uncertain_count: int
    execution_time_ms: float
