"""Pydantic schemas for Price Alerts, Rule Triggers, and Notifications."""

from decimal import Decimal
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PriceAlertCreate(BaseModel):
    """Payload to create a new price monitoring alert rule."""

    product_id: str
    alert_type: str = Field(..., description="'threshold_below', 'pct_change_drop', 'landed_cost_breach', 'out_of_stock'")
    condition_value: Decimal = Field(..., description="Target numeric price or percentage threshold")
    severity: str = Field("medium", description="'low', 'medium', 'high', 'critical'")
    is_active: bool = True


class PriceAlertUpdate(BaseModel):
    """Payload to update an existing price alert rule."""

    alert_type: Optional[str] = None
    condition_value: Optional[Decimal] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None


class PriceAlertResponse(BaseModel):
    """DTO for a configured price alert rule."""

    id: str
    product_id: str
    product_title: Optional[str] = None
    alert_type: str
    condition_value: Decimal
    severity: str
    is_active: bool
    created_at: datetime
    notifications_count: int = 0


class AlertNotificationResponse(BaseModel):
    """DTO for a triggered price alert event."""

    id: str
    alert_id: str
    product_id: Optional[str] = None
    product_title: Optional[str] = None
    observation_id: str
    alert_type: str
    severity: str
    message: str
    evidence_payload: Dict[str, Any]
    is_acknowledged: bool
    triggered_at: datetime


class AlertEvaluationResult(BaseModel):
    """Result summary of an automated alert evaluation run."""

    rules_evaluated: int
    alerts_triggered: int
    new_notifications: List[AlertNotificationResponse]
