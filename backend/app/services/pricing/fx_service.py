"""Foreign Exchange Rate Service with Real-Time Fetching and Resilient Fallback Caching."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging_config import logger
from app.core.security import SafeHttpClient
from app.models.exchange_rate import ExchangeRate
from app.schemas.pricing import ExchangeRateResponse


class FXService:
    """Provides traceable currency conversion rates with persistent caching."""

    CACHE_TTL_HOURS = settings.FX_CACHE_TTL_HOURS
    FX_API_URL = settings.FX_API_URL

    @classmethod
    async def refresh_live_rates(cls, db: Session) -> List[ExchangeRate]:
        """Fetches live FX rates from open.er-api.com and persists to DB cache."""
        logger.info("Fetching live FX rates from %s...", cls.FX_API_URL)
        client = SafeHttpClient()
        try:
            response = await client.get(cls.FX_API_URL)
            if response.status_code != 200:
                raise AppError(f"FX API returned HTTP {response.status_code}")
            data = response.json()
        except Exception as e:
            logger.warning("Live FX fetch failed: %s. Relying on fallback cache.", str(e))
            raise AppError(f"Unable to refresh FX rates: {str(e)}")

        rates_dict = data.get("rates", {})
        now = datetime.now(timezone.utc)
        stored_rates = []

        # Always include USD base identity
        rates_dict["USD"] = 1.0

        for target_curr, rate_val in rates_dict.items():
            try:
                dec_rate = Decimal(str(rate_val))
                if dec_rate <= 0:
                    continue

                # Locate or create ExchangeRate
                fx_record = (
                    db.query(ExchangeRate)
                    .filter(
                        ExchangeRate.base_currency == "USD",
                        ExchangeRate.target_currency == target_curr.upper(),
                    )
                    .order_by(ExchangeRate.fetched_at.desc())
                    .first()
                )

                if fx_record:
                    fx_record.rate = dec_rate
                    fx_record.source = "open.er-api.com"
                    fx_record.is_fallback = False
                    fx_record.fetched_at = now
                else:
                    fx_record = ExchangeRate(
                        base_currency="USD",
                        target_currency=target_curr.upper(),
                        rate=dec_rate,
                        source="open.er-api.com",
                        is_fallback=False,
                        fetched_at=now,
                    )
                    db.add(fx_record)

                stored_rates.append(fx_record)
            except Exception as ex:
                continue

        db.commit()
        logger.info("Successfully refreshed %d foreign exchange rates.", len(stored_rates))
        return stored_rates

    @classmethod
    def get_rate(
        cls,
        db: Session,
        from_currency: str,
        to_currency: str,
    ) -> Tuple[Decimal, str, bool, datetime]:
        """Retrieves cross exchange rate between two currencies.

        Returns:
            (rate_multiplier, rate_source, is_fallback, fetched_at)
        """
        from_c = from_currency.strip().upper()
        to_c = to_currency.strip().upper()
        now = datetime.now(timezone.utc)

        # 1. Identity conversion
        if from_c == to_c:
            return Decimal("1.000000"), "identity", False, now

        # 2. Query rates from USD base
        rate_from = (
            db.query(ExchangeRate)
            .filter(ExchangeRate.base_currency == "USD", ExchangeRate.target_currency == from_c)
            .order_by(ExchangeRate.fetched_at.desc())
            .first()
        )
        rate_to = (
            db.query(ExchangeRate)
            .filter(ExchangeRate.base_currency == "USD", ExchangeRate.target_currency == to_c)
            .order_by(ExchangeRate.fetched_at.desc())
            .first()
        )

        # Baseline fallback defaults if DB is uninitialized for currency
        default_fallback_rates = {
            "USD": Decimal("1.000000"),
            "EUR": Decimal("0.920000"),
            "GBP": Decimal("0.785000"),
            "INR": Decimal("83.500000"),
            "JPY": Decimal("152.400000"),
            "CAD": Decimal("1.360000"),
            "AUD": Decimal("1.520000"),
        }

        usd_to_from = rate_from.rate if rate_from else default_fallback_rates.get(from_c, Decimal("1.000000"))
        usd_to_to = rate_to.rate if rate_to else default_fallback_rates.get(to_c, Decimal("1.000000"))

        is_fallback = False
        source = "open.er-api.com"
        fetched_at = now

        if rate_from and rate_to:
            is_fallback = rate_from.is_fallback or rate_to.is_fallback
            source = rate_to.source
            fetched_at = min(rate_from.fetched_at, rate_to.fetched_at)
        else:
            is_fallback = True
            source = "static_baseline_snapshot"

        # Ensure fetched_at is timezone-aware for comparison
        if fetched_at.tzinfo is None:
            fetched_at_aware = fetched_at.replace(tzinfo=timezone.utc)
        else:
            fetched_at_aware = fetched_at

        # Check for staleness (> 24 hours)
        if (now - fetched_at_aware) > timedelta(hours=24):
            is_fallback = True

        # Cross-rate: R(from -> to) = R(USD -> to) / R(USD -> from)
        cross_rate = usd_to_to / usd_to_from
        return Decimal(f"{cross_rate:.6f}"), source, is_fallback, fetched_at

    @classmethod
    def list_cached_rates(cls, db: Session) -> List[ExchangeRateResponse]:
        """Lists all cached exchange rates with freshness status."""
        records = (
            db.query(ExchangeRate)
            .filter(ExchangeRate.base_currency == "USD")
            .order_by(ExchangeRate.target_currency.asc())
            .all()
        )
        return [
            ExchangeRateResponse(
                base_currency=r.base_currency,
                target_currency=r.target_currency,
                rate=r.rate,
                source=r.source,
                is_fallback=r.is_fallback,
                fetched_at=r.fetched_at,
            )
            for r in records
        ]
