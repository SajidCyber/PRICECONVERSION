"""Integration tests for Product Matching REST API."""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.main import app
from app.models import Product, ProductListing, ProductMatch

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_list_matching_pairs():
    """Verify GET /api/v1/matching/pairs returns seeded matches with evidence breakdown."""
    response = client.get("/api/v1/matching/pairs")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    matches = body["data"]
    assert len(matches) >= 1

    first_match = matches[0]
    assert "product_id" in first_match
    assert "listing_id" in first_match
    assert "confidence_score" in first_match
    assert "match_evidence" in first_match
    assert first_match["status"] in {"confirmed", "probable", "uncertain"}


def test_filter_matching_pairs():
    """Verify filtering matches by min_confidence and status."""
    # Filter by confirmed status
    resp_conf = client.get("/api/v1/matching/pairs?status=confirmed")
    assert resp_conf.status_code == 200
    for item in resp_conf.json()["data"]:
        assert item["status"] == "confirmed"

    # Filter by min_confidence
    resp_score = client.get("/api/v1/matching/pairs?min_confidence=90.0")
    assert resp_score.status_code == 200
    for item in resp_score.json()["data"]:
        assert float(item["confidence_score"]) >= 90.0


def test_run_batch_matching_endpoint():
    """Verify POST /api/v1/matching/run triggers batch matching."""
    response = client.post("/api/v1/matching/run")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    summary = body["data"]
    assert summary["total_listings_inspected"] >= 1
    assert "confirmed_count" in summary
    assert "execution_time_ms" in summary


def test_update_and_delete_match_review():
    """Verify PATCH /api/v1/matching/pairs/{id} and DELETE endpoints."""
    import uuid
    uid = str(uuid.uuid4())[:8]

    with SessionLocal() as db:
        # Create an isolated test match record
        test_prod = Product(
            sku=f"TEST-ISO-{uid}",
            title=f"Isolated Test Product {uid}",
            brand="TestBrand",
            category="Test",
        )
        db.add(test_prod)
        db.flush()

        test_listing = ProductListing(
            product_id=test_prod.id,
            marketplace_id="amazon_us",
            external_id=f"TEST-LISTING-{uid}",
            listing_title=f"Isolated Test Product Listing {uid}",
            listing_url=f"https://amazon.com/dp/TEST-{uid}",
            currency_code="USD",
        )
        db.add(test_listing)
        db.flush()

        match = ProductMatch(
            product_id=test_prod.id,
            listing_id=test_listing.id,
            confidence_score=Decimal("88.50"),
            match_type="token_cosine",
            status="confirmed",
            match_evidence={"test": True},
        )
        db.add(match)
        db.commit()
        match_id = match.id

    # 1. Update status to 'probable'
    patch_resp = client.patch(
        f"/api/v1/matching/pairs/{match_id}",
        json={"status": "probable", "notes": "Manually reviewed by operator"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "probable"

    # 2. Update status to 'rejected'
    reject_resp = client.patch(
        f"/api/v1/matching/pairs/{match_id}",
        json={"status": "rejected"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["data"]["status"] == "rejected"

    # 3. Delete match
    del_resp = client.delete(f"/api/v1/matching/pairs/{match_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["deleted_match_id"] == match_id
