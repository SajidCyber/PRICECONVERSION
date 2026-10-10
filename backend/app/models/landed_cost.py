"""Landed Cost Assumption & Tariff Configuration ORM Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class LandedCostConfig(Base):
    """Represents trade tariff, tax, shipping, and insurance parameters per country and category."""

    __tablename__ = "landed_cost_configs"
    __table_args__ = (
        UniqueConstraint("country_id", "category", name="uq_country_category_config"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country_id = Column(String(2), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, default="*")  # '*' wildcard or exact category

    # Duty & Tax Rates (ad valorem fractions)
    customs_duty_rate = Column(Numeric(5, 4), nullable=False, default=0.0500)  # 0.05 = 5%
    import_tax_rate = Column(Numeric(5, 4), nullable=False, default=0.1000)  # 0.10 = 10% (VAT / GST)
    de_minimis_threshold = Column(Numeric(10, 2), nullable=False, default=0.00)  # In local destination currency

    # Logistics & Handling Defaults (in destination currency or USD base)
    default_freight = Column(Numeric(10, 2), nullable=False, default=15.00)
    insurance_rate = Column(Numeric(5, 4), nullable=False, default=0.0100)  # 1% of item value
    handling_fee = Column(Numeric(10, 2), nullable=False, default=5.00)

    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    country = relationship("Country", back_populates="landed_cost_configs")

    def __repr__(self) -> str:
        return f"<LandedCostConfig {self.country_id} (cat={self.category}): duty={self.customs_duty_rate}, tax={self.import_tax_rate}>"
