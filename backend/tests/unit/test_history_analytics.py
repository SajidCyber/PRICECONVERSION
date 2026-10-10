"""Unit tests for Price History Tracking and Time-Series Analytics Service."""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pytest
from app.core.exceptions import EntityNotFoundError
from app.models import Country, ExchangeRate, Marketplace, PriceObservation, Product, ProductListing
from app.services.analytics.history_service import PriceHistoryService


def test_compute_stats_empty():
    """Verify compute_stats handles empty observation list gracefully."""
    stats = PriceHistoryService.compute_stats([])
    assert stats.observation_count == 0
    assert stats.current_price == Decimal("0.00")
    assert stats.min_price == Decimal("0.00")
    assert stats.max_price == Decimal("0.00")
    assert stats.avg_price == Decimal("0.00")
    assert stats.absolute_change == Decimal("0.00")
    assert stats.pct_change == Decimal("0.00")
    assert stats.volatility == Decimal("0.00")
    assert stats.freshness_status == "expired"


def test_compute_stats_single_observation():
    """Verify compute_stats handles single observation correctly."""
    now = datetime.now(timezone.utc)
    obs = PriceObservation(
        id=str(uuid.uuid4()),
        listing_id="list_1",
        listed_price=Decimal("199.99"),
        currency_code="USD",
        observed_at=now,
        availability_status="in_stock",
    )
    stats = PriceHistoryService.compute_stats([obs])
    assert stats.observation_count == 1
    assert stats.current_price == Decimal("199.99")
    assert stats.min_price == Decimal("199.99")
    assert stats.max_price == Decimal("199.99")
    assert stats.avg_price == Decimal("199.99")
    assert stats.absolute_change == Decimal("0.00")
    assert stats.pct_change == Decimal("0.00")
    assert stats.volatility == Decimal("0.00")
    assert stats.freshness_status == "fresh"


def test_compute_stats_multiple_series():
    """Verify statistical aggregates, volatility, and deltas across price changes."""
    t0 = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 10, 3, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)

    observations = [
        PriceObservation(id="1", listing_id="l1", listed_price=Decimal("100.00"), currency_code="USD", observed_at=t0),
        PriceObservation(id="2", listing_id="l1", listed_price=Decimal("120.00"), currency_code="USD", observed_at=t1),
        PriceObservation(id="3", listing_id="l1", listed_price=Decimal("80.00"), currency_code="USD", observed_at=t2),
        PriceObservation(id="4", listing_id="l1", listed_price=Decimal("110.00"), currency_code="USD", observed_at=t3),
    ]

    stats = PriceHistoryService.compute_stats(observations)
    assert stats.observation_count == 4
    assert stats.current_price == Decimal("110.00")
    assert stats.min_price == Decimal("80.00")
    assert stats.max_price == Decimal("120.00")
    assert stats.avg_price == Decimal("102.50")
    # Absolute change: 110 - 100 = 10.00
    assert stats.absolute_change == Decimal("10.00")
    # Pct change: ((110 - 100) / 100) * 100 = +10.00%
    assert stats.pct_change == Decimal("10.00")
    # Volatility should be standard deviation of [100, 120, 80, 110]
    # Mean = 102.5. Diff sq = (2.5)^2 + (17.5)^2 + (-22.5)^2 + (7.5)^2 = 6.25 + 306.25 + 506.25 + 56.25 = 875.
    # Variance = 875 / 3 = 291.6667. Sqrt(291.6667) = 17.08
    assert float(stats.volatility) == pytest.approx(17.08, abs=0.05)


def test_compute_stats_freshness_categories():
    """Verify freshness classification based on elapsed time."""
    now = datetime.now(timezone.utc)

    # Fresh (<24h)
    obs_fresh = [PriceObservation(id="1", listing_id="l1", listed_price=Decimal("10.00"), currency_code="USD", observed_at=now - timedelta(hours=6))]
    assert PriceHistoryService.compute_stats(obs_fresh).freshness_status == "fresh"

    # Stale (24h - 72h)
    obs_stale = [PriceObservation(id="2", listing_id="l1", listed_price=Decimal("10.00"), currency_code="USD", observed_at=now - timedelta(hours=48))]
    assert PriceHistoryService.compute_stats(obs_stale).freshness_status == "stale"

    # Expired (>72h)
    obs_expired = [PriceObservation(id="3", listing_id="l1", listed_price=Decimal("10.00"), currency_code="USD", observed_at=now - timedelta(hours=96))]
    assert PriceHistoryService.compute_stats(obs_expired).freshness_status == "expired"
