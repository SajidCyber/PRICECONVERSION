"""Integration tests for DataIngestionService (CSV & JSON imports)."""

from decimal import Decimal
import pytest
from app.core.database import SessionLocal
from app.core.db_init import init_db
from app.core.exceptions import DataIngestionError
from app.models import DataImportBatch, PriceObservation, Product, ProductListing
from app.services.ingestion.importer import DataIngestionService


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    yield


def test_import_valid_csv():
    """Verify importing valid CSV records creates products, listings, observations, and batch record."""
    csv_data = """title,price,currency,marketplace_id,external_id,brand,category,shipping_price
Logitech MX Master 3S Wireless Mouse,99.99,USD,amazon_us,LOGI-MX3S-US,Logitech,Electronics,0.00
Logitech MX Master 3S Wireless Mouse,89.99,GBP,amazon_uk,LOGI-MX3S-UK,Logitech,Electronics,4.99
Logitech MX Master 3S Wireless Mouse,8495.00,INR,flipkart_in,LOGI-MX3S-IN,Logitech,Electronics,0.00
"""
    with SessionLocal() as db:
        summary = DataIngestionService.import_csv(
            db=db,
            csv_content=csv_data,
            source_name="test_logitech.csv",
        )

        assert summary.record_count == 3
        assert summary.inserted_count == 3
        assert summary.duplicate_count == 0
        assert summary.rejected_count == 0

        # Verify DB records
        batch = db.query(DataImportBatch).filter(DataImportBatch.id == summary.batch_id).first()
        assert batch is not None
        assert batch.inserted_count == 3

        # Verify listings
        listing_us = db.query(ProductListing).filter(ProductListing.external_id == "LOGI-MX3S-US").first()
        assert listing_us is not None
        assert listing_us.currency_code == "USD"
        assert len(listing_us.observations) >= 1
        assert listing_us.observations[0].listed_price == Decimal("99.99")


def test_import_csv_missing_mandatory_columns():
    """Verify CSV with missing mandatory column raises DataIngestionError."""
    invalid_csv = """title,price,brand
Incomplete Row Product,49.99,BrandX
"""
    with SessionLocal() as db:
        with pytest.raises(DataIngestionError) as exc_info:
            DataIngestionService.import_csv(db=db, csv_content=invalid_csv)
        assert "missing mandatory columns" in str(exc_info.value)


def test_import_csv_with_malformed_and_duplicate_rows():
    """Verify handling of invalid prices and duplicate observations in same batch."""
    csv_data = """title,price,currency,marketplace_id,external_id
Valid Item 1,29.99,USD,amazon_us,VAL-001
Invalid Price Item,FREE,USD,amazon_us,INV-002
Duplicate Item,49.99,USD,amazon_us,DUP-003
Duplicate Item,49.99,USD,amazon_us,DUP-003
"""
    with SessionLocal() as db:
        summary = DataIngestionService.import_csv(
            db=db,
            csv_content=csv_data,
            source_name="test_duplicates.csv",
        )

        assert summary.record_count == 4
        assert summary.inserted_count == 2
        assert summary.duplicate_count == 1
        assert summary.rejected_count == 1
        assert len(summary.summary_log["rejections"]) >= 1


def test_import_json_records():
    """Verify importing JSON product records."""
    json_data = [
        {
            "title": "Bose QuietComfort 45 Headphones",
            "price": "279.00",
            "currency": "USD",
            "marketplace_id": "amazon_us",
            "external_id": "BOSE-QC45-US",
            "brand": "Bose",
            "category": "Electronics",
        },
        {
            "title": "Bose QuietComfort 45 Headphones",
            "price": "229.00",
            "currency": "GBP",
            "marketplace_id": "amazon_uk",
            "external_id": "BOSE-QC45-UK",
            "brand": "Bose",
            "category": "Electronics",
        },
    ]
    with SessionLocal() as db:
        summary = DataIngestionService.import_json(
            db=db,
            json_content=json_data,
            source_name="test_bose.json",
        )

        assert summary.record_count == 2
        assert summary.inserted_count == 2
        assert summary.duplicate_count == 0
