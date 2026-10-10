"""End-to-End Pipeline Test: Full lifecycle from ingestion to intelligence and dashboard."""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.main import app
from app.models import (
    AlertNotification,
    Country,
    DataImportBatch,
    ExchangeRate,
    Marketplace,
    PriceAlert,
    PriceObservation,
    Product,
    ProductListing,
    ProductMatch,
    ScrapingJob,
)
from app.services.alerts.alert_service import AlertService
from app.services.analytics.dashboard_service import DashboardService
from app.services.analytics.history_service import PriceHistoryService
from app.services.analytics.positioning import MarketPositioningService
from app.services.export.export_service import ExportService
from app.services.ingestion.importer import DataIngestionService
from app.services.matcher.engine import ProductMatchingEngine
from app.services.pricing.fx_service import FXService
from app.services.pricing.landed_cost import LandedCostService

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_full_e2e_pricing_intelligence_pipeline():
    """
    Executes the entire business intelligence pipeline:
    1. Ingestion: Ingest multi-market listings via CSV batch.
    2. Matching: Run automated fuzzy matcher to link listings to canonical products.
    3. Landed Cost: Calculate landed cost matrix with customs duties and FX.
    4. Price History: Track chronological price series and compute rolling stats.
    5. Intelligence: Generate competitive positioning and discover export arbitrage.
    6. Alerts: Trigger automated rule evaluations and produce notifications.
    7. Exports: Stream CSV reports.
    8. Dashboard: Consolidate platform-wide executive KPIs.
    """
    with SessionLocal() as db:
        suffix = uuid.uuid4().hex[:6]
        sku = f"E2E-CAM-{suffix}"
        ext_us = f"ext_cam_us_{suffix}"
        ext_uk = f"ext_cam_uk_{suffix}"
        ext_de = f"ext_cam_de_{suffix}"

        # Step 1: Ingestion of New Cross-Border Listing Batch
        csv_content = (
            "sku,title,brand,category,marketplace_id,price,currency,url,external_id\n"
            f"{sku},Ultra HD 4K Action Camera {suffix},GoPro,Electronics,amazon_us,399.00,USD,https://amazon.com/dp/CAM4K1,{ext_us}\n"
            f"{sku},Ultra HD 4K Action Cam Waterproof {suffix},GoPro,Electronics,amazon_uk,349.00,GBP,https://amazon.co.uk/dp/CAM4K2,{ext_uk}\n"
            f"{sku},GoPro 4K Action Camera Ultra HD {suffix},GoPro,Electronics,amazon_de,389.00,EUR,https://amazon.de/dp/CAM4K3,{ext_de}\n"
        )
        batch = DataIngestionService.import_csv(db, csv_content, source_name="e2e_camera_batch.csv")
        assert batch.record_count == 3
        assert batch.inserted_count == 3

        # Verify product created
        listing_us = db.query(ProductListing).filter(ProductListing.external_id == ext_us).first()
        assert listing_us is not None
        cam_product = listing_us.product
        assert cam_product is not None
        assert cam_product.sku == sku
        cam_product_id = cam_product.id

        # Step 2: Automated Product Matching
        match_result = ProductMatchingEngine.run_batch_matching(db)
        assert match_result.total_listings_inspected >= 3

        # Step 3: Landed Cost Engine Calculation
        matrix = LandedCostService.get_product_comparison_matrix(
            db=db,
            product_id=cam_product_id,
            destination_country_id="US",
            reporting_currency="USD",
        )
        assert matrix.product_id == cam_product_id
        assert len(matrix.listings) >= 3
        assert matrix.lowest_landed_cost is not None
        assert matrix.highest_landed_cost is not None
        assert matrix.lowest_landed_cost <= matrix.highest_landed_cost

        # Step 4: Historical Price Tracking & Analytics
        history = PriceHistoryService.get_product_history(
            db=db,
            product_id=cam_product_id,
            reporting_currency="USD",
            days=30,
        )
        assert history.product_id == cam_product_id
        assert history.marketplaces_tracked >= 3
        assert len(history.timeline_series) >= 1
        for listing_hist in history.listings_history:
            assert listing_hist.stats.observation_count >= 1

        # Step 5: Market Positioning & Strategic Advice
        positioning = MarketPositioningService.analyze_product_positioning(
            db=db,
            product_id=cam_product_id,
            destination_country_id="US",
            reporting_currency="USD",
        )
        assert positioning.product_id == cam_product_id
        assert positioning.strategic_recommendation in [
            "raise_price_to_maximize_margin",
            "maintain_price",
            "lower_price_to_compete",
            "differentiate_or_match_leader",
        ]
        assert len(positioning.rankings) >= 3
        assert positioning.rankings[0].is_cheapest is True

        # Step 6: Export Arbitrage Opportunities
        arbitrage = MarketPositioningService.detect_export_opportunities(
            db=db,
            min_margin_pct=Decimal("2.0"),
            reporting_currency="USD",
        )
        assert arbitrage.total_opportunities_found >= 0

        # Step 7: Price Alert Configuration & Evaluation
        alert_payload = PriceAlert(
            product_id=cam_product_id,
            alert_type="threshold_below",
            condition_value=Decimal("450.00"),
            severity="high",
            is_active=True,
        )
        db.add(alert_payload)
        db.commit()

        eval_result = AlertService.evaluate_alerts(db, product_id=cam_product_id)
        assert eval_result.rules_evaluated >= 1
        assert eval_result.alerts_triggered >= 1

        # Step 8: Structured CSV Report Exports
        comparison_csv = ExportService.export_comparison_matrix_csv(db, "US", "USD")
        assert sku in comparison_csv
        assert "Total Landed Cost" in comparison_csv

        history_csv = ExportService.export_product_history_csv(db, cam_product_id, "USD", 30)
        assert sku in history_csv

        # Step 9: Executive Dashboard KPI Summary
        dashboard_summary = DashboardService.get_summary(db)
        assert dashboard_summary.total_products >= 3
        assert dashboard_summary.total_listings >= 7
        assert dashboard_summary.total_observations >= 7
        assert dashboard_summary.active_alerts_count >= 1
        assert dashboard_summary.scraping_health.total_jobs >= 0


def test_e2e_api_http_workflow():
    """Verify HTTP endpoints end-to-end via FastAPI TestClient."""
    # 1. Health check
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["data"]["database_connected"] is True

    # 2. Executive Dashboard Summary
    res_dash = client.get("/api/v1/dashboard/summary")
    assert res_dash.status_code == 200
    assert res_dash.json()["success"] is True

    # 3. Product Comparison Matrix
    with SessionLocal() as db:
        product = db.query(Product).first()
        prod_id = product.id

    res_comp = client.get(f"/api/v1/pricing/comparison?product_id={prod_id}&destination_country=US&reporting_currency=USD")
    assert res_comp.status_code == 200
    assert res_comp.json()["data"]["product_id"] == prod_id

    # 4. Landed Cost Simulation
    sim_payload = {
        "price": 999.00,
        "source_currency": "USD",
        "destination_country": "US",
        "override_freight": 20.00,
        "override_duty_rate": 0.05,
        "override_tax_rate": 0.08,
        "override_insurance_rate": 0.01,
        "override_handling_fee": 10.00,
    }
    res_sim = client.post("/api/v1/pricing/landed-cost/calculate", json=sim_payload)
    assert res_sim.status_code == 200
    assert float(res_sim.json()["data"]["total_landed_cost"]) > 999.00

    # 5. Market Positioning
    res_pos = client.get(f"/api/v1/intelligence/positioning?product_id={prod_id}&destination_country=US&reporting_currency=USD")
    assert res_pos.status_code == 200
    assert "strategic_recommendation" in res_pos.json()["data"]

    # 6. CSV Report Downloads
    res_csv = client.get("/api/v1/reports/export/comparison/csv?destination_country=US&reporting_currency=USD")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
