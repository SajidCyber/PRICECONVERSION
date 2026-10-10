"""Market Positioning, Strategic Pricing Intelligence, and Arbitrage API Router."""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.intelligence import (
    ExportOpportunitiesResponse,
    PriceAnomalyDTO,
    ProductPositioningResponse,
)
from app.services.analytics.positioning import MarketPositioningService

router = APIRouter(prefix="/intelligence", tags=["Market Positioning & Intelligence"])


@router.get("/positioning", response_model=APIResponse[ProductPositioningResponse])
def get_product_positioning_analysis(
    product_id: str = Query(..., description="Canonical product UUID"),
    destination_country: str = Query("US", min_length=2, max_length=2, description="Target market country (e.g. 'US', 'GB', 'IN')"),
    reporting_currency: Optional[str] = Query(None, min_length=3, max_length=3, description="Optional reporting currency override"),
    db: Session = Depends(get_db),
) -> APIResponse[ProductPositioningResponse]:
    """Generates competitive positioning analysis, price gap calculations, and strategic pricing recommendations."""
    positioning = MarketPositioningService.analyze_product_positioning(
        db=db,
        product_id=product_id,
        destination_country_id=destination_country,
        reporting_currency=reporting_currency,
    )
    return APIResponse(success=True, data=positioning)


@router.get("/opportunities", response_model=APIResponse[ExportOpportunitiesResponse])
def get_export_arbitrage_opportunities(
    min_margin_pct: float = Query(15.0, ge=1.0, le=90.0, description="Minimum net profit margin percentage filter"),
    reporting_currency: str = Query("USD", min_length=3, max_length=3, description="Display reporting currency"),
    db: Session = Depends(get_db),
) -> APIResponse[ExportOpportunitiesResponse]:
    """Scans multi-region catalog for cross-border price arbitrage and high-margin export opportunities."""
    opportunities = MarketPositioningService.detect_export_opportunities(
        db=db,
        min_margin_pct=Decimal(str(min_margin_pct)),
        reporting_currency=reporting_currency,
    )
    return APIResponse(success=True, data=opportunities)


@router.get("/anomalies", response_model=APIResponse[List[PriceAnomalyDTO]])
def list_price_anomalies(
    product_id: Optional[str] = Query(None, description="Optional canonical product UUID filter"),
    threshold_pct: float = Query(15.0, ge=5.0, le=80.0, description="Price jump/drop percentage threshold"),
    db: Session = Depends(get_db),
) -> APIResponse[List[PriceAnomalyDTO]]:
    """Retrieves detected price anomalies, sudden discount drops, and flash volatility events."""
    anomalies = MarketPositioningService.detect_anomalies(
        db=db,
        product_id=product_id,
        threshold_pct=Decimal(str(threshold_pct)),
    )
    return APIResponse(success=True, data=anomalies)
