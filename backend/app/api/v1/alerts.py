"""Price Alerts and Notification Management API Router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.alert import (
    AlertEvaluationResult,
    AlertNotificationResponse,
    PriceAlertCreate,
    PriceAlertResponse,
    PriceAlertUpdate,
)
from app.schemas.common import APIResponse
from app.services.alerts.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Price Alerts & Notifications"])


@router.get("", response_model=APIResponse[List[PriceAlertResponse]])
def list_price_alerts(
    product_id: Optional[str] = Query(None, description="Filter alerts by canonical product ID"),
    active_only: bool = Query(False, description="Filter for active rules only"),
    db: Session = Depends(get_db),
) -> APIResponse[List[PriceAlertResponse]]:
    """Lists configured price alert rules."""
    alerts = AlertService.list_alerts(db=db, product_id=product_id, active_only=active_only)
    return APIResponse(success=True, data=alerts)


@router.post("", response_model=APIResponse[PriceAlertResponse], status_code=status.HTTP_201_CREATED)
def create_price_alert(
    payload: PriceAlertCreate,
    db: Session = Depends(get_db),
) -> APIResponse[PriceAlertResponse]:
    """Creates a new price alert rule."""
    alert = AlertService.create_alert(db=db, payload=payload)
    return APIResponse(success=True, data=alert)


@router.put("/{alert_id}", response_model=APIResponse[PriceAlertResponse])
def update_price_alert(
    alert_id: str,
    payload: PriceAlertUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[PriceAlertResponse]:
    """Updates an existing price alert rule."""
    alert = AlertService.update_alert(db=db, alert_id=alert_id, payload=payload)
    return APIResponse(success=True, data=alert)


@router.delete("/{alert_id}", response_model=APIResponse[dict])
def delete_price_alert(
    alert_id: str,
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    """Deletes a price alert rule."""
    AlertService.delete_alert(db=db, alert_id=alert_id)
    return APIResponse(success=True, data={"deleted": True, "alert_id": alert_id})


@router.post("/evaluate", response_model=APIResponse[AlertEvaluationResult])
def trigger_alert_evaluation(
    product_id: Optional[str] = Query(None, description="Optional canonical product UUID to evaluate"),
    db: Session = Depends(get_db),
) -> APIResponse[AlertEvaluationResult]:
    """Triggers an immediate evaluation run of active alert rules against latest observation data."""
    result = AlertService.evaluate_alerts(db=db, product_id=product_id)
    return APIResponse(success=True, data=result)


@router.get("/notifications", response_model=APIResponse[List[AlertNotificationResponse]])
def list_alert_notifications(
    unacknowledged_only: bool = Query(False, description="Filter for unread/unacknowledged notifications only"),
    limit: int = Query(50, ge=1, le=200, description="Max notifications to retrieve"),
    db: Session = Depends(get_db),
) -> APIResponse[List[AlertNotificationResponse]]:
    """Retrieves triggered price and stock alert notification events."""
    notifications = AlertService.list_notifications(
        db=db, unacknowledged_only=unacknowledged_only, limit=limit
    )
    return APIResponse(success=True, data=notifications)


@router.patch("/notifications/{notification_id}/read", response_model=APIResponse[AlertNotificationResponse])
def acknowledge_alert_notification(
    notification_id: str,
    db: Session = Depends(get_db),
) -> APIResponse[AlertNotificationResponse]:
    """Marks a specific alert notification as acknowledged/read."""
    notif = AlertService.acknowledge_notification(db=db, notification_id=notification_id)
    return APIResponse(success=True, data=notif)
