"""Executive Dashboard and Platform KPIs API Router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.analytics.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Executive Dashboard"])


@router.get("/summary", response_model=APIResponse[DashboardSummaryResponse])
def get_dashboard_summary(db: Session = Depends(get_db)) -> APIResponse[DashboardSummaryResponse]:
    """Returns aggregated executive KPIs, platform health metrics, active alerts, and cross-border opportunities."""
    summary = DashboardService.get_summary(db=db)
    return APIResponse(success=True, data=summary)
