"""Historical Price Tracking and Time-Series Analytics Service."""

import math
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import EntityNotFoundError
from app.core.logging_config import logger
from app.models import PriceObservation, Product, ProductListing
from app.schemas.history import (
    HistoricalStats,
    ListingHistorySummary,
    PricePointDTO,
    ProductHistoryResponse,
)
from app.services.pricing.fx_service import FXService


class PriceHistoryService:
    """Computes price statistics, volatility, trend deltas, and chart timelines."""

    @classmethod
    def compute_stats(
        cls,
        observations: List[PriceObservation],
    ) -> HistoricalStats:
        """Calculates statistical summary for a sequence of observations."""
        now = datetime.now(timezone.utc)
        if not observations:
            return HistoricalStats(
                current_price=Decimal("0.00"),
                min_price=Decimal("0.00"),
                max_price=Decimal("0.00"),
                avg_price=Decimal("0.00"),
                absolute_change=Decimal("0.00"),
                pct_change=Decimal("0.00"),
                volatility=Decimal("0.00"),
                observation_count=0,
                first_observed_at=now,
                last_observed_at=now,
                freshness_status="expired",
            )

        # Ensure sorted chronologically
        sorted_obs = sorted(observations, key=lambda o: o.observed_at)
        prices = [Decimal(str(o.listed_price)) for o in sorted_obs]

        min_p = min(prices)
        max_p = max(prices)
        avg_p = Decimal(f"{(sum(prices) / len(prices)):.2f}")
        current_p = prices[-1]
        oldest_p = prices[0]

        abs_change = Decimal(f"{(current_p - oldest_p):.2f}")
        pct_change = Decimal(f"{(((current_p - oldest_p) / oldest_p) * 100):.2f}") if oldest_p > 0 else Decimal("0.00")

        # Volatility (sample standard deviation)
        if len(prices) > 1:
            mean = float(avg_p)
            variance = sum((float(p) - mean) ** 2 for p in prices) / (len(prices) - 1)
            volatility = Decimal(f"{math.sqrt(variance):.2f}")
        else:
            volatility = Decimal("0.00")

        first_at = sorted_obs[0].observed_at
        last_at = sorted_obs[-1].observed_at

        # Ensure timezone-aware for delta calculation
        last_at_aware = last_at if last_at.tzinfo else last_at.replace(tzinfo=timezone.utc)
        age = now - last_at_aware

        if age < timedelta(hours=24):
            freshness = "fresh"
        elif age < timedelta(hours=72):
            freshness = "stale"
        else:
            freshness = "expired"

        return HistoricalStats(
            current_price=current_p,
            min_price=min_p,
            max_price=max_p,
            avg_price=avg_p,
            absolute_change=abs_change,
            pct_change=pct_change,
            volatility=volatility,
            observation_count=len(sorted_obs),
            first_observed_at=first_at,
            last_observed_at=last_at,
            freshness_status=freshness,
        )

    @classmethod
    def get_product_history(
        cls,
        db: Session,
        product_id: str,
        reporting_currency: str = "USD",
        days: int = 30,
    ) -> ProductHistoryResponse:
        """Consolidates cross-marketplace historical price data and time-series for a product."""
        product = (
            db.query(Product)
            .options(
                joinedload(Product.listings)
                .joinedload(ProductListing.marketplace)
            )
            .filter(Product.id == product_id)
            .first()
        )
        if not product:
            raise EntityNotFoundError("Product", product_id)

        rep_curr = reporting_currency.upper()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days) if days > 0 else datetime.min.replace(tzinfo=timezone.utc)

        listings_summaries: List[ListingHistorySummary] = []
        all_converted_prices: List[Decimal] = []
        timeline_dict: Dict[str, Dict[str, Any]] = {}
        total_obs_count = 0

        for listing in product.listings:
            obs_query = (
                db.query(PriceObservation)
                .filter(PriceObservation.listing_id == listing.id)
                .order_by(PriceObservation.observed_at.asc())
            )
            if days > 0:
                obs_query = obs_query.filter(PriceObservation.observed_at >= cutoff_date)

            observations = obs_query.all()
            if not observations:
                continue

            total_obs_count += len(observations)
            stats = cls.compute_stats(observations)

            # FX conversion for price points
            fx_rate, _, _, _ = FXService.get_rate(db, listing.currency_code, rep_curr)

            price_points: List[PricePointDTO] = []
            m_key = listing.marketplace_id

            for obs in observations:
                converted = Decimal(f"{(obs.listed_price * fx_rate):.2f}")
                all_converted_prices.append(converted)

                dto = PricePointDTO(
                    observation_id=obs.id,
                    observed_at=obs.observed_at,
                    listed_price=obs.listed_price,
                    currency_code=obs.currency_code,
                    converted_price=converted,
                    reporting_currency=rep_curr,
                    shipping_price=obs.shipping_price,
                    availability_status=obs.availability_status,
                    discount_pct=obs.discount_pct,
                    data_provenance=obs.data_provenance,
                )
                price_points.append(dto)

                # Format timeline for charts (hourly / daily grouping key)
                time_key = obs.observed_at.strftime("%Y-%m-%dT%H:00:00Z")
                if time_key not in timeline_dict:
                    timeline_dict[time_key] = {"timestamp": time_key}
                timeline_dict[time_key][m_key] = float(converted)
                timeline_dict[time_key][f"{m_key}_original"] = float(obs.listed_price)
                timeline_dict[time_key][f"{m_key}_currency"] = obs.currency_code

            summary = ListingHistorySummary(
                listing_id=listing.id,
                marketplace_id=listing.marketplace_id,
                marketplace_name=listing.marketplace.name if listing.marketplace else listing.marketplace_id,
                country_id=listing.marketplace.country_id if listing.marketplace else "US",
                listing_title=listing.listing_title,
                listing_url=listing.listing_url,
                currency_code=listing.currency_code,
                stats=stats,
                price_points=price_points,
            )
            listings_summaries.append(summary)

        # Sort timeline by timestamp ASC
        timeline_series = [timeline_dict[k] for k in sorted(timeline_dict.keys())]

        overall_min = min(all_converted_prices) if all_converted_prices else None
        overall_max = max(all_converted_prices) if all_converted_prices else None
        overall_avg = Decimal(f"{(sum(all_converted_prices) / len(all_converted_prices)):.2f}") if all_converted_prices else None

        return ProductHistoryResponse(
            product_id=product.id,
            product_title=product.title,
            product_sku=product.sku,
            reporting_currency=rep_curr,
            query_days=days,
            overall_min_converted=overall_min,
            overall_max_converted=overall_max,
            overall_avg_converted=overall_avg,
            marketplaces_tracked=len(listings_summaries),
            total_observations=total_obs_count,
            listings_history=listings_summaries,
            timeline_series=timeline_series,
        )
