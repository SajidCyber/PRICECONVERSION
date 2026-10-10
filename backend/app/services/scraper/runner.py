"""Scraping Job Execution Runner."""

import traceback
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.core.exceptions import ScrapingError
from app.core.logging_config import logger
from app.models import PriceObservation, Product, ProductListing, ScrapingJob
from app.services.scraper.registry import scraper_registry


class ScrapingRunnerService:
    """Orchestrates job execution, adapter extraction, and database persistence."""

    @staticmethod
    async def run_job(
        db: Session,
        marketplace_id: str,
        category: Optional[str] = None,
        target_url: Optional[str] = None,
        max_items: int = 20,
    ) -> ScrapingJob:
        """Executes a complete scraping job run against a target marketplace."""
        # 1. Create ScrapingJob in DB
        job = ScrapingJob(
            marketplace_id=marketplace_id,
            status="running",
            target_category=category,
            target_url=target_url,
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info("Started ScrapingJob %s for marketplace '%s'...", job.id, marketplace_id)

        try:
            adapter = scraper_registry.get_adapter(marketplace_id)
            extracted_items = await adapter.fetch_catalog(
                category=category,
                max_items=max_items,
                custom_url=target_url,
            )

            job.items_discovered = len(extracted_items)
            extracted_count = 0
            error_count = 0
            now = datetime.now(timezone.utc)

            for item in extracted_items:
                try:
                    # 1. Find or create ProductListing
                    listing = (
                        db.query(ProductListing)
                        .filter(
                            ProductListing.marketplace_id == marketplace_id,
                            ProductListing.external_id == item.external_id,
                        )
                        .first()
                    )

                    if not listing:
                        # Auto-create or link canonical product if needed
                        product = (
                            db.query(Product)
                            .filter(Product.title.ilike(f"%{item.title[:40]}%"))
                            .first()
                        )
                        if not product:
                            product = Product(
                                title=item.title,
                                brand=item.brand or "Unknown",
                                category=item.category or "General",
                                image_url=item.image_url,
                                target_base_price=item.price,
                                base_currency=item.currency_code,
                            )
                            db.add(product)
                            db.flush()

                        listing = ProductListing(
                            product_id=product.id,
                            marketplace_id=marketplace_id,
                            external_id=item.external_id,
                            listing_title=item.title,
                            listing_url=item.url,
                            currency_code=item.currency_code,
                            seller_name=item.brand or "Marketplace Seller",
                        )
                        db.add(listing)
                        db.flush()

                    # 2. Append immutable PriceObservation
                    observation = PriceObservation(
                        listing_id=listing.id,
                        scraping_job_id=job.id,
                        listed_price=item.price,
                        currency_code=item.currency_code,
                        shipping_price=item.shipping_price,
                        discount_pct=item.discount_pct,
                        availability_status=item.availability_status,
                        rating=item.rating,
                        review_count=item.review_count,
                        data_provenance=item.data_provenance,
                        raw_payload_snippet=item.raw_snippet,
                        observed_at=now,
                    )
                    db.add(observation)
                    extracted_count += 1
                except Exception as ex:
                    logger.warning("Failed to store item %s: %s", item.external_id, str(ex))
                    error_count += 1

            db.commit()

            job.items_extracted = extracted_count
            job.error_count = error_count
            job.finished_at = datetime.now(timezone.utc)
            job.status = "success" if error_count == 0 else "partial_failure"
            db.commit()
            db.refresh(job)

            logger.info(
                "Completed ScrapingJob %s: %d extracted, %d errors. Status: %s",
                job.id,
                extracted_count,
                error_count,
                job.status,
            )
            return job

        except Exception as e:
            logger.error("ScrapingJob %s failed fatally: %s", job.id, str(e))
            db.rollback()
            job.status = "failed"
            job.error_log = f"{str(e)}\n{traceback.format_exc()}"
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(job)
            raise ScrapingError(f"Job execution failed: {str(e)}", details={"job_id": job.id})
