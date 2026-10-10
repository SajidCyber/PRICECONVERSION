"""Price Alerts and Triggered Notification ORM Models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class PriceAlert(Base):
    """Represents a rule-based price or market condition alert configuration."""

    __tablename__ = "price_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # 'threshold_below', 'pct_change_drop', 'landed_cost_breach', 'out_of_stock'
    condition_value = Column(Numeric(12, 2), nullable=False)  # target price or target percentage
    severity = Column(String(20), nullable=False, default="medium")  # 'low', 'medium', 'high', 'critical'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="alerts")
    notifications = relationship("AlertNotification", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PriceAlert {self.id[:8]} prod={self.product_id[:8]} ({self.alert_type} @ {self.condition_value})>"


class AlertNotification(Base):
    """Represents an instantiated alert event triggered by an observed price change."""

    __tablename__ = "alert_notifications"
    __table_args__ = (
        Index("idx_notification_time", "triggered_at"),
        Index("idx_notification_ack", "is_acknowledged"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("price_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_id = Column(String(36), ForeignKey("price_observations.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    evidence_payload = Column(JSON, nullable=False, default=dict)  # Snapshot of triggering price and delta
    is_acknowledged = Column(Boolean, nullable=False, default=False)
    triggered_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    alert = relationship("PriceAlert", back_populates="notifications")
    observation = relationship("PriceObservation", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<AlertNotification {self.id[:8]} alert={self.alert_id[:8]} (Ack={self.is_acknowledged})>"
