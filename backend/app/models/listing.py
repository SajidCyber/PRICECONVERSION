"""Marketplace Product Listing ORM Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProductListing(Base):
    """Represents a specific product listing on an external e-commerce channel."""

    __tablename__ = "product_listings"
    __table_args__ = (
        UniqueConstraint("marketplace_id", "external_id", name="uq_listing_marketplace_external"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    marketplace_id = Column(String(50), ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(100), nullable=False, index=True)  # ASIN, item id, slug
    listing_title = Column(String(500), nullable=False)
    listing_url = Column(String(1000), nullable=False)
    currency_code = Column(String(3), nullable=False)
    seller_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    product = relationship("Product", back_populates="listings")
    marketplace = relationship("Marketplace", back_populates="listings")
    observations = relationship("PriceObservation", back_populates="listing", cascade="all, delete-orphan")
    matches = relationship("ProductMatch", back_populates="listing", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ProductListing {self.id[:8]} - {self.listing_title[:30]} @ {self.marketplace_id}>"
