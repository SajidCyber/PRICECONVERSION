"""Price Alerts Evaluation and Trigger Dispatching Service."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import EntityNotFoundError
from app.core.logging_config import logger
from app.models import AlertNotification, PriceAlert, PriceObservation, Product, ProductListing
from app.schemas.alert import (
    AlertEvaluationResult,
    AlertNotificationResponse,
    PriceAlertCreate,
    PriceAlertResponse,
    PriceAlertUpdate,
)
from app.services.pricing.landed_cost import LandedCostService


class AlertService:
    """Manages price alert rules, triggers threshold evaluations, and produces notifications."""

    @classmethod
    def create_alert(cls, db: Session, payload: PriceAlertCreate) -> PriceAlertResponse:
        """Creates a new price alert rule for a product."""
        product = db.query(Product).filter(Product.id == payload.product_id).first()
        if not product:
            raise EntityNotFoundError("Product", payload.product_id)

        alert = PriceAlert(
            product_id=payload.product_id,
            alert_type=payload.alert_type,
            condition_value=payload.condition_value,
            severity=payload.severity,
            is_active=payload.is_active,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        return PriceAlertResponse(
            id=alert.id,
            product_id=alert.product_id,
            product_title=product.title,
            alert_type=alert.alert_type,
            condition_value=alert.condition_value,
            severity=alert.severity,
            is_active=alert.is_active,
            created_at=alert.created_at,
            notifications_count=0,
        )

    @classmethod
    def list_alerts(
        cls,
        db: Session,
        product_id: Optional[str] = None,
        active_only: bool = False,
    ) -> List[PriceAlertResponse]:
        """Lists configured price alert rules."""
        query = db.query(PriceAlert).options(
            joinedload(PriceAlert.product),
            joinedload(PriceAlert.notifications),
        )
        if product_id:
            query = query.filter(PriceAlert.product_id == product_id)
        if active_only:
            query = query.filter(PriceAlert.is_active == True)

        alerts = query.order_by(PriceAlert.created_at.desc()).all()
        return [
            PriceAlertResponse(
                id=a.id,
                product_id=a.product_id,
                product_title=a.product.title if a.product else None,
                alert_type=a.alert_type,
                condition_value=a.condition_value,
                severity=a.severity,
                is_active=a.is_active,
                created_at=a.created_at,
                notifications_count=len(a.notifications),
            )
            for a in alerts
        ]

    @classmethod
    def update_alert(
        cls,
        db: Session,
        alert_id: str,
        payload: PriceAlertUpdate,
    ) -> PriceAlertResponse:
        """Updates properties of an existing alert rule."""
        alert = db.query(PriceAlert).options(joinedload(PriceAlert.product), joinedload(PriceAlert.notifications)).filter(PriceAlert.id == alert_id).first()
        if not alert:
            raise EntityNotFoundError("PriceAlert", alert_id)

        if payload.alert_type is not None:
            alert.alert_type = payload.alert_type
        if payload.condition_value is not None:
            alert.condition_value = payload.condition_value
        if payload.severity is not None:
            alert.severity = payload.severity
        if payload.is_active is not None:
            alert.is_active = payload.is_active

        db.commit()
        db.refresh(alert)

        return PriceAlertResponse(
            id=alert.id,
            product_id=alert.product_id,
            product_title=alert.product.title if alert.product else None,
            alert_type=alert.alert_type,
            condition_value=alert.condition_value,
            severity=alert.severity,
            is_active=alert.is_active,
            created_at=alert.created_at,
            notifications_count=len(alert.notifications),
        )

    @classmethod
    def delete_alert(cls, db: Session, alert_id: str) -> bool:
        """Deletes an alert rule."""
        alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
        if not alert:
            raise EntityNotFoundError("PriceAlert", alert_id)
        db.delete(alert)
        db.commit()
        return True

    @classmethod
    def evaluate_alerts(
        cls,
        db: Session,
        product_id: Optional[str] = None,
    ) -> AlertEvaluationResult:
        """Evaluates active alert rules against latest observation state and generates notification events."""
        query = db.query(PriceAlert).options(
            joinedload(PriceAlert.product)
            .joinedload(Product.listings)
            .joinedload(ProductListing.observations),
            joinedload(PriceAlert.product)
            .joinedload(Product.listings)
            .joinedload(ProductListing.marketplace),
        ).filter(PriceAlert.is_active == True)

        if product_id:
            query = query.filter(PriceAlert.product_id == product_id)

        alerts = query.all()
        triggered_notifications: List[AlertNotificationResponse] = []

        for alert in alerts:
            product = alert.product
            if not product or not product.listings:
                continue

            for listing in product.listings:
                if not listing.observations:
                    continue

                sorted_obs = sorted(listing.observations, key=lambda o: o.observed_at)
                latest_obs = sorted_obs[-1]

                # Check if notification already logged for this specific (alert, observation)
                existing = (
                    db.query(AlertNotification)
                    .filter(
                        AlertNotification.alert_id == alert.id,
                        AlertNotification.observation_id == latest_obs.id,
                    )
                    .first()
                )
                if existing:
                    continue

                triggered = False
                message = ""
                evidence: Dict[str, Any] = {
                    "product_id": product.id,
                    "product_title": product.title,
                    "listing_id": listing.id,
                    "marketplace": listing.marketplace.name if listing.marketplace else listing.marketplace_id,
                    "current_price": float(latest_obs.listed_price),
                    "currency": latest_obs.currency_code,
                    "condition_value": float(alert.condition_value),
                }

                if alert.alert_type == "threshold_below":
                    if latest_obs.listed_price <= alert.condition_value:
                        triggered = True
                        message = (
                            f"Price Alert: '{product.title}' dropped to {latest_obs.currency_code} {latest_obs.listed_price} "
                            f"on {evidence['marketplace']}, which is at or below threshold of {latest_obs.currency_code} {alert.condition_value}."
                        )

                elif alert.alert_type == "pct_change_drop":
                    if len(sorted_obs) >= 2:
                        prev_price = sorted_obs[-2].listed_price
                        if prev_price > 0:
                            pct_drop = Decimal(f"{(((latest_obs.listed_price - prev_price) / prev_price) * 100):.2f}")
                            if pct_drop < 0 and abs(pct_drop) >= alert.condition_value:
                                triggered = True
                                evidence["previous_price"] = float(prev_price)
                                evidence["pct_drop"] = float(pct_drop)
                                message = (
                                    f"Flash Discount: '{product.title}' dropped by {abs(float(pct_drop)):.1f}% "
                                    f"(from {prev_price} to {latest_obs.listed_price} {latest_obs.currency_code}) on {evidence['marketplace']}."
                                )

                elif alert.alert_type == "out_of_stock":
                    if latest_obs.availability_status == "out_of_stock":
                        triggered = True
                        message = f"Stock Alert: '{product.title}' is reported OUT OF STOCK on {evidence['marketplace']}."

                elif alert.alert_type == "landed_cost_breach":
                    # Check if competitor landed cost is below threshold
                    dest_country = listing.marketplace.country_id if listing.marketplace else "US"
                    calc = LandedCostService.calculate_landed_cost(
                        db=db,
                        price=latest_obs.listed_price,
                        source_currency=listing.currency_code,
                        destination_country_id=dest_country,
                        product_category=product.category,
                    )
                    evidence["landed_cost"] = float(calc.total_landed_cost)
                    if calc.total_landed_cost <= alert.condition_value:
                        triggered = True
                        message = (
                            f"Landed Cost Breach: '{product.title}' on {evidence['marketplace']} has landed cost of "
                            f"{calc.destination_currency} {calc.total_landed_cost}, falling below target limit of {alert.condition_value}."
                        )

                if triggered:
                    notification = AlertNotification(
                        alert_id=alert.id,
                        observation_id=latest_obs.id,
                        message=message,
                        evidence_payload=evidence,
                        is_acknowledged=False,
                    )
                    db.add(notification)
                    db.commit()
                    db.refresh(notification)

                    dto = AlertNotificationResponse(
                        id=notification.id,
                        alert_id=notification.alert_id,
                        product_id=product.id,
                        product_title=product.title,
                        observation_id=notification.observation_id,
                        alert_type=alert.alert_type,
                        severity=alert.severity,
                        message=notification.message,
                        evidence_payload=notification.evidence_payload,
                        is_acknowledged=notification.is_acknowledged,
                        triggered_at=notification.triggered_at,
                    )
                    triggered_notifications.append(dto)

        return AlertEvaluationResult(
            rules_evaluated=len(alerts),
            alerts_triggered=len(triggered_notifications),
            new_notifications=triggered_notifications,
        )

    @classmethod
    def list_notifications(
        cls,
        db: Session,
        unacknowledged_only: bool = False,
        limit: int = 50,
    ) -> List[AlertNotificationResponse]:
        """Returns triggered alert events."""
        query = db.query(AlertNotification).options(
            joinedload(AlertNotification.alert).joinedload(PriceAlert.product)
        )
        if unacknowledged_only:
            query = query.filter(AlertNotification.is_acknowledged == False)

        notifications = query.order_by(AlertNotification.triggered_at.desc()).limit(limit).all()
        return [
            AlertNotificationResponse(
                id=n.id,
                alert_id=n.alert_id,
                product_id=n.alert.product_id if n.alert else None,
                product_title=n.alert.product.title if n.alert and n.alert.product else None,
                observation_id=n.observation_id,
                alert_type=n.alert.alert_type if n.alert else "unknown",
                severity=n.alert.severity if n.alert else "medium",
                message=n.message,
                evidence_payload=n.evidence_payload or {},
                is_acknowledged=n.is_acknowledged,
                triggered_at=n.triggered_at,
            )
            for n in notifications
        ]

    @classmethod
    def acknowledge_notification(cls, db: Session, notification_id: str) -> AlertNotificationResponse:
        """Marks an alert notification as acknowledged/read."""
        notif = db.query(AlertNotification).options(
            joinedload(AlertNotification.alert).joinedload(PriceAlert.product)
        ).filter(AlertNotification.id == notification_id).first()
        if not notif:
            raise EntityNotFoundError("AlertNotification", notification_id)

        notif.is_acknowledged = True
        db.commit()
        db.refresh(notif)

        return AlertNotificationResponse(
            id=notif.id,
            alert_id=notif.alert_id,
            product_id=notif.alert.product_id if notif.alert else None,
            product_title=notif.alert.product.title if notif.alert and notif.alert.product else None,
            observation_id=notif.observation_id,
            alert_type=notif.alert.alert_type if notif.alert else "unknown",
            severity=notif.alert.severity if notif.alert else "medium",
            message=notif.message,
            evidence_payload=notif.evidence_payload or {},
            is_acknowledged=notif.is_acknowledged,
            triggered_at=notif.triggered_at,
        )
