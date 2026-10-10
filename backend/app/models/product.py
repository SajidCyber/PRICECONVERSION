"""Canonical Product ORM Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Product(Base):
    """Represents a canonical product definition tracked across international markets."""

    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku = Column(String(100), unique=True, index=True, nullable=True)  # Global SKU / GTIN / Model No
    title = Column(String(255), index=True, nullable=False)
    brand = Column(String(100), index=True, nullable=True)
    category = Column(String(100), index=True, nullable=False, default="General")
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    target_base_price = Column(Numeric(12, 2), nullable=True)  # Reference benchmark price
    base_currency = Column(String(3), nullable=False, default="USD")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    listings = relationship("ProductListing", back_populates="product", cascade="all, delete-orphan")
    matches = relationship("ProductMatch", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Product {self.id[:8]} - {self.title[:30]} ({self.category})>"
