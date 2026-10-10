"""Integration tests for Scraping and Ingestion REST API Endpoints."""

import io
from unittest.mock import AsyncMock, patch
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.main import app
from app.schemas.scraper import ExtractedProductDTO

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_list_scraper_adapters():
    """Verify GET /api/v1/scraping/adapters returns registered adapters."""
    response = client.get("/api/v1/scraping/adapters")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    adapters = body["data"]
    adapter_ids = [a["marketplace_id"] for a in adapters]
    assert "books_to_scrape" in adapter_ids
    assert "dummyjson_store" in adapter_ids
    assert "fakestore" in adapter_ids


@pytest.mark.asyncio
async def test_trigger_and_query_scraping_job():
    """Verify POST /api/v1/scraping/jobs and GET /api/v1/scraping/jobs/{id}."""
    mock_items = [
        ExtractedProductDTO(
            external_id="MOCK-BOOK-1",
            title="The Art of Software Testing",
            url="https://books.toscrape.com/mock-1",
            price=Decimal("42.50"),
            currency_code="GBP",
            availability_status="in_stock",
            rating=Decimal("5.0"),
            data_provenance="live_scrape",
        )
    ]

    with patch("app.services.scraper.books_adapter.BooksToScrapeAdapter.fetch_catalog", new=AsyncMock(return_value=mock_items)):
        # Trigger scraping job
        payload = {
            "marketplace_id": "books_to_scrape",
            "category": "science",
            "max_items": 5,
        }
        create_resp = client.post("/api/v1/scraping/jobs", json=payload)
        assert create_resp.status_code == 201
        job_data = create_resp.json()["data"]
        job_id = job_data["id"]
        assert job_data["marketplace_id"] == "books_to_scrape"
        assert job_data["status"] == "success"
        assert job_data["items_extracted"] == 1

        # Query job by ID
        get_resp = client.get(f"/api/v1/scraping/jobs/{job_id}")
        assert get_resp.status_code == 200
        fetched_job = get_resp.json()["data"]
        assert fetched_job["id"] == job_id
        assert fetched_job["items_extracted"] == 1


def test_upload_csv_endpoint():
    """Verify POST /api/v1/ingestion/upload-csv processes multipart file."""
    csv_content = """title,price,currency,marketplace_id,external_id
Anker 737 Power Bank 24000mAh,149.99,USD,amazon_us,ANK-737-US
Anker 737 Power Bank 24000mAh,129.99,GBP,amazon_uk,ANK-737-UK
"""
    file_payload = {"file": ("test_anker.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/ingestion/upload-csv", files=file_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["inserted_count"] == 2
    assert body["data"]["source_name"] == "test_anker.csv"


def test_list_import_batches_endpoint():
    """Verify GET /api/v1/ingestion/batches returns batch history."""
    response = client.get("/api/v1/ingestion/batches")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) >= 1
    assert "total" in body["meta"]
