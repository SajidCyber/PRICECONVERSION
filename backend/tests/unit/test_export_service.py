"""Unit tests for ExportService CSV generation."""

import csv
import io
from decimal import Decimal
import pytest
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.models import Product
from app.services.export.export_service import ExportService


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_export_comparison_matrix_csv():
    """Verify comparison matrix CSV export contains headers and data."""
    with SessionLocal() as db:
        csv_str = ExportService.export_comparison_matrix_csv(
            db=db,
            destination_country="US",
            reporting_currency="USD",
        )
        assert csv_str is not None
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) >= 2  # Header + at least 1 data row
        header = rows[0]
        assert "Product SKU" in header
        assert "Total Landed Cost" in header
        assert "CIF Value" in header


def test_export_product_history_csv():
    """Verify product history CSV export contains time-series rows."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        assert product is not None
        product_id = product.id

        csv_str = ExportService.export_product_history_csv(
            db=db,
            product_id=product_id,
            reporting_currency="USD",
            days=30,
        )
        assert csv_str is not None
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) >= 2  # Header + observations
        header = rows[0]
        assert "Product SKU" in header
        assert "Listed Price" in header
        assert "Converted Price" in header


def test_export_opportunities_csv():
    """Verify export arbitrage CSV output format."""
    with SessionLocal() as db:
        csv_str = ExportService.export_opportunities_csv(
            db=db,
            min_margin_pct=Decimal("5.0"),
            reporting_currency="USD",
        )
        assert csv_str is not None
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) >= 1  # Header
        header = rows[0]
        assert "Source Marketplace" in header
        assert "Target Marketplace" in header
        assert "Net Profit Margin" in header
