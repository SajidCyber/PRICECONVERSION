"""Dataset Ingestion API Router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import DataIngestionError
from app.models.job import DataImportBatch
from app.schemas.common import APIResponse, MetaInfo
from app.schemas.scraper import ImportSummaryResponse
from app.services.ingestion.importer import DataIngestionService
from app.services.scraper.registry import scraper_registry

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & Dataset Importers"])


@router.post("/upload-csv", response_model=APIResponse[ImportSummaryResponse], status_code=status.HTTP_201_CREATED)
async def upload_csv_dataset(
    file: UploadFile = File(..., description="CSV dataset file to import"),
    db: Session = Depends(get_db),
) -> APIResponse[ImportSummaryResponse]:
    """Imports and validates product listings and price observations from an uploaded CSV file."""
    if not file.filename.lower().endswith(".csv"):
        raise DataIngestionError("Only .csv files are supported by this endpoint.")

    content_bytes = await file.read()
    try:
        csv_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1")

    summary = DataIngestionService.import_csv(
        db=db,
        csv_content=csv_text,
        source_name=file.filename,
        source_type="imported_dataset",
    )
    return APIResponse(success=True, data=summary)


@router.post("/import-sample-feed", response_model=APIResponse[ImportSummaryResponse], status_code=status.HTTP_201_CREATED)
async def import_sample_feed(
    source: str = Query("dummyjson", description="'dummyjson' or 'fakestore'"),
    category: Optional[str] = Query(None, description="Optional category filter (e.g. 'laptops', 'smartphones')"),
    max_items: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[ImportSummaryResponse]:
    """Fetches public structured e-commerce catalog items (DummyJSON / FakeStore) and ingests into catalog."""
    source_key = "dummyjson_store" if source.lower() == "dummyjson" else "fakestore"
    adapter = scraper_registry.get_adapter(source_key)

    extracted_items = await adapter.fetch_catalog(category=category, max_items=max_items)
    # Convert DTOs to dictionaries for IngestionService
    records = [
        {
            "title": item.title,
            "price": str(item.price),
            "currency": item.currency_code,
            "marketplace_id": item.data_provenance if item.data_provenance != "demo_api" else source_key,
            "external_id": item.external_id,
            "brand": item.brand,
            "category": item.category,
            "image_url": item.image_url,
            "shipping": str(item.shipping_price),
            "discount_pct": str(item.discount_pct),
            "availability_status": item.availability_status,
            "rating": str(item.rating) if item.rating else None,
            "url": item.url,
        }
        for item in extracted_items
    ]

    summary = DataIngestionService.import_json(
        db=db,
        json_content=records,
        source_name=f"{source_key}_{category or 'all'}",
        source_type="demo_api",
    )
    return APIResponse(success=True, data=summary)


@router.get("/batches", response_model=APIResponse[List[ImportSummaryResponse]])
def list_import_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> APIResponse[List[ImportSummaryResponse]]:
    """Lists historical dataset import batches and summary reports."""
    query = db.query(DataImportBatch)
    total = query.count()
    batches = query.order_by(DataImportBatch.imported_at.desc()).offset(offset).limit(limit).all()

    data = [
        ImportSummaryResponse(
            batch_id=b.id,
            source_name=b.source_name,
            source_type=b.source_type,
            record_count=b.record_count,
            inserted_count=b.inserted_count,
            duplicate_count=b.duplicate_count,
            rejected_count=b.rejected_count,
            summary_log=b.summary_log,
            imported_at=b.imported_at,
        )
        for b in batches
    ]
    return APIResponse(success=True, data=data, meta=MetaInfo(total=total, limit=limit, offset=offset))
