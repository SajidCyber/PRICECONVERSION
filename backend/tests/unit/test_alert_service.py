"""Unit tests for AlertService rule management and trigger engine."""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pytest
from app.core.database import SessionLocal
from app.core.db_init import init_db, seed_initial_data
from app.models import AlertNotification, PriceAlert, PriceObservation, Product, ProductListing
from app.schemas.alert import PriceAlertCreate, PriceAlertUpdate
from app.services.alerts.alert_service import AlertService


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


def test_alert_crud_lifecycle():
    """Verify creating, reading, updating, and deleting price alert rules."""
    with SessionLocal() as db:
        product = db.query(Product).first()
        assert product is not None
        prod_id = product.id

        # Create
        create_payload = PriceAlertCreate(
            product_id=prod_id,
            alert_type="threshold_below",
            condition_value=Decimal("1500.00"),
            severity="high",
        )
        created = AlertService.create_alert(db, create_payload)
        assert created.id is not None
        assert created.alert_type == "threshold_below"
        assert created.condition_value == Decimal("1500.00")
        assert created.severity == "high"
        alert_id = created.id

        # List
        alerts = AlertService.list_alerts(db, product_id=prod_id)
        assert any(a.id == alert_id for a in alerts)

        # Update
        update_payload = PriceAlertUpdate(condition_value=Decimal("1400.00"), severity="critical")
        updated = AlertService.update_alert(db, alert_id, update_payload)
        assert updated.condition_value == Decimal("1400.00")
        assert updated.severity == "critical"

        # Delete
        deleted = AlertService.delete_alert(db, alert_id)
        assert deleted is True


def test_evaluate_threshold_below_alert():
    """Verify threshold_below rule triggers notification when price falls below threshold."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        u_id = uuid.uuid4().hex[:8]
        prod = Product(
            id=f"test_alt_p_{u_id}",
            sku=f"ALT-P-{u_id}",
            title="Alert Test Product",
            category="Electronics",
        )
        db.add(prod)
        db.flush()

        listing = ProductListing(
            id=f"test_alt_l_{u_id}",
            product_id=prod.id,
            marketplace_id="amazon_us",
            currency_code="USD",
            listing_title="Alert Test Listing",
            listing_url="https://amazon.com/dp/B0ALERT11",
            external_id=f"ext_alt_{u_id}",
        )
        db.add(listing)
        db.flush()

        # Observation price is $1200
        obs = PriceObservation(
            listing_id=listing.id,
            listed_price=Decimal("1200.00"),
            currency_code="USD",
            observed_at=now,
        )
        db.add(obs)
        db.flush()

        # Rule triggers if price <= $1300
        rule = PriceAlert(
            product_id=prod.id,
            alert_type="threshold_below",
            condition_value=Decimal("1300.00"),
            severity="high",
            is_active=True,
        )
        db.add(rule)
        db.commit()

        # Evaluate alerts
        result = AlertService.evaluate_alerts(db, product_id=prod.id)
        assert result.rules_evaluated >= 1
        assert result.alerts_triggered >= 1
        assert len(result.new_notifications) >= 1

        notif = result.new_notifications[0]
        assert notif.product_id == prod.id
        assert notif.is_acknowledged is False
        assert "dropped to USD 1200.00" in notif.message

        # Test deduplication - running again should trigger 0 new notifications
        result_second_run = AlertService.evaluate_alerts(db, product_id=prod.id)
        assert result_second_run.alerts_triggered == 0


def test_evaluate_pct_change_drop_alert():
    """Verify pct_change_drop rule triggers notification on flash discount."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        u_id = uuid.uuid4().hex[:8]
        prod = Product(
            id=f"test_pct_p_{u_id}",
            sku=f"PCT-P-{u_id}",
            title="Flash Drop Test Product",
            category="Electronics",
        )
        db.add(prod)
        db.flush()

        listing = ProductListing(
            id=f"test_pct_l_{u_id}",
            product_id=prod.id,
            marketplace_id="amazon_us",
            currency_code="USD",
            listing_title="Flash Drop Listing",
            listing_url="https://amazon.com/dp/B0FLASH11",
            external_id=f"ext_pct_{u_id}",
        )
        db.add(listing)
        db.flush()

        # Previous price $1000, current price $750 (25% drop)
        obs1 = PriceObservation(
            listing_id=listing.id,
            listed_price=Decimal("1000.00"),
            currency_code="USD",
            observed_at=now - timedelta(hours=2),
        )
        obs2 = PriceObservation(
            listing_id=listing.id,
            listed_price=Decimal("750.00"),
            currency_code="USD",
            observed_at=now,
        )
        db.add_all([obs1, obs2])
        db.flush()

        # Rule triggers if price drop >= 20%
        rule = PriceAlert(
            product_id=prod.id,
            alert_type="pct_change_drop",
            condition_value=Decimal("20.00"),
            severity="critical",
            is_active=True,
        )
        db.add(rule)
        db.commit()

        result = AlertService.evaluate_alerts(db, product_id=prod.id)
        assert result.alerts_triggered >= 1
        notif = result.new_notifications[0]
        assert "Flash Discount" in notif.message
        assert notif.severity == "critical"


def test_acknowledge_notification():
    """Verify acknowledging a triggered notification updates its state."""
    with SessionLocal() as db:
        notif = db.query(AlertNotification).filter(AlertNotification.is_acknowledged == False).first()
        if not notif:
            alert = db.query(PriceAlert).first()
            obs = db.query(PriceObservation).first()
            notif = AlertNotification(
                alert_id=alert.id,
                observation_id=obs.id,
                message="Test notification message",
                evidence_payload={},
                is_acknowledged=False,
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)

        notif_id = notif.id
        ack_res = AlertService.acknowledge_notification(db, notif_id)
        assert ack_res.id == notif_id
        assert ack_res.is_acknowledged is True
