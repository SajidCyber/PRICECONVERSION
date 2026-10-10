"""Report and Dataset Export API Router."""

from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.export.export_service import ExportService

router = APIRouter(prefix="/reports", tags=["Reports & Dataset Exports"])


@router.get("/export/comparison/csv")
def export_comparison_matrix_csv(
    destination_country: str = Query("US", min_length=2, max_length=2, description="Destination target country"),
    reporting_currency: str = Query("USD", min_length=3, max_length=3, description="Output reporting currency"),
    db: Session = Depends(get_db),
) -> Response:
    """Exports full catalog cross-border landed cost comparison matrix as a CSV attachment."""
    csv_data = ExportService.export_comparison_matrix_csv(
        db=db,
        destination_country=destination_country,
        reporting_currency=reporting_currency,
    )
    filename = f"pricing_comparison_{destination_country.lower()}_{reporting_currency.lower()}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/history/{product_id}/csv")
def export_product_history_csv(
    product_id: str,
    reporting_currency: str = Query("USD", min_length=3, max_length=3, description="Reporting currency"),
    days: int = Query(30, ge=0, le=365, description="Lookback window in days"),
    db: Session = Depends(get_db),
) -> Response:
    """Exports multi-market historical price time series for a product as a CSV attachment."""
    csv_data = ExportService.export_product_history_csv(
        db=db,
        product_id=product_id,
        reporting_currency=reporting_currency,
        days=days,
    )
    filename = f"product_history_{product_id[:8]}_{reporting_currency.lower()}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/opportunities/csv")
def export_arbitrage_opportunities_csv(
    min_margin_pct: float = Query(15.0, ge=1.0, le=90.0, description="Minimum profit margin percentage"),
    reporting_currency: str = Query("USD", min_length=3, max_length=3, description="Reporting currency"),
    db: Session = Depends(get_db),
) -> Response:
    """Exports detected cross-border price arbitrage opportunities as a CSV attachment."""
    csv_data = ExportService.export_opportunities_csv(
        db=db,
        min_margin_pct=Decimal(str(min_margin_pct)),
        reporting_currency=reporting_currency,
    )
    filename = f"export_arbitrage_opportunities_{reporting_currency.lower()}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
