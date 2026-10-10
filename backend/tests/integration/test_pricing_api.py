"""Integration tests for Pricing & Landed Cost REST API."""

from decimal import Decimal
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


def test_get_exchange_rates_api():
    """Verify GET /api/v1/pricing/exchange-rates returns cached currency rates."""
    response = client.get("/api/v1/pricing/exchange-rates")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    rates = body["data"]
    assert len(rates) >= 5
    currencies = [r["target_currency"] for r in rates]
    assert "EUR" in currencies
    assert "GBP" in currencies
    assert "INR" in currencies


def test_product_price_comparison_matrix_api():
    """Verify GET /api/v1/pricing/comparison returns full multi-market matrix."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        assert product is not None
        product_id = product.id

    response = client.get(f"/api/v1/pricing/comparison?product_id={product_id}&destination_country=US")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    assert data["product_id"] == product_id
    assert data["destination_country"] == "US"
    assert data["reporting_currency"] == "USD"
    assert len(data["listings"]) >= 2

    # Check breakdown in first listing
    first_listing = data["listings"][0]
    assert "breakdown" in first_listing
    assert "total_landed_cost" in first_listing["breakdown"]
    assert "cif_value" in first_listing["breakdown"]
    assert first_listing["breakdown"]["destination_currency"] == "USD"


def test_simulate_landed_cost_api():
    """Verify POST /api/v1/pricing/landed-cost/calculate performs custom scenario math."""
    payload = {
        "price": 1200.00,
        "source_currency": "USD",
        "destination_country": "US",
        "override_freight": 25.00,
        "override_duty_rate": 0.05,
        "override_tax_rate": 0.08,
        "override_insurance_rate": 0.01,
        "override_handling_fee": 10.00,
    }
    response = client.post("/api/v1/pricing/landed-cost/calculate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    # Converted = 1200.00, Ins = 12.00, Freight = 25.00 -> CIF = 1237.00
    # Duty = 1237 * 0.05 = 61.85
    # Tax = (1237 + 61.85) * 0.08 = 103.91
    # Total = 1237 + 61.85 + 103.91 + 10 = 1412.76
    assert float(data["total_landed_cost"]) == pytest.approx(1412.76, abs=0.05)
    assert data["destination_currency"] == "USD"


def test_get_and_update_landed_cost_configs_api():
    """Verify GET and PUT /api/v1/pricing/configs."""
    # List configs
    list_resp = client.get("/api/v1/pricing/configs")
    assert list_resp.status_code == 200
    configs = list_resp.json()["data"]
    assert len(configs) >= 4

    # Update config for US
    update_payload = {
        "customs_duty_rate": 0.045,
        "import_tax_rate": 0.085,
        "default_freight": 18.00,
    }
    put_resp = client.put("/api/v1/pricing/configs/US?category=*", json=update_payload)
    assert put_resp.status_code == 200
    updated = put_resp.json()["data"]
    assert float(updated["customs_duty_rate"]) == pytest.approx(0.045)
    assert float(updated["import_tax_rate"]) == pytest.approx(0.085)
    assert float(updated["default_freight"]) == pytest.approx(18.00)
