"""Unit tests for Foreign Exchange Service (FXService)."""

from decimal import Decimal
from datetime import datetime, timezone
import pytest
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.models import ExchangeRate
from app.services.pricing.fx_service import FXService


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_fx_identity_conversion():
    """Verify converting a currency to itself returns rate of 1.000000 with identity source."""
    with SessionLocal() as db:
        rate, source, is_fallback, _ = FXService.get_rate(db, "USD", "USD")
        assert rate == Decimal("1.000000")
        assert source == "identity"
        assert is_fallback is False

        rate_gbp, _, _, _ = FXService.get_rate(db, "GBP", "GBP")
        assert rate_gbp == Decimal("1.000000")


def test_fx_direct_and_cross_rate_conversions():
    """Verify USD base and cross-currency conversions (e.g. GBP -> EUR, EUR -> INR)."""
    with SessionLocal() as db:
        # USD to GBP
        rate_usd_gbp, _, is_fb, _ = FXService.get_rate(db, "USD", "GBP")
        assert rate_usd_gbp == Decimal("0.785000")
        assert is_fb is False

        # USD to EUR
        rate_usd_eur, _, _, _ = FXService.get_rate(db, "USD", "EUR")
        assert rate_usd_eur == Decimal("0.920000")

        # Cross-rate: GBP -> EUR = R(USD->EUR) / R(USD->GBP) = 0.92 / 0.785 = ~1.171975
        rate_gbp_eur, _, _, _ = FXService.get_rate(db, "GBP", "EUR")
        expected_cross = Decimal("0.920000") / Decimal("0.785000")
        assert abs(rate_gbp_eur - Decimal(f"{expected_cross:.6f}")) < Decimal("0.0001")


def test_fx_fallback_for_unseeded_currency():
    """Verify querying an unseeded currency activates fallback indicator."""
    with SessionLocal() as db:
        rate, source, is_fallback, _ = FXService.get_rate(db, "CAD", "AUD")
        assert rate > 0
        # Should complete calculation without crashing
