"""Integration tests for Market Positioning and Intelligence REST API."""

import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.main import app
from app.models import Product

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_get_product_positioning_api():
    """Verify GET /api/v1/intelligence/positioning returns strategic pricing insights."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        assert product is not None
        product_id = product.id

    response = client.get(f"/api/v1/intelligence/positioning?product_id={product_id}&destination_country=US&reporting_currency=USD")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    assert data["product_id"] == product_id
    assert data["destination_country"] == "US"
    assert data["reporting_currency"] == "USD"
    assert "strategic_recommendation" in data
    assert "market_competitiveness" in data
    assert "recommendation_reasoning" in data
    assert data["total_competitors"] >= 2
    assert len(data["rankings"]) >= 2

    # Check top ranked item
    top_rank = data["rankings"][0]
    assert top_rank["rank"] == 1
    assert top_rank["is_cheapest"] is True
    assert float(top_rank["landed_cost"]) > 0


def test_get_export_opportunities_api():
    """Verify GET /api/v1/intelligence/opportunities detects cross-border price arbitrage."""
    response = client.get("/api/v1/intelligence/opportunities?min_margin_pct=5.0&reporting_currency=USD")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    assert data["reporting_currency"] == "USD"
    assert "total_opportunities_found" in data
    assert isinstance(data["opportunities"], list)


def test_get_anomalies_api():
    """Verify GET /api/v1/intelligence/anomalies returns price anomaly events."""
    response = client.get("/api/v1/intelligence/anomalies?threshold_pct=15.0")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


def test_get_positioning_not_found():
    """Verify 404 response for invalid product UUID."""
    response = client.get("/api/v1/intelligence/positioning?product_id=unknown_uuid_123&destination_country=US")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert "not found" in body["error"]["message"].lower()
