"""Unit tests for Landed Cost Mathematical Formulas and De Minimis Exemptions."""

from decimal import Decimal
import pytest
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.services.pricing.landed_cost import LandedCostService


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_landed_cost_below_de_minimis_exemption():
    """Verify items below de minimis threshold ($800 for US) incur zero customs duty."""
    with SessionLocal() as db:
        # $100 item imported to US (De minimis threshold is $800)
        breakdown = LandedCostService.calculate_landed_cost(
            db=db,
            price=Decimal("100.00"),
            source_currency="USD",
            destination_country_id="US",
            override_freight=Decimal("10.00"),
            override_insurance_rate=Decimal("0.0100"),  # $1.00
            override_handling_fee=Decimal("5.00"),
            override_tax_rate=Decimal("0.0800"),        # 8%
        )

        assert breakdown.converted_price == Decimal("100.00")
        assert breakdown.freight_fee == Decimal("10.00")
        assert breakdown.insurance_fee == Decimal("1.00")
        assert breakdown.cif_value == Decimal("111.00")

        # Below $800 -> Duty is $0.00
        assert breakdown.is_duty_exempt is True
        assert breakdown.customs_duty_amount == Decimal("0.00")

        # Tax Base = CIF + Duty = $111.00 -> Tax @ 8% = $8.88
        assert breakdown.tax_base_value == Decimal("111.00")
        assert breakdown.import_tax_amount == Decimal("8.88")

        # Total = $111.00 (CIF) + $0.00 (Duty) + $8.88 (Tax) + $5.00 (Handling) = $124.88
        assert breakdown.total_landed_cost == Decimal("124.88")
        assert breakdown.effective_markup_pct == Decimal("24.88")


def test_landed_cost_above_de_minimis_with_duty():
    """Verify high-value items incur both customs duty and import tax on (CIF + Duty)."""
    with SessionLocal() as db:
        # $1000 item imported to US (Above $800 threshold)
        breakdown = LandedCostService.calculate_landed_cost(
            db=db,
            price=Decimal("1000.00"),
            source_currency="USD",
            destination_country_id="US",
            override_freight=Decimal("20.00"),
            override_insurance_rate=Decimal("0.0100"),  # $10.00
            override_duty_rate=Decimal("0.0500"),       # 5%
            override_tax_rate=Decimal("0.1000"),        # 10%
            override_handling_fee=Decimal("5.00"),
        )

        assert breakdown.converted_price == Decimal("1000.00")
        assert breakdown.cif_value == Decimal("1030.00")  # 1000 + 20 + 10

        # Above $800 -> Duty = 1030 * 0.05 = $51.50
        assert breakdown.is_duty_exempt is False
        assert breakdown.customs_duty_amount == Decimal("51.50")

        # Tax Base = CIF + Duty = 1030 + 51.50 = $1081.50
        assert breakdown.tax_base_value == Decimal("1081.50")
        # Tax = 1081.50 * 0.10 = $108.15
        assert breakdown.import_tax_amount == Decimal("108.15")

        # Total = 1030 + 51.50 + 108.15 + 5.00 = $1194.65
        assert breakdown.total_landed_cost == Decimal("1194.65")
        assert breakdown.effective_markup_pct in {Decimal("19.46"), Decimal("19.47")}


def test_cross_currency_landed_cost():
    """Verify landed cost for foreign currency listing (e.g. £1449 GBP imported into US)."""
    with SessionLocal() as db:
        # £1449 GBP -> Converted to USD via rate ~1.273885 (1 / 0.785)
        breakdown = LandedCostService.calculate_landed_cost(
            db=db,
            price=Decimal("1449.00"),
            source_currency="GBP",
            destination_country_id="US",
        )

        assert breakdown.destination_currency == "USD"
        assert breakdown.original_currency == "GBP"
        assert breakdown.converted_price > Decimal("1800.00")
        assert breakdown.total_landed_cost > breakdown.converted_price
