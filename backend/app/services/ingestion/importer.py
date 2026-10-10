"""Data Ingestion Service for CSV, JSON, and Dataset Imports."""

import csv
import io
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from app.core.exceptions import DataIngestionError
from app.core.logging_config import logger
from app.models import (
    Country,
    DataImportBatch,
    Marketplace,
    PriceObservation,
    Product,
    ProductListing,
)
from app.schemas.scraper import ImportSummaryResponse


class DataIngestionService:
    """Ingests, validates, normalizes, and persists external datasets."""

    REQUIRED_FIELDS = {"title", "price", "currency", "marketplace_id", "external_id"}

    @classmethod
    def import_csv(
        cls,
        db: Session,
        csv_content: str,
        source_name: str = "uploaded_dataset.csv",
        source_type: str = "imported_dataset",
    ) -> ImportSummaryResponse:
        """Parses and ingests CSV string content."""
        reader = csv.DictReader(io.StringIO(csv_content))
        if not reader.fieldnames:
            raise DataIngestionError("CSV file is empty or missing headers.")

        # Normalize fieldnames to lowercase stripped
        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames}
        missing_req = [f for f in cls.REQUIRED_FIELDS if f not in normalized_headers]
        if missing_req:
            raise DataIngestionError(f"CSV missing mandatory columns: {missing_req}")

        rows = []
        for raw_row in reader:
            row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
            rows.append(row)

        return cls._process_records(db, rows, source_name=source_name, source_type=source_type)

    @classmethod
    def import_json(
        cls,
        db: Session,
        json_content: Union[str, List[Dict[str, Any]]],
        source_name: str = "uploaded_dataset.json",
        source_type: str = "imported_dataset",
    ) -> ImportSummaryResponse:
        """Parses and ingests JSON content."""
        if isinstance(json_content, str):
            try:
                data = json.loads(json_content)
            except Exception as e:
                raise DataIngestionError(f"Invalid JSON payload: {str(e)}")
        else:
            data = json_content

        if not isinstance(data, list):
            raise DataIngestionError("JSON dataset must be an array of product listing objects.")

        normalized_rows = []
        for item in data:
            row = {str(k).strip().lower(): v for k, v in item.items()}
            normalized_rows.append(row)

        return cls._process_records(db, normalized_rows, source_name=source_name, source_type=source_type)

    @classmethod
    def _process_records(
        cls,
        db: Session,
        rows: List[Dict[str, Any]],
        source_name: str,
        source_type: str,
    ) -> ImportSummaryResponse:
        """Processes normalized rows, validating types and persisting models."""
        now = datetime.now(timezone.utc)
        batch = DataImportBatch(
            source_name=source_name,
            source_type=source_type,
            record_count=len(rows),
        )
        db.add(batch)
        db.flush()

        inserted_count = 0
        duplicate_count = 0
        rejected_count = 0
        rejection_reasons = []

        # Cache known marketplaces to auto-create missing if needed
        known_marketplaces = {m.id: m for m in db.query(Marketplace).all()}

        seen_listings_in_batch = set()

        for idx, row in enumerate(rows, start=1):
            try:
                # 1. Validate mandatory fields
                title = str(row.get("title", "")).strip()
                external_id = str(row.get("external_id", "")).strip()
                marketplace_id = str(row.get("marketplace_id", "")).strip().lower()
                currency = str(row.get("currency", row.get("currency_code", "USD"))).strip().upper()

                if not title or not external_id or not marketplace_id:
                    rejected_count += 1
                    rejection_reasons.append(f"Row {idx}: missing title, external_id, or marketplace_id")
                    continue

                # 2. Parse price
                raw_price = row.get("price")
                clean_price_str = re.sub(r"[^\d.]", "", str(raw_price))
                if not clean_price_str:
                    rejected_count += 1
                    rejection_reasons.append(f"Row {idx}: invalid price '{raw_price}'")
                    continue
                price = Decimal(clean_price_str)
                if price <= 0:
                    rejected_count += 1
                    rejection_reasons.append(f"Row {idx}: non-positive price {price}")
                    continue

                # Parse shipping & discount
                shipping = Decimal(re.sub(r"[^\d.]", "", str(row.get("shipping", row.get("shipping_price", 0)))) or "0.00")
                discount = Decimal(re.sub(r"[^\d.]", "", str(row.get("discount_pct", row.get("discount", 0)))) or "0.00")
                rating = Decimal(str(row.get("rating", 4.5))) if row.get("rating") else None
                availability = str(row.get("availability_status", row.get("availability", "in_stock"))).strip().lower()

                # Ensure marketplace exists
                if marketplace_id not in known_marketplaces:
                    # Auto-create generic marketplace
                    m_new = Marketplace(
                        id=marketplace_id,
                        name=marketplace_id.replace("_", " ").title(),
                        country_id="US",
                        base_url=f"https://{marketplace_id}.com",
                        adapter_name="generic_structured",
                        currency_code=currency,
                    )
                    db.add(m_new)
                    db.flush()
                    known_marketplaces[marketplace_id] = m_new

                # 3. Locate or create ProductListing
                listing = (
                    db.query(ProductListing)
                    .filter(
                        ProductListing.marketplace_id == marketplace_id,
                        ProductListing.external_id == external_id,
                    )
                    .first()
                )

                if not listing:
                    # Find or create Product
                    brand = str(row.get("brand", "Generic")).strip()
                    category = str(row.get("category", "General")).strip()
                    sku = str(row.get("sku", "")).strip() or None

                    product = None
                    if sku:
                        product = db.query(Product).filter(Product.sku == sku).first()
                    if not product:
                        product = db.query(Product).filter(Product.title.ilike(f"%{title[:40]}%")).first()

                    if not product:
                        product = Product(
                            sku=sku,
                            title=title,
                            brand=brand,
                            category=category,
                            image_url=row.get("image_url"),
                            target_base_price=price,
                            base_currency=currency,
                        )
                        db.add(product)
                        db.flush()
                    elif not product.sku and sku:
                        product.sku = sku
                        db.flush()

                    listing = ProductListing(
                        product_id=product.id,
                        marketplace_id=marketplace_id,
                        external_id=external_id,
                        listing_title=title,
                        listing_url=str(row.get("url", f"https://{marketplace_id}.com/item/{external_id}")),
                        currency_code=currency,
                        seller_name=row.get("seller_name", "Importer Feed"),
                    )
                    db.add(listing)
                    db.flush()

                # 4. Check for duplicate observation in same batch
                if listing.id in seen_listings_in_batch:
                    duplicate_count += 1
                    continue

                seen_listings_in_batch.add(listing.id)

                # 5. Append PriceObservation
                obs = PriceObservation(
                    listing_id=listing.id,
                    import_batch_id=batch.id,
                    listed_price=price,
                    currency_code=currency,
                    shipping_price=shipping,
                    discount_pct=discount,
                    availability_status=availability if availability in {"in_stock", "out_of_stock", "pre_order"} else "in_stock",
                    rating=rating,
                    data_provenance=source_type,
                    raw_payload_snippet=f"Imported from {source_name}",
                    observed_at=now,
                )
                db.add(obs)
                inserted_count += 1

            except Exception as e:
                rejected_count += 1
                rejection_reasons.append(f"Row {idx} processing error: {str(e)}")
                continue

        batch.inserted_count = inserted_count
        batch.duplicate_count = duplicate_count
        batch.rejected_count = rejected_count
        batch.summary_log = {
            "total_rows": len(rows),
            "inserted": inserted_count,
            "duplicate": duplicate_count,
            "rejected": rejected_count,
            "rejections": rejection_reasons[:20],
        }
        db.commit()
        db.refresh(batch)

        logger.info(
            "Batch %s completed: %d inserted, %d dupes, %d rejected from %d total rows.",
            batch.id,
            inserted_count,
            duplicate_count,
            rejected_count,
            len(rows),
        )

        return ImportSummaryResponse(
            batch_id=batch.id,
            source_name=batch.source_name,
            source_type=batch.source_type,
            record_count=batch.record_count,
            inserted_count=batch.inserted_count,
            duplicate_count=batch.duplicate_count,
            rejected_count=batch.rejected_count,
            summary_log=batch.summary_log,
            imported_at=batch.imported_at,
        )
