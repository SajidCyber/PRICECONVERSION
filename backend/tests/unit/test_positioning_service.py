"""Unit tests for Market Positioning and Export Arbitrage Intelligence."""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pytest
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.models import Country, Marketplace, PriceObservation, Product, ProductListing
from app.services.analytics.positioning import MarketPositioningService


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_analyze_product_positioning_dominant_tier():
    """Verify strategic recommendation when our target price is significantly below competitor minimum."""
    with SessionLocal() as db:
        # Create a product with very low base price ($800 vs competitor $1500)
        u_id = uuid.uuid4().hex[:8]
        low_prod = Product(
            id=f"test_dom_{u_id}",
            sku=f"DOM-SKU-{u_id}",
            title="Dominant Market Laptop",
            category="Electronics",
            target_base_price=Decimal("800.00"),
            base_currency="USD",
        )
        db.add(low_prod)
        db.flush()

        listing1 = ProductListing(
            id=f"list_dom_{u_id}",
            product_id=low_prod.id,
            marketplace_id="amazon_us",
            currency_code="USD",
            listing_title="Dominant Laptop US Competitor",
            listing_url="https://amazon.com/dp/B0DOM1234",
            external_id=f"ext_dom_{u_id}",
        )
        db.add(listing1)
        db.flush()

        obs1 = PriceObservation(
            listing_id=listing1.id,
            listed_price=Decimal("1500.00"),
            currency_code="USD",
            observed_at=datetime.now(timezone.utc),
        )
        db.add(obs1)
        db.commit()

        analysis = MarketPositioningService.analyze_product_positioning(
            db=db,
            product_id=low_prod.id,
            destination_country_id="US",
            reporting_currency="USD",
        )

        assert analysis.product_id == low_prod.id
        assert analysis.market_competitiveness == "dominant"
        assert analysis.strategic_recommendation == "raise_price_to_maximize_margin"
        assert analysis.positioning_index is not None
        assert float(analysis.positioning_index) < 0.90
        assert analysis.total_competitors == 1
        assert len(analysis.rankings) == 1


def test_analyze_product_positioning_uncompetitive_tier():
    """Verify strategic recommendation when our target price is higher than market median."""
    with SessionLocal() as db:
        u_id = uuid.uuid4().hex[:8]
        high_prod = Product(
            id=f"test_uncomp_{u_id}",
            sku=f"UNCOMP-SKU-{u_id}",
            title="Overpriced Laptop",
            category="Electronics",
            target_base_price=Decimal("2200.00"),
            base_currency="USD",
        )
        db.add(high_prod)
        db.flush()

        listing1 = ProductListing(
            id=f"list_uncomp_{u_id}",
            product_id=high_prod.id,
            marketplace_id="amazon_us",
            currency_code="USD",
            listing_title="Market Competitor",
            listing_url="https://amazon.com/dp/B0UNCOMP12",
            external_id=f"ext_uncomp_{u_id}",
        )
        db.add(listing1)
        db.flush()

        obs1 = PriceObservation(
            listing_id=listing1.id,
            listed_price=Decimal("1500.00"),
            currency_code="USD",
            observed_at=datetime.now(timezone.utc),
        )
        db.add(obs1)
        db.commit()

        analysis = MarketPositioningService.analyze_product_positioning(
            db=db,
            product_id=high_prod.id,
            destination_country_id="US",
            reporting_currency="USD",
        )

        assert analysis.market_competitiveness == "uncompetitive"
        assert analysis.strategic_recommendation == "lower_price_to_compete"
        assert float(analysis.price_gap_vs_median_pct) > 0.0


def test_detect_anomalies_unit():
    """Verify detection of price drop and price spike events with severity flags."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        u_id = uuid.uuid4().hex[:8]
        prod = Product(
            id=f"test_anom_{u_id}",
            sku=f"ANOM-SKU-{u_id}",
            title="Anomaly Test Item",
            category="Electronics",
        )
        db.add(prod)
        db.flush()

        listing = ProductListing(
            id=f"list_anom_{u_id}",
            product_id=prod.id,
            marketplace_id="amazon_us",
            currency_code="USD",
            listing_title="Anomaly Listing",
            listing_url="https://amazon.com/dp/B0ANOM999",
            external_id=f"ext_anom_{u_id}",
        )
        db.add(listing)
        db.flush()

        # Add 35% flash price drop
        obs1 = PriceObservation(
            listing_id=listing.id,
            listed_price=Decimal("100.00"),
            currency_code="USD",
            observed_at=now - timedelta(days=2),
        )
        obs2 = PriceObservation(
            listing_id=listing.id,
            listed_price=Decimal("60.00"),
            currency_code="USD",
            observed_at=now - timedelta(days=1),
        )
        db.add_all([obs1, obs2])
        db.commit()

        anomalies = MarketPositioningService.detect_anomalies(
            db=db,
            product_id=prod.id,
            threshold_pct=Decimal("15.0"),
        )

        assert len(anomalies) >= 1
        anom = anomalies[0]
        assert anom.anomaly_type == "price_drop"
        assert anom.severity == "critical"  # >= 30% drop
        assert float(anom.pct_change) == pytest.approx(-40.0, abs=0.5)


def test_detect_export_opportunities_unit():
    """Verify detection of cross-border price arbitrage opportunities."""
    with SessionLocal() as db:
        # Check existing seeded catalog (e.g. MacBook Pro across US and UK/DE)
        opps_resp = MarketPositioningService.detect_export_opportunities(
            db=db,
            min_margin_pct=Decimal("5.0"),
            reporting_currency="USD",
        )

        assert opps_resp.reporting_currency == "USD"
        assert isinstance(opps_resp.opportunities, list)
        for opp in opps_resp.opportunities:
            assert opp.net_margin_pct >= Decimal("5.0")
            assert opp.opportunity_score >= 0.0
            assert opp.feasibility_rating in ["high", "medium", "low"]
            assert opp.source_country != opp.target_country
