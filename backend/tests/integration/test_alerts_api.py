"""Integration tests for Price Alerts & Notifications REST API."""

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


def test_alerts_full_api_workflow():
    """Verify full alert creation, listing, evaluation, notification, acknowledgment, and deletion flow."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.sku == "TECH-APL-MBP14-M3").first()
        assert product is not None
        product_id = product.id

    # 1. Create Alert
    create_payload = {
        "product_id": product_id,
        "alert_type": "threshold_below",
        "condition_value": 2000.00,
        "severity": "high",
        "is_active": True,
    }
    create_res = client.post("/api/v1/alerts", json=create_payload)
    assert create_res.status_code == 201
    alert_data = create_res.json()["data"]
    alert_id = alert_data["id"]
    assert alert_data["product_id"] == product_id
    assert float(alert_data["condition_value"]) == 2000.00

    # 2. List Alerts
    list_res = client.get(f"/api/v1/alerts?product_id={product_id}")
    assert list_res.status_code == 200
    alerts = list_res.json()["data"]
    assert any(a["id"] == alert_id for a in alerts)

    # 3. Update Alert
    update_res = client.put(f"/api/v1/alerts/{alert_id}", json={"severity": "critical"})
    assert update_res.status_code == 200
    assert update_res.json()["data"]["severity"] == "critical"

    # 4. Trigger Evaluation Run
    eval_res = client.post(f"/api/v1/alerts/evaluate?product_id={product_id}")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()["data"]
    assert eval_data["rules_evaluated"] >= 1

    # 5. List Notifications
    notif_res = client.get("/api/v1/alerts/notifications")
    assert notif_res.status_code == 200
    notifs = notif_res.json()["data"]
    assert isinstance(notifs, list)

    if notifs:
        target_notif = notifs[0]
        notif_id = target_notif["id"]

        # 6. Acknowledge Notification
        ack_res = client.patch(f"/api/v1/alerts/notifications/{notif_id}/read")
        assert ack_res.status_code == 200
        assert ack_res.json()["data"]["is_acknowledged"] is True

    # 7. Delete Alert
    del_res = client.delete(f"/api/v1/alerts/{alert_id}")
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True
