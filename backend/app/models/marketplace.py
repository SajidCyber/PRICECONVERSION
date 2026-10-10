"""Marketplace Entity ORM Model."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Marketplace(Base):
    """Represents an e-commerce channel, platform, or scraping target domain."""

    __tablename__ = "marketplaces"

    id = Column(String(50), primary_key=True, index=True)  # e.g., 'amazon_us', 'amazon_uk', 'books_to_scrape'
    name = Column(String(100), nullable=False)
    country_id = Column(String(2), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False)
    base_url = Column(String(255), nullable=False)
    adapter_name = Column(String(50), nullable=False)  # Strategy adapter key
    currency_code = Column(String(3), nullable=False, default="USD")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    country = relationship("Country", back_populates="marketplaces")
    listings = relationship("ProductListing", back_populates="marketplace", cascade="all, delete-orphan")
    scraping_jobs = relationship("ScrapingJob", back_populates="marketplace", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Marketplace {self.id} - {self.name} ({self.country_id})>"
