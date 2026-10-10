"""Health Check API Router."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.schemas.common import APIResponse, HealthStatus

router = APIRouter(tags=["System Health"])


@router.get("/health", response_model=APIResponse[HealthStatus])
def get_health(db: Session = Depends(get_db)) -> APIResponse[HealthStatus]:
    """Returns application health and database connection status."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    status_data = HealthStatus(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database_connected=db_ok,
        timestamp=datetime.now(timezone.utc),
    )
    return APIResponse(success=True, data=status_data)
