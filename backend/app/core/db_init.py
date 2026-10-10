"""Database schema initialization and standard initial dataset seeding."""

from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.core.logging_config import logger
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
)


def init_db() -> None:
    """Creates all database tables defined in the metadata."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def seed_initial_data(db: Session) -> None:
    """Seeds baseline geographic markets, marketplaces, landed-cost rules, and reference catalog."""

    # 1. Seed Countries
    if not db.query(Country).first():
        logger.info("Seeding initial countries...")
        countries = [
            Country(id="US", name="United States", currency_code="USD", currency_symbol="$", region="North America"),
            Country(id="GB", name="United Kingdom", currency_code="GBP", currency_symbol="£", region="Europe"),
            Country(id="IN", name="India", currency_code="INR", currency_symbol="₹", region="Asia-Pacific"),
            Country(id="DE", name="Germany", currency_code="EUR", currency_symbol="€", region="Europe"),
            Country(id="JP", name="Japan", currency_code="JPY", currency_symbol="¥", region="Asia-Pacific"),
        ]
        db.add_all(countries)
        db.commit()

    # 2. Seed Marketplaces
    if not db.query(Marketplace).first():
        logger.info("Seeding initial marketplaces...")
        marketplaces = [
            Marketplace(
                id="amazon_us",
                name="Amazon US",
                country_id="US",
                base_url="https://www.amazon.com",
                adapter_name="generic_structured",
                currency_code="USD",
            ),
            Marketplace(
                id="amazon_uk",
                name="Amazon UK",
                country_id="GB",
                base_url="https://www.amazon.co.uk",
                adapter_name="generic_structured",
                currency_code="GBP",
            ),
            Marketplace(
                id="flipkart_in",
                name="Flipkart India",
                country_id="IN",
                base_url="https://www.flipkart.com",
                adapter_name="generic_structured",
                currency_code="INR",
            ),
            Marketplace(
                id="books_to_scrape",
                name="Books To Scrape Sandbox",
                country_id="GB",
                base_url="https://books.toscrape.com",
                adapter_name="books_to_scrape",
                currency_code="GBP",
            ),
            Marketplace(
                id="dummyjson_store",
                name="DummyJSON Catalog Feed",
                country_id="US",
                base_url="https://dummyjson.com",
                adapter_name="dummyjson",
                currency_code="USD",
            ),
            Marketplace(
                id="fakestore",
                name="FakeStore Public API",
                country_id="US",
                base_url="https://fakestoreapi.com",
                adapter_name="fakestore",
                currency_code="USD",
            ),
        ]
        db.add_all(marketplaces)
        db.commit()

    # 3. Seed Landed Cost Assumptions per Country
    if not db.query(LandedCostConfig).first():
        logger.info("Seeding initial landed-cost trade parameters...")
        configs = [
            LandedCostConfig(
                country_id="US",
                category="*",
                customs_duty_rate=Decimal("0.0350"),  # 3.5% avg duty
                import_tax_rate=Decimal("0.0700"),    # 7.0% avg state sales tax
                de_minimis_threshold=Decimal("800.00"),  # Section 321 de minimis
                default_freight=Decimal("15.00"),
                insurance_rate=Decimal("0.0100"),
                handling_fee=Decimal("5.00"),
            ),
            LandedCostConfig(
                country_id="GB",
                category="*",
                customs_duty_rate=Decimal("0.0400"),  # 4.0% UK tariff
                import_tax_rate=Decimal("0.2000"),    # 20.0% UK VAT
                de_minimis_threshold=Decimal("135.00"),  # £135 threshold
                default_freight=Decimal("20.00"),
                insurance_rate=Decimal("0.0100"),
                handling_fee=Decimal("8.00"),
            ),
            LandedCostConfig(
                country_id="IN",
                category="*",
                customs_duty_rate=Decimal("0.1000"),  # 10.0% Basic Customs Duty
                import_tax_rate=Decimal("0.1800"),    # 18.0% IGST
                de_minimis_threshold=Decimal("0.00"), # Strict duty enforcement
                default_freight=Decimal("25.00"),
                insurance_rate=Decimal("0.0150"),
                handling_fee=Decimal("10.00"),
            ),
            LandedCostConfig(
                country_id="DE",
                category="*",
                customs_duty_rate=Decimal("0.0450"),  # 4.5% EU external tariff
                import_tax_rate=Decimal("0.1900"),    # 19.0% German MwSt
                de_minimis_threshold=Decimal("150.00"),  # €150 EU customs de minimis
                default_freight=Decimal("18.00"),
                insurance_rate=Decimal("0.0100"),
                handling_fee=Decimal("6.00"),
            ),
            LandedCostConfig(
                country_id="JP",
                category="*",
                customs_duty_rate=Decimal("0.0300"),  # 3.0% Japan tariff
                import_tax_rate=Decimal("0.1000"),    # 10.0% Japanese consumption tax
                de_minimis_threshold=Decimal("10000.00"),  # ¥10,000 threshold
                default_freight=Decimal("22.00"),
                insurance_rate=Decimal("0.0100"),
                handling_fee=Decimal("7.00"),
            ),
        ]
        db.add_all(configs)
        db.commit()

    # 4. Seed Traceable Exchange Rates
    if not db.query(ExchangeRate).first():
        logger.info("Seeding baseline foreign exchange rates...")
        now = datetime.now(timezone.utc)
        fx_rates = [
            ExchangeRate(base_currency="USD", target_currency="USD", rate=Decimal("1.000000"), source="open.er-api.com", fetched_at=now),
            ExchangeRate(base_currency="USD", target_currency="EUR", rate=Decimal("0.920000"), source="open.er-api.com", fetched_at=now),
            ExchangeRate(base_currency="USD", target_currency="GBP", rate=Decimal("0.785000"), source="open.er-api.com", fetched_at=now),
            ExchangeRate(base_currency="USD", target_currency="INR", rate=Decimal("83.500000"), source="open.er-api.com", fetched_at=now),
            ExchangeRate(base_currency="USD", target_currency="JPY", rate=Decimal("152.400000"), source="open.er-api.com", fetched_at=now),
            ExchangeRate(base_currency="USD", target_currency="CAD", rate=Decimal("1.360000"), source="open.er-api.com", fetched_at=now),
            ExchangeRate(base_currency="USD", target_currency="AUD", rate=Decimal("1.520000"), source="open.er-api.com", fetched_at=now),
        ]
        db.add_all(fx_rates)
        db.commit()

    # 5. Seed Initial Canonical Products with Cross-Border Listings & Historical Observations
    if not db.query(Product).first():
        logger.info("Seeding initial benchmark products and cross-border listings...")
        now = datetime.now(timezone.utc)

        # Product 1: MacBook Pro 14 M3
        p1 = Product(
            sku="TECH-APL-MBP14-M3",
            title="Apple MacBook Pro 14-inch (M3 Chip, 512GB SSD, Space Gray)",
            brand="Apple",
            category="Electronics",
            description="Apple MacBook Pro 14-inch with M3 chip, 8-core CPU, 10-core GPU, 8GB unified memory, 512GB SSD storage.",
            image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop&q=60",
            target_base_price=Decimal("1599.00"),
            base_currency="USD",
        )
        db.add(p1)
        db.flush()

        # Listings for Product 1
        l1_us = ProductListing(
            product_id=p1.id,
            marketplace_id="amazon_us",
            external_id="B0CM5JV5N5",
            listing_title="Apple 2023 MacBook Pro Laptop M3 chip, 14.2-inch Liquid Retina XDR Display, 8GB Unified Memory, 512GB SSD Storage",
            listing_url="https://www.amazon.com/dp/B0CM5JV5N5",
            currency_code="USD",
            seller_name="Amazon.com",
        )
        l1_uk = ProductListing(
            product_id=p1.id,
            marketplace_id="amazon_uk",
            external_id="B0CM5JV5N5_UK",
            listing_title="Apple 2023 MacBook Pro laptop with M3 chip: 14.2-inch Liquid Retina XDR display, 8GB Unified Memory, 512GB SSD",
            listing_url="https://www.amazon.co.uk/dp/B0CM5JV5N5",
            currency_code="GBP",
            seller_name="Amazon UK Retail",
        )
        l1_in = ProductListing(
            product_id=p1.id,
            marketplace_id="flipkart_in",
            external_id="FLIP_MBP14_M3_512",
            listing_title="Apple MacBook Pro M3 - (8 GB/512 GB SSD/macOS Sonoma) MTL73HN/A (14.2 Inch, Space Grey)",
            listing_url="https://www.flipkart.com/apple-macbook-pro-m3-8-gb-512-gb-ssd-macos-sonoma-mtl73hn-a/p/itm123",
            currency_code="INR",
            seller_name="IndiFlashMart",
        )
        db.add_all([l1_us, l1_uk, l1_in])
        db.flush()

        # Matches for Product 1
        m1_us = ProductMatch(
            product_id=p1.id,
            listing_id=l1_us.id,
            confidence_score=Decimal("100.00"),
            match_type="exact_sku",
            match_evidence={"exact_model": "MTL73LL/A", "title_similarity": 0.98},
            status="confirmed",
        )
        m1_uk = ProductMatch(
            product_id=p1.id,
            listing_id=l1_uk.id,
            confidence_score=Decimal("94.50"),
            match_type="token_cosine",
            match_evidence={"brand": "Apple", "token_overlap": ["macbook", "pro", "14", "m3", "512gb"]},
            status="confirmed",
        )
        m1_in = ProductMatch(
            product_id=p1.id,
            listing_id=l1_in.id,
            confidence_score=Decimal("91.20"),
            match_type="fuzzy_levenshtein",
            match_evidence={"brand": "Apple", "model": "MTL73HN/A"},
            status="confirmed",
        )
        db.add_all([m1_us, m1_uk, m1_in])

        # Observations for Product 1
        obs_1_us = PriceObservation(
            listing_id=l1_us.id,
            listed_price=Decimal("1549.00"),
            currency_code="USD",
            shipping_price=Decimal("0.00"),
            discount_pct=Decimal("3.13"),
            availability_status="in_stock",
            rating=Decimal("4.80"),
            review_count=1420,
            data_provenance="synthetic_seed",
            observed_at=now,
        )
        obs_1_uk = PriceObservation(
            listing_id=l1_uk.id,
            listed_price=Decimal("1449.00"),
            currency_code="GBP",
            shipping_price=Decimal("4.99"),
            discount_pct=Decimal("0.00"),
            availability_status="in_stock",
            rating=Decimal("4.75"),
            review_count=890,
            data_provenance="synthetic_seed",
            observed_at=now,
        )
        obs_1_in = PriceObservation(
            listing_id=l1_in.id,
            listed_price=Decimal("159900.00"),
            currency_code="INR",
            shipping_price=Decimal("0.00"),
            discount_pct=Decimal("5.00"),
            availability_status="in_stock",
            rating=Decimal("4.60"),
            review_count=310,
            data_provenance="synthetic_seed",
            observed_at=now,
        )
        db.add_all([obs_1_us, obs_1_uk, obs_1_in])

        # Price Alert for Product 1
        alert_1 = PriceAlert(
            product_id=p1.id,
            alert_type="threshold_below",
            condition_value=Decimal("1500.00"),
            severity="high",
            is_active=True,
        )
        db.add(alert_1)

        # Product 2: Sony WH-1000XM5 Headphones
        p2 = Product(
            sku="AUDIO-SNY-WH1000XM5",
            title="Sony WH-1000XM5 Wireless Noise Canceling Headphones",
            brand="Sony",
            category="Electronics",
            description="Industry Leading Noise Canceling Wireless Over-Ear Headphones with Auto NC Optimizer, crystal clear hands-free calling, and 30-hour battery life.",
            image_url="https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&auto=format&fit=crop&q=60",
            target_base_price=Decimal("399.99"),
            base_currency="USD",
        )
        db.add(p2)
        db.flush()

        l2_us = ProductListing(
            product_id=p2.id,
            marketplace_id="amazon_us",
            external_id="B09XS7JWHH",
            listing_title="Sony WH-1000XM5 Wireless Industry Leading Noise Canceling Headphones, Black",
            listing_url="https://www.amazon.com/dp/B09XS7JWHH",
            currency_code="USD",
            seller_name="Sony Direct",
        )
        l2_uk = ProductListing(
            product_id=p2.id,
            marketplace_id="amazon_uk",
            external_id="B09XS7JWHH_UK",
            listing_title="Sony WH-1000XM5 Noise Cancelling Wireless Headphones - 30 hours battery life - Black",
            listing_url="https://www.amazon.co.uk/dp/B09XS7JWHH",
            currency_code="GBP",
            seller_name="Amazon UK",
        )
        db.add_all([l2_us, l2_uk])
        db.flush()

        obs_2_us = PriceObservation(
            listing_id=l2_us.id,
            listed_price=Decimal("348.00"),
            currency_code="USD",
            shipping_price=Decimal("0.00"),
            discount_pct=Decimal("13.00"),
            availability_status="in_stock",
            rating=Decimal("4.60"),
            review_count=8450,
            data_provenance="synthetic_seed",
            observed_at=now,
        )
        obs_2_uk = PriceObservation(
            listing_id=l2_uk.id,
            listed_price=Decimal("299.00"),
            currency_code="GBP",
            shipping_price=Decimal("0.00"),
            discount_pct=Decimal("14.50"),
            availability_status="in_stock",
            rating=Decimal("4.55"),
            review_count=3200,
            data_provenance="synthetic_seed",
            observed_at=now,
        )
        db.add_all([obs_2_us, obs_2_uk])

        db.commit()
        logger.info("Initial benchmark dataset seeded successfully.")
