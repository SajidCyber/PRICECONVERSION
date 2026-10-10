"""Foreign Exchange Rate Observation ORM Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Index, Numeric, String
from app.core.database import Base


class ExchangeRate(Base):
    """Represents a foreign currency conversion rate snapshot with provenance metadata."""

    __tablename__ = "exchange_rates"
    __table_args__ = (
        Index("idx_fx_pair_time", "base_currency", "target_currency", "fetched_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    base_currency = Column(String(3), nullable=False, index=True)  # e.g., 'USD'
    target_currency = Column(String(3), nullable=False, index=True)  # e.g., 'EUR', 'GBP', 'INR'
    rate = Column(Numeric(18, 6), nullable=False)
    source = Column(String(100), nullable=False, default="open.er-api.com")
    is_fallback = Column(Boolean, nullable=False, default=False)
    fetched_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self) -> str:
        return f"<ExchangeRate {self.base_currency}->{self.target_currency} = {self.rate} ({self.source})>"
