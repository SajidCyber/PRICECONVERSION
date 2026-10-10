"""Landed Cost Calculator and Cross-Border Price Comparison Matrix Engine."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import EntityNotFoundError, LandedCostCalculationError
from app.core.logging_config import logger
from app.models import (
    Country,
    LandedCostConfig,
    Marketplace,
    PriceObservation,
    Product,
    ProductListing,
)
from app.schemas.pricing import (
    LandedCostBreakdown,
    LandedCostSimulationRequest,
    ListingComparisonItem,
    ProductComparisonMatrixResponse,
)
from app.services.pricing.fx_service import FXService


class LandedCostService:
    """Computes international landed cost and compiles cross-border comparison matrices."""

    @classmethod
    def calculate_landed_cost(
        cls,
        db: Session,
        price: Decimal,
        source_currency: str,
        destination_country_id: str,
        product_category: str = "*",
        shipping_price_hint: Optional[Decimal] = None,
        override_freight: Optional[Decimal] = None,
        override_duty_rate: Optional[Decimal] = None,
        override_tax_rate: Optional[Decimal] = None,
        override_insurance_rate: Optional[Decimal] = None,
        override_handling_fee: Optional[Decimal] = None,
    ) -> LandedCostBreakdown:
        """Calculates itemized landed cost based on country rules, tariffs, and FX conversion."""
        dest_country = db.query(Country).filter(Country.id == destination_country_id.upper()).first()
        if not dest_country:
            raise EntityNotFoundError("Country", destination_country_id)

        dest_currency = dest_country.currency_code

        # 1. Fetch trade & tariff configuration
        config = (
            db.query(LandedCostConfig)
            .filter(
                LandedCostConfig.country_id == dest_country.id,
                LandedCostConfig.category.in_([product_category, "*"]),
            )
            .order_by(LandedCostConfig.category.desc())  # Specific category before '*'
            .first()
        )

        if not config:
            # Fallback default configuration
            duty_rate = override_duty_rate if override_duty_rate is not None else Decimal("0.0500")
            tax_rate = override_tax_rate if override_tax_rate is not None else Decimal("0.1000")
            de_minimis = Decimal("0.00")
            freight = override_freight if override_freight is not None else Decimal("20.00")
            ins_rate = override_insurance_rate if override_insurance_rate is not None else Decimal("0.0100")
            handling = override_handling_fee if override_handling_fee is not None else Decimal("5.00")
        else:
            duty_rate = override_duty_rate if override_duty_rate is not None else config.customs_duty_rate
            tax_rate = override_tax_rate if override_tax_rate is not None else config.import_tax_rate
            de_minimis = config.de_minimis_threshold
            freight = override_freight if override_freight is not None else config.default_freight
            ins_rate = override_insurance_rate if override_insurance_rate is not None else config.insurance_rate
            handling = override_handling_fee if override_handling_fee is not None else config.handling_fee

        # If shipping price hint was extracted from listing and no manual override given, use it
        if shipping_price_hint is not None and override_freight is None:
            # Convert shipping hint if in foreign currency
            if shipping_price_hint > 0:
                freight = shipping_price_hint

        # 2. Currency Conversion
        fx_rate, fx_source, is_fallback, _ = FXService.get_rate(db, source_currency, dest_currency)
        converted_price = Decimal(f"{(price * fx_rate):.2f}")

        # 3. Freight & Insurance (CIF Base)
        insurance_amount = Decimal(f"{(converted_price * ins_rate):.2f}")
        cif_value = Decimal(f"{(converted_price + freight + insurance_amount):.2f}")

        # 4. Customs Duty Calculation with De Minimis Check
        is_duty_exempt = (de_minimis > 0) and (cif_value <= de_minimis)
        if is_duty_exempt:
            duty_amount = Decimal("0.00")
        else:
            duty_amount = Decimal(f"{(cif_value * duty_rate):.2f}")

        # 5. Import Tax Calculation (VAT / GST applied on CIF + Duty)
        tax_base = Decimal(f"{(cif_value + duty_amount):.2f}")
        tax_amount = Decimal(f"{(tax_base * tax_rate):.2f}")

        # 6. Total Landed Cost
        total_landed = Decimal(f"{(cif_value + duty_amount + tax_amount + handling):.2f}")

        # Effective markup percentage over converted base sticker price
        if converted_price > 0:
            markup_pct = Decimal(f"{(((total_landed - converted_price) / converted_price) * 100):.2f}")
        else:
            markup_pct = Decimal("0.00")

        assumptions = {
            "destination_country": dest_country.name,
            "currency_pair": f"{source_currency}->{dest_currency}",
            "applied_duty_rate_pct": float(duty_rate * 100),
            "applied_tax_rate_pct": float(tax_rate * 100),
            "de_minimis_threshold": float(de_minimis),
            "is_de_minimis_applied": is_duty_exempt,
            "freight_assumed": float(freight),
            "insurance_rate_pct": float(ins_rate * 100),
            "handling_fee": float(handling),
        }

        return LandedCostBreakdown(
            original_price=price,
            original_currency=source_currency.upper(),
            destination_currency=dest_currency,
            fx_rate=fx_rate,
            fx_source=fx_source,
            is_fx_fallback=is_fallback,
            converted_price=converted_price,
            freight_fee=freight,
            insurance_fee=insurance_amount,
            cif_value=cif_value,
            de_minimis_threshold=de_minimis,
            is_duty_exempt=is_duty_exempt,
            customs_duty_rate=duty_rate,
            customs_duty_amount=duty_amount,
            tax_base_value=tax_base,
            import_tax_rate=tax_rate,
            import_tax_amount=tax_amount,
            handling_fee=handling,
            total_landed_cost=total_landed,
            effective_markup_pct=markup_pct,
            assumptions_log=assumptions,
        )

    @classmethod
    def get_product_comparison_matrix(
        cls,
        db: Session,
        product_id: str,
        destination_country_id: str = "US",
        reporting_currency: Optional[str] = None,
    ) -> ProductComparisonMatrixResponse:
        """Compiles cross-border comparison matrix for a canonical product across all its active listings."""
        product = (
            db.query(Product)
            .options(
                joinedload(Product.listings)
                .joinedload(ProductListing.marketplace)
                .joinedload(Marketplace.country)
            )
            .filter(Product.id == product_id)
            .first()
        )
        if not product:
            raise EntityNotFoundError("Product", product_id)

        target_country = db.query(Country).filter(Country.id == destination_country_id.upper()).first()
        if not target_country:
            raise EntityNotFoundError("Country", destination_country_id)

        rep_curr = (reporting_currency or target_country.currency_code).upper()

        listing_items: List[ListingComparisonItem] = []

        for listing in product.listings:
            if not listing.is_active:
                continue

            # Fetch newest price observation
            latest_obs = (
                db.query(PriceObservation)
                .filter(PriceObservation.listing_id == listing.id)
                .order_by(PriceObservation.observed_at.desc())
                .first()
            )
            if not latest_obs:
                continue

            breakdown = cls.calculate_landed_cost(
                db=db,
                price=latest_obs.listed_price,
                source_currency=latest_obs.currency_code,
                destination_country_id=destination_country_id,
                product_category=product.category,
                shipping_price_hint=latest_obs.shipping_price,
            )

            # Benchmark price gap if benchmark target price available
            gap_pct = None
            if product.target_base_price and product.target_base_price > 0:
                # Convert benchmark to destination currency
                b_fx, _, _, _ = FXService.get_rate(db, product.base_currency, rep_curr)
                benchmark_converted = product.target_base_price * b_fx
                if benchmark_converted > 0:
                    gap_pct = Decimal(f"{(((breakdown.total_landed_cost - benchmark_converted) / benchmark_converted) * 100):.2f}")

            country_name = listing.marketplace.country.name if listing.marketplace and listing.marketplace.country else "Unknown"

            item = ListingComparisonItem(
                listing_id=listing.id,
                marketplace_id=listing.marketplace_id,
                marketplace_name=listing.marketplace.name if listing.marketplace else listing.marketplace_id,
                country_id=listing.marketplace.country_id if listing.marketplace else "US",
                country_name=country_name,
                listing_title=listing.listing_title,
                listing_url=listing.listing_url,
                seller_name=listing.seller_name,
                availability_status=latest_obs.availability_status,
                rating=latest_obs.rating,
                data_provenance=latest_obs.data_provenance,
                last_observed_at=latest_obs.observed_at,
                original_price=latest_obs.listed_price,
                original_currency=latest_obs.currency_code,
                breakdown=breakdown,
                is_cheapest_sticker=False,
                is_cheapest_landed=False,
                price_gap_vs_benchmark_pct=gap_pct,
            )
            listing_items.append(item)

        # Flag cheapest sticker and cheapest landed
        if listing_items:
            min_converted = min(l.breakdown.converted_price for l in listing_items)
            min_landed = min(l.breakdown.total_landed_cost for l in listing_items)
            max_landed = max(l.breakdown.total_landed_cost for l in listing_items)

            for l in listing_items:
                if l.breakdown.converted_price == min_converted:
                    l.is_cheapest_sticker = True
                if l.breakdown.total_landed_cost == min_landed:
                    l.is_cheapest_landed = True

            cheapest_market = next((l.marketplace_name for l in listing_items if l.is_cheapest_landed), None)
            spread_pct = Decimal(f"{(((max_landed - min_landed) / min_landed) * 100):.2f}") if min_landed > 0 else Decimal("0.00")
        else:
            min_landed = None
            max_landed = None
            cheapest_market = None
            spread_pct = None

        return ProductComparisonMatrixResponse(
            product_id=product.id,
            product_sku=product.sku,
            product_title=product.title,
            product_brand=product.brand,
            product_category=product.category,
            image_url=product.image_url,
            target_base_price=product.target_base_price,
            base_currency=product.base_currency,
            destination_country=destination_country_id.upper(),
            reporting_currency=rep_curr,
            total_marketplaces_tracked=len(listing_items),
            cheapest_marketplace=cheapest_market,
            lowest_landed_cost=min_landed,
            highest_landed_cost=max_landed,
            landed_cost_spread_pct=spread_pct,
            listings=listing_items,
        )
