"""Integration Tests for Database Schema, Entity Models, Constraints, and Seeding."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.core.database import Base, SessionLocal, engine
from app.core.db_init import init_db, seed_initial_data
from app.models import (
    Country,
    Marketplace,
    Product,
    ProductListing,
    PriceObservation,
    ProductMatch,
    ExchangeRate,
    LandedCostConfig,
    PriceAlert,
    AlertNotification,
    ScrapingJob,
    DataImportBatch,
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Initializes and seeds database for tests."""
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_seeded_countries_and_marketplaces():
    """Verify seeded countries and marketplaces exist with relationships."""
    with SessionLocal() as db:
        us = db.query(Country).filter(Country.id == "US").first()
        assert us is not None
        assert us.currency_code == "USD"
        assert len(us.marketplaces) >= 1

        gb = db.query(Country).filter(Country.id == "GB").first()
        assert gb is not None
        assert gb.currency_code == "GBP"

        # Verify books_to_scrape marketplace
        books_market = db.query(Marketplace).filter(Marketplace.id == "books_to_scrape").first()
        assert books_market is not None
        assert books_market.country_id == "GB"
        assert books_market.currency_code == "GBP"


def test_canonical_product_and_listings_hierarchy():
    """Verify canonical product has related listings, matches, and observations."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        assert product is not None
        assert product.brand == "Apple"

        # Ensure listings are associated
        listings = db.query(ProductListing).filter(
            ProductListing.external_id.in_(["B0CM5JV5N5", "B0CM5JV5N5_UK", "FLIP_MBP14_M3_512"])
        ).all()
        for l in listings:
            l.product_id = product.id
        db.commit()
        db.refresh(product)

        assert len(product.listings) >= 3

        # Verify listings across US, UK, and IN
        marketplace_ids = [l.marketplace_id for l in product.listings]
        assert "amazon_us" in marketplace_ids
        assert "amazon_uk" in marketplace_ids
        assert "flipkart_in" in marketplace_ids

        # Verify matches
        assert len(product.matches) >= 3
        for match in product.matches:
            assert match.status in {"confirmed", "probable"}
            assert match.confidence_score >= Decimal("70.00")


def test_price_observations_immutability_and_history():
    """Verify multiple price observations for a listing are preserved sequentially."""
    with SessionLocal() as db:
        listing = db.query(ProductListing).filter(ProductListing.external_id == "B0CM5JV5N5").first()
        assert listing is not None
        initial_obs_count = len(listing.observations)
        assert initial_obs_count >= 1

        # Add a new historical price observation
        new_obs = PriceObservation(
            listing_id=listing.id,
            listed_price=Decimal("1499.00"),  # Price drop
            currency_code="USD",
            shipping_price=Decimal("0.00"),
            discount_pct=Decimal("6.25"),
            availability_status="in_stock",
            data_provenance="live_scrape",
            observed_at=datetime.now(timezone.utc),
        )
        db.add(new_obs)
        db.commit()

        # Query again and verify history is intact
        db.refresh(listing)
        assert len(listing.observations) == initial_obs_count + 1
        prices = [obs.listed_price for obs in listing.observations]
        assert Decimal("1549.00") in prices
        assert Decimal("1499.00") in prices


def test_unique_constraint_on_listing_marketplace_external_id():
    """Verify duplicate (marketplace_id, external_id) causes IntegrityError."""
    with SessionLocal() as db:
        duplicate_listing = ProductListing(
            marketplace_id="amazon_us",
            external_id="B0CM5JV5N5",  # Already exists
            listing_title="Duplicate Attempt",
            listing_url="https://www.amazon.com/dp/B0CM5JV5N5",
            currency_code="USD",
        )
        db.add(duplicate_listing)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_unique_constraint_on_landed_cost_config():
    """Verify duplicate (country_id, category) causes IntegrityError."""
    with SessionLocal() as db:
        duplicate_config = LandedCostConfig(
            country_id="US",
            category="*",  # Already exists
            customs_duty_rate=Decimal("0.05"),
        )
        db.add(duplicate_config)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_scraping_job_and_import_batch_models():
    """Verify ScrapingJob and DataImportBatch creation and status tracking."""
    with SessionLocal() as db:
        job = ScrapingJob(
            marketplace_id="books_to_scrape",
            status="success",
            target_category="science",
            items_discovered=20,
            items_extracted=20,
            error_count=0,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        assert job.id is not None
        assert job.status == "success"

        batch = DataImportBatch(
            source_name="kaggle_crossborder_sample.csv",
            source_type="imported_dataset",
            record_count=100,
            inserted_count=98,
            duplicate_count=2,
            rejected_count=0,
            summary_log={"status": "completed"},
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        assert batch.id is not None
        assert batch.inserted_count == 98
