"""Scraping Job and Dataset Ingestion Batch Telemetry ORM Models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class ScrapingJob(Base):
    """Represents an asynchronous or scheduled scraping execution task."""

    __tablename__ = "scraping_jobs"
    __table_args__ = (
        Index("idx_job_status", "status"),
        Index("idx_job_created", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    marketplace_id = Column(String(50), ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued")  # 'queued', 'running', 'success', 'partial_failure', 'failed'

    target_category = Column(String(100), nullable=True)
    target_url = Column(String(1000), nullable=True)

    items_discovered = Column(Integer, nullable=False, default=0)
    items_extracted = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    error_log = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Relationships
    marketplace = relationship("Marketplace", back_populates="scraping_jobs")
    observations = relationship("PriceObservation", back_populates="scraping_job")

    def __repr__(self) -> str:
        return f"<ScrapingJob {self.id[:8]} target={self.marketplace_id} status={self.status}>"


class DataImportBatch(Base):
    """Represents a batch ingestion event of an external dataset (CSV/JSON/Public Feed)."""

    __tablename__ = "data_import_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name = Column(String(100), nullable=False)  # e.g., 'dummyjson_laptops', 'kaggle_crossborder.csv'
    source_type = Column(String(50), nullable=False, default="imported_dataset")  # 'imported_dataset', 'demo_api', 'synthetic_seed'

    record_count = Column(Integer, nullable=False, default=0)
    inserted_count = Column(Integer, nullable=False, default=0)
    duplicate_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)

    summary_log = Column(JSON, nullable=False, default=dict)
    imported_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    observations = relationship("PriceObservation", back_populates="import_batch")

    def __repr__(self) -> str:
        return f"<DataImportBatch {self.id[:8]} source={self.source_name} ({self.inserted_count}/{self.record_count} inserted)>"
