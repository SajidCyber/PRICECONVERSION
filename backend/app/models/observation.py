"""Immutable Price Observation ORM Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class PriceObservation(Base):
    """Represents a discrete, immutable historical price capture event."""

    __tablename__ = "price_observations"
    __table_args__ = (
        Index("idx_obs_listing_observed", "listing_id", "observed_at"),
        Index("idx_obs_provenance", "data_provenance"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id = Column(String(36), ForeignKey("product_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    scraping_job_id = Column(String(36), ForeignKey("scraping_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    import_batch_id = Column(String(36), ForeignKey("data_import_batches.id", ondelete="SET NULL"), nullable=True, index=True)

    # Pricing Metrics
    listed_price = Column(Numeric(12, 2), nullable=False)
    currency_code = Column(String(3), nullable=False)
    shipping_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    discount_pct = Column(Numeric(5, 2), nullable=False, default=0.00)

    # Stock & Reputation
    availability_status = Column(String(50), nullable=False, default="in_stock")  # 'in_stock', 'out_of_stock', 'pre_order'
    rating = Column(Numeric(3, 2), nullable=True)
    review_count = Column(Integer, nullable=True)

    # Provenance Tracking
    data_provenance = Column(String(50), nullable=False, default="live_scrape")  # 'live_scrape', 'imported_dataset', 'demo_api', 'synthetic_seed'
    raw_payload_snippet = Column(String(500), nullable=True)
    observed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    listing = relationship("ProductListing", back_populates="observations")
    scraping_job = relationship("ScrapingJob", back_populates="observations")
    import_batch = relationship("DataImportBatch", back_populates="observations")
    notifications = relationship("AlertNotification", back_populates="observation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PriceObservation {self.listed_price} {self.currency_code} ({self.data_provenance}) @ {self.observed_at}>"
