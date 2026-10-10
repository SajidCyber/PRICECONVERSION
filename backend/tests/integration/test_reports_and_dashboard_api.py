"""Integration tests for Reports Export & Dashboard Summary REST API."""

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


def test_export_comparison_matrix_csv_endpoint():
    """Verify GET /api/v1/reports/export/comparison/csv returns downloadable CSV stream."""
    response = client.get("/api/v1/reports/export/comparison/csv?destination_country=US&reporting_currency=USD")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert len(response.text) > 50
    assert "Product SKU" in response.text
    assert "Total Landed Cost" in response.text


def test_export_product_history_csv_endpoint():
    """Verify GET /api/v1/reports/export/history/{product_id}/csv returns time-series CSV."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        assert product is not None
        product_id = product.id

    response = client.get(f"/api/v1/reports/export/history/{product_id}/csv?reporting_currency=USD&days=30")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Product SKU" in response.text
    assert "Listed Price" in response.text


def test_export_opportunities_csv_endpoint():
    """Verify GET /api/v1/reports/export/opportunities/csv returns arbitrage opportunities CSV."""
    response = client.get("/api/v1/reports/export/opportunities/csv?min_margin_pct=5.0&reporting_currency=USD")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Source Marketplace" in response.text


def test_get_dashboard_summary_endpoint():
    """Verify GET /api/v1/dashboard/summary returns consolidated KPI metrics."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    assert data["total_products"] >= 2
    assert data["total_marketplaces"] >= 5
    assert data["total_listings"] >= 4
    assert data["total_observations"] >= 4
    assert "scraping_health" in data
    assert "recent_activities" in data
    assert isinstance(data["recent_activities"], list)
