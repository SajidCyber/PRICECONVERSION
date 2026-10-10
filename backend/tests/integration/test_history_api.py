"""Integration tests for Price History & Time-Series Analytics API."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.main import app
from app.models import PriceObservation, Product, ProductListing

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_get_product_price_history_api():
    """Verify GET /api/v1/pricing/history/{product_id} returns time series and statistics."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        assert product is not None
        product_id = product.id

    response = client.get(f"/api/v1/pricing/history/{product_id}?reporting_currency=USD&days=30")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    assert data["product_id"] == product_id
    assert data["reporting_currency"] == "USD"
    assert data["marketplaces_tracked"] >= 2
    assert data["total_observations"] >= 2
    assert len(data["listings_history"]) >= 2
    assert len(data["timeline_series"]) >= 1

    # Verify listing history stats
    first_listing = data["listings_history"][0]
    assert "stats" in first_listing
    stats = first_listing["stats"]
    assert float(stats["current_price"]) > 0
    assert float(stats["min_price"]) > 0
    assert float(stats["max_price"]) >= float(stats["min_price"])
    assert stats["observation_count"] >= 1
    assert "freshness_status" in stats


def test_get_product_history_with_currency_conversion():
    """Verify historical time series converted into custom reporting currency (e.g. EUR)."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        product_id = product.id

    response = client.get(f"/api/v1/pricing/history/{product_id}?reporting_currency=EUR&days=30")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["reporting_currency"] == "EUR"
    for listing in data["listings_history"]:
        for point in listing["price_points"]:
            assert point["reporting_currency"] == "EUR"
            assert float(point["converted_price"]) > 0


def test_get_product_history_multi_point_evolution():
    """Add sequential historical price points and verify trend deltas and volatility calculations."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        product_id = product.id
        listing = db.query(ProductListing).filter(ProductListing.product_id == product_id).first()
        assert listing is not None
        listing_id = listing.id
        listing_currency = listing.currency_code

        # Insert 3 spaced price observations for this listing
        obs1 = PriceObservation(
            listing_id=listing_id,
            listed_price=Decimal("1500.00"),
            currency_code=listing_currency,
            observed_at=now - timedelta(days=5),
            data_provenance="test_history",
        )
        obs2 = PriceObservation(
            listing_id=listing_id,
            listed_price=Decimal("1450.00"),
            currency_code=listing_currency,
            observed_at=now - timedelta(days=3),
            data_provenance="test_history",
        )
        obs3 = PriceObservation(
            listing_id=listing_id,
            listed_price=Decimal("1400.00"),
            currency_code=listing_currency,
            observed_at=now - timedelta(days=1),
            data_provenance="test_history",
        )
        db.add_all([obs1, obs2, obs3])
        db.commit()

    response = client.get(f"/api/v1/pricing/history/{product_id}?reporting_currency=USD&days=10")
    assert response.status_code == 200
    data = response.json()["data"]

    target_listing = next(l for l in data["listings_history"] if l["listing_id"] == listing_id)
    stats = target_listing["stats"]

    # Current price is latest (obs3 or seeded)
    assert stats["observation_count"] >= 4
    assert float(stats["min_price"]) <= 1400.00
    assert float(stats["max_price"]) >= 1500.00
    assert float(stats["volatility"]) > 0.0


def test_get_product_history_not_found():
    """Verify 404 response for nonexistent product ID."""
    response = client.get("/api/v1/pricing/history/nonexistent_uuid")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert "not found" in body["error"]["message"].lower()
