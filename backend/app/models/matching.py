"""Product Cross-Listing Match Record ORM Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProductMatch(Base):
    """Represents a discovered or verified match between a canonical product and an external listing."""

    __tablename__ = "product_matches"
    __table_args__ = (
        UniqueConstraint("product_id", "listing_id", name="uq_product_listing_match"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = Column(String(36), ForeignKey("product_listings.id", ondelete="CASCADE"), nullable=False, index=True)

    confidence_score = Column(Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    match_type = Column(String(50), nullable=False)  # 'exact_sku', 'token_cosine', 'fuzzy_levenshtein', 'manual'
    match_evidence = Column(JSON, nullable=False, default=dict)  # Similarity breakdown and token details
    status = Column(String(20), nullable=False, default="confirmed")  # 'confirmed', 'probable', 'uncertain', 'rejected'
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="matches")
    listing = relationship("ProductListing", back_populates="matches")

    def __repr__(self) -> str:
        return f"<ProductMatch prod={self.product_id[:8]} -> listing={self.listing_id[:8]} ({self.confidence_score}%, {self.status})>"
