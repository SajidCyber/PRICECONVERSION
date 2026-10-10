"""Product Cross-Listing Matching API Router."""

from typing import Any, Dict, List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundError
from app.models import Product, ProductListing, ProductMatch
from app.schemas.common import APIResponse, MetaInfo
from app.schemas.matching import BatchMatchResponse, MatchReviewUpdate, ProductMatchResponse
from app.services.matcher.engine import ProductMatchingEngine

router = APIRouter(prefix="/matching", tags=["Cross-Marketplace Product Matching"])


@router.get("/pairs", response_model=APIResponse[List[ProductMatchResponse]])
def list_product_matches(
    product_id: Optional[str] = Query(None, description="Filter by canonical product ID"),
    marketplace_id: Optional[str] = Query(None, description="Filter by marketplace ID"),
    status: Optional[str] = Query(None, description="Filter by status ('confirmed', 'probable', 'uncertain', 'rejected')"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum confidence score threshold"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> APIResponse[List[ProductMatchResponse]]:
    """Lists matched product-listing pairs with similarity breakdown and evidence."""
    query = (
        db.query(ProductMatch)
        .join(Product, ProductMatch.product_id == Product.id)
        .join(ProductListing, ProductMatch.listing_id == ProductListing.id)
        .options(joinedload(ProductMatch.product), joinedload(ProductMatch.listing))
    )

    if product_id:
        query = query.filter(ProductMatch.product_id == product_id)
    if marketplace_id:
        query = query.filter(ProductListing.marketplace_id == marketplace_id)
    if status:
        query = query.filter(ProductMatch.status == status)
    if min_confidence is not None:
        query = query.filter(ProductMatch.confidence_score >= Decimal(str(min_confidence)))

    total = query.count()
    matches = query.order_by(ProductMatch.confidence_score.desc()).offset(offset).limit(limit).all()

    data = []
    for m in matches:
        data.append(
            ProductMatchResponse(
                id=m.id,
                product_id=m.product.id,
                product_title=m.product.title,
                product_brand=m.product.brand,
                product_category=m.product.category,
                listing_id=m.listing.id,
                listing_title=m.listing.listing_title,
                marketplace_id=m.listing.marketplace_id,
                marketplace_name=m.listing.marketplace_id.replace("_", " ").title(),
                currency_code=m.listing.currency_code,
                confidence_score=m.confidence_score,
                match_type=m.match_type,
                match_evidence=m.match_evidence,
                status=m.status,
                created_at=m.created_at,
            )
        )

    return APIResponse(success=True, data=data, meta=MetaInfo(total=total, limit=limit, offset=offset))


@router.post("/run", response_model=APIResponse[BatchMatchResponse])
def run_product_matching(db: Session = Depends(get_db)) -> APIResponse[BatchMatchResponse]:
    """Triggers automated cross-marketplace product matching across all listings."""
    result = ProductMatchingEngine.run_batch_matching(db)
    return APIResponse(success=True, data=result)


@router.patch("/pairs/{match_id}", response_model=APIResponse[ProductMatchResponse])
def update_match_review(
    match_id: str,
    payload: MatchReviewUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductMatchResponse]:
    """Reviews or overrides a product match status ('confirmed', 'probable', 'uncertain', 'rejected')."""
    match_record = (
        db.query(ProductMatch)
        .options(joinedload(ProductMatch.product), joinedload(ProductMatch.listing))
        .filter(ProductMatch.id == match_id)
        .first()
    )
    if not match_record:
        raise EntityNotFoundError("ProductMatch", match_id)

    valid_statuses = {"confirmed", "probable", "uncertain", "rejected"}
    if payload.status.lower() not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of {valid_statuses}",
        )

    match_record.status = payload.status.lower()
    if payload.status.lower() == "rejected":
        # Decouple listing from product if rejected
        if match_record.listing and match_record.listing.product_id == match_record.product_id:
            match_record.listing.product_id = None
    elif payload.status.lower() in {"confirmed", "probable"}:
        if match_record.listing:
            match_record.listing.product_id = match_record.product_id

    db.commit()
    db.refresh(match_record)

    data = ProductMatchResponse(
        id=match_record.id,
        product_id=match_record.product.id,
        product_title=match_record.product.title,
        product_brand=match_record.product.brand,
        product_category=match_record.product.category,
        listing_id=match_record.listing.id,
        listing_title=match_record.listing.listing_title,
        marketplace_id=match_record.listing.marketplace_id,
        marketplace_name=match_record.listing.marketplace_id.replace("_", " ").title(),
        currency_code=match_record.listing.currency_code,
        confidence_score=match_record.confidence_score,
        match_type=match_record.match_type,
        match_evidence=match_record.match_evidence,
        status=match_record.status,
        created_at=match_record.created_at,
    )
    return APIResponse(success=True, data=data)


@router.delete("/pairs/{match_id}", response_model=APIResponse[Dict[str, Any]])
def delete_product_match(match_id: str, db: Session = Depends(get_db)) -> APIResponse[Dict[str, Any]]:
    """Deletes/decouples a product match relationship."""
    match_record = db.query(ProductMatch).filter(ProductMatch.id == match_id).first()
    if not match_record:
        raise EntityNotFoundError("ProductMatch", match_id)

    db.delete(match_record)
    db.commit()
    return APIResponse(success=True, data={"deleted_match_id": match_id, "message": "Match pair successfully removed."})
