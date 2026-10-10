"""Unit tests for Scraper Adapters, HTML Parsers, and Currency extractors."""

from decimal import Decimal
from pathlib import Path
import pytest
from app.services.scraper.books_adapter import BooksToScrapeAdapter
from app.services.scraper.dummyjson_adapter import DummyJsonAdapter
from app.services.scraper.fakestore_adapter import FakeStoreAdapter


@pytest.fixture
def books_html_fixture() -> str:
    fixture_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "fixtures" / "books_to_scrape_sample.html"
    return fixture_path.read_text(encoding="utf-8")


def test_numeric_price_parsing():
    """Verify price string parsing handles various currency formats and separators."""
    adapter = BooksToScrapeAdapter()

    assert adapter.parse_numeric_price("£51.77") == Decimal("51.77")
    assert adapter.parse_numeric_price("$1,299.99") == Decimal("1299.99")
    assert adapter.parse_numeric_price("€ 49,90") == Decimal("49.90")
    assert adapter.parse_numeric_price("₹ 1,59,900.00") == Decimal("159900.00")
    assert adapter.parse_numeric_price("149.00 USD") == Decimal("149.00")

    with pytest.raises(ValueError):
        adapter.parse_numeric_price("$0.00")

    with pytest.raises(ValueError):
        adapter.parse_numeric_price("Out of Stock")


def test_currency_symbol_normalization():
    """Verify currency symbol to ISO code mapping."""
    adapter = BooksToScrapeAdapter()
    assert adapter.normalize_currency_symbol("£45.00") == "GBP"
    assert adapter.normalize_currency_symbol("$19.99") == "USD"
    assert adapter.normalize_currency_symbol("€29.00") == "EUR"
    assert adapter.normalize_currency_symbol("₹999.00") == "INR"
    assert adapter.normalize_currency_symbol("¥15000") == "JPY"


def test_books_to_scrape_html_parsing(books_html_fixture):
    """Verify BooksToScrapeAdapter correctly parses HTML fixture into ExtractedProductDTO."""
    adapter = BooksToScrapeAdapter()
    items = adapter.parse_catalog_html(books_html_fixture, base_page_url="https://books.toscrape.com/catalogue/page-1.html")

    assert len(items) == 3

    item1 = items[0]
    assert item1.title == "A Light in the Attic"
    assert item1.price == Decimal("51.77")
    assert item1.currency_code == "GBP"
    assert item1.availability_status == "in_stock"
    assert item1.rating == Decimal("3.0")
    assert item1.external_id == "a-light-in-the-attic_1000"
    assert "books.toscrape.com" in item1.url

    item2 = items[1]
    assert item2.title == "Tipping the Velvet"
    assert item2.price == Decimal("53.74")
    assert item2.rating == Decimal("1.0")

    item3 = items[2]
    assert item3.title == "Soumission"
    assert item3.price == Decimal("50.10")
    assert item3.rating == Decimal("5.0")


def test_dummyjson_adapter_json_mapping():
    """Verify DummyJSONAdapter correctly maps API response items."""
    adapter = DummyJsonAdapter()
    mock_products = [
        {
            "id": 1,
            "title": "iPhone 9",
            "description": "An apple mobile which is nothing like apple",
            "price": 549,
            "discountPercentage": 12.96,
            "rating": 4.69,
            "stock": 94,
            "brand": "Apple",
            "category": "smartphones",
            "thumbnail": "https://cdn.dummyjson.com/product-images/1/thumbnail.jpg",
        }
    ]
    items = adapter.parse_json_products(mock_products)
    assert len(items) == 1
    item = items[0]
    assert item.external_id == "DUMMY-1"
    assert item.title == "iPhone 9"
    assert item.price == Decimal("549")
    assert item.discount_pct == Decimal("12.96")
    assert item.brand == "Apple"
    assert item.data_provenance == "demo_api"


def test_fakestore_adapter_json_mapping():
    """Verify FakeStoreAdapter correctly maps API response items."""
    adapter = FakeStoreAdapter()
    mock_items = [
        {
            "id": 1,
            "title": "Fjallraven - Foldsack No. 1 Backpack",
            "price": 109.95,
            "description": "Your perfect pack for everyday use",
            "category": "men's clothing",
            "image": "https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg",
            "rating": {"rate": 3.9, "count": 120},
        }
    ]
    items = adapter.parse_fakestore_products(mock_items)
    assert len(items) == 1
    item = items[0]
    assert item.external_id == "FAKESTORE-1"
    assert item.price == Decimal("109.95")
    assert item.rating == Decimal("3.9")
    assert item.review_count == 120
