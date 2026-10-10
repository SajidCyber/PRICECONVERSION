"""Cross-Border Pricing, Currency Conversion, and Landed Cost API Router."""

from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Country, LandedCostConfig, Product
from app.schemas.common import APIResponse
from app.schemas.history import ProductHistoryResponse
from app.schemas.pricing import (
    ExchangeRateResponse,
    LandedCostBreakdown,
    LandedCostConfigDTO,
    LandedCostConfigUpdate,
    LandedCostSimulationRequest,
    ProductCatalogItem,
    ProductComparisonMatrixResponse,
)
from app.services.analytics.history_service import PriceHistoryService
from app.services.pricing.fx_service import FXService
from app.services.pricing.landed_cost import LandedCostService

router = APIRouter(prefix="/pricing", tags=["Cross-Border Pricing & Landed Cost"])


@router.get("/products", response_model=APIResponse[List[ProductCatalogItem]])
def list_catalog_products(db: Session = Depends(get_db)) -> APIResponse[List[ProductCatalogItem]]:
    """Lists all canonical products available in the cross-border catalog."""
    products = db.query(Product).order_by(Product.created_at.asc()).all()
    items = [
        ProductCatalogItem(
            id=p.id,
            sku=p.sku,
            title=p.title,
            brand=p.brand,
            category=p.category,
            image_url=p.image_url,
            target_base_price=p.target_base_price,
            base_currency=p.base_currency,
            listings_count=len(p.listings),
        )
        for p in products
    ]
    return APIResponse(success=True, data=items)



@router.get("/history/{product_id}", response_model=APIResponse[ProductHistoryResponse])
def get_product_price_history(
    product_id: str,
    reporting_currency: str = Query("USD", min_length=3, max_length=3, description="Display reporting currency"),
    days: int = Query(30, ge=0, le=365, description="Lookback window in days (0 for all time)"),
    db: Session = Depends(get_db),
) -> APIResponse[ProductHistoryResponse]:
    """Retrieves consolidated cross-marketplace historical price points and trend analytics for a product."""
    history = PriceHistoryService.get_product_history(
        db=db,
        product_id=product_id,
        reporting_currency=reporting_currency,
        days=days,
    )
    return APIResponse(success=True, data=history)


@router.get("/exchange-rates", response_model=APIResponse[List[ExchangeRateResponse]])
def get_exchange_rates(db: Session = Depends(get_db)) -> APIResponse[List[ExchangeRateResponse]]:
    """Returns the list of cached foreign exchange rates with source and staleness flags."""
    rates = FXService.list_cached_rates(db)
    return APIResponse(success=True, data=rates)


@router.post("/exchange-rates/refresh", response_model=APIResponse[List[ExchangeRateResponse]])
async def refresh_exchange_rates(db: Session = Depends(get_db)) -> APIResponse[List[ExchangeRateResponse]]:
    """Forces an immediate synchronization with the live foreign exchange rate provider."""
    await FXService.refresh_live_rates(db)
    rates = FXService.list_cached_rates(db)
    return APIResponse(success=True, data=rates)


@router.get("/comparison", response_model=APIResponse[ProductComparisonMatrixResponse])
def get_product_price_comparison(
    product_id: str = Query(..., description="Canonical product UUID"),
    destination_country: str = Query("US", min_length=2, max_length=2, description="Target import country (e.g. 'US', 'GB', 'IN')"),
    reporting_currency: Optional[str] = Query(None, description="Optional override of output display currency"),
    db: Session = Depends(get_db),
) -> APIResponse[ProductComparisonMatrixResponse]:
    """Generates cross-border landed cost comparison matrix across all regional listings of a product."""
    matrix = LandedCostService.get_product_comparison_matrix(
        db=db,
        product_id=product_id,
        destination_country_id=destination_country,
        reporting_currency=reporting_currency,
    )
    return APIResponse(success=True, data=matrix)


@router.post("/landed-cost/calculate", response_model=APIResponse[LandedCostBreakdown])
def simulate_landed_cost(
    payload: LandedCostSimulationRequest,
    db: Session = Depends(get_db),
) -> APIResponse[LandedCostBreakdown]:
    """Interactive simulation calculator for calculating landed cost with custom sensitivity overrides."""
    breakdown = LandedCostService.calculate_landed_cost(
        db=db,
        price=payload.price,
        source_currency=payload.source_currency,
        destination_country_id=payload.destination_country,
        product_category=payload.product_category or "*",
        override_freight=payload.override_freight,
        override_duty_rate=payload.override_duty_rate,
        override_tax_rate=payload.override_tax_rate,
        override_insurance_rate=payload.override_insurance_rate,
        override_handling_fee=payload.override_handling_fee,
    )
    return APIResponse(success=True, data=breakdown)


@router.get("/configs", response_model=APIResponse[List[LandedCostConfigDTO]])
def list_landed_cost_configs(db: Session = Depends(get_db)) -> APIResponse[List[LandedCostConfigDTO]]:
    """Lists trade tariff, tax rates, de minimis thresholds, and logistics defaults per country."""
    configs = db.query(LandedCostConfig).all()
    countries = {c.id: c.name for c in db.query(Country).all()}

    data = [
        LandedCostConfigDTO(
            id=c.id,
            country_id=c.country_id,
            country_name=countries.get(c.country_id, c.country_id),
            category=c.category,
            customs_duty_rate=c.customs_duty_rate,
            import_tax_rate=c.import_tax_rate,
            de_minimis_threshold=c.de_minimis_threshold,
            default_freight=c.default_freight,
            insurance_rate=c.insurance_rate,
            handling_fee=c.handling_fee,
            updated_at=c.updated_at,
        )
        for c in configs
    ]
    return APIResponse(success=True, data=data)


@router.put("/configs/{country_id}", response_model=APIResponse[LandedCostConfigDTO])
def update_landed_cost_config(
    country_id: str,
    payload: LandedCostConfigUpdate,
    category: str = Query("*", description="Category wildcard or specific name"),
    db: Session = Depends(get_db),
) -> APIResponse[LandedCostConfigDTO]:
    """Updates trade tariff, tax rate, and shipping assumptions for a destination country."""
    config = (
        db.query(LandedCostConfig)
        .filter(
            LandedCostConfig.country_id == country_id.upper(),
            LandedCostConfig.category == category,
        )
        .first()
    )

    if not config:
        # Check if country exists
        country = db.query(Country).filter(Country.id == country_id.upper()).first()
        if not country:
            raise EntityNotFoundError("Country", country_id)
        config = LandedCostConfig(country_id=country_id.upper(), category=category)
        db.add(config)

    if payload.customs_duty_rate is not None:
        config.customs_duty_rate = payload.customs_duty_rate
    if payload.import_tax_rate is not None:
        config.import_tax_rate = payload.import_tax_rate
    if payload.de_minimis_threshold is not None:
        config.de_minimis_threshold = payload.de_minimis_threshold
    if payload.default_freight is not None:
        config.default_freight = payload.default_freight
    if payload.insurance_rate is not None:
        config.insurance_rate = payload.insurance_rate
    if payload.handling_fee is not None:
        config.handling_fee = payload.handling_fee

    db.commit()
    db.refresh(config)

    country = db.query(Country).filter(Country.id == config.country_id).first()
    dto = LandedCostConfigDTO(
        id=config.id,
        country_id=config.country_id,
        country_name=country.name if country else config.country_id,
        category=config.category,
        customs_duty_rate=config.customs_duty_rate,
        import_tax_rate=config.import_tax_rate,
        de_minimis_threshold=config.de_minimis_threshold,
        default_freight=config.default_freight,
        insurance_rate=config.insurance_rate,
        handling_fee=config.handling_fee,
        updated_at=config.updated_at,
    )
    return APIResponse(success=True, data=dto)
