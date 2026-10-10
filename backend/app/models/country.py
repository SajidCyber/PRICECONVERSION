"""Country and Market Profile ORM Model."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Country(Base):
    """Represents a sovereign country or regional market jurisdiction."""

    __tablename__ = "countries"

    id = Column(String(2), primary_key=True, index=True)  # ISO 3166-1 alpha-2 (e.g., 'US', 'GB', 'IN')
    name = Column(String(100), nullable=False)
    currency_code = Column(String(3), nullable=False)  # ISO 4217 (e.g., 'USD', 'GBP', 'INR')
    currency_symbol = Column(String(10), nullable=False, default="$")
    region = Column(String(50), nullable=False, default="Global")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    marketplaces = relationship("Marketplace", back_populates="country", cascade="all, delete-orphan")
    landed_cost_configs = relationship("LandedCostConfig", back_populates="country", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Country {self.id} - {self.name} ({self.currency_code})>"
