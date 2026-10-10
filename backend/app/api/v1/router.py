"""Central API v1 Router."""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.scraping import router as scraping_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.matching import router as matching_router
from app.api.v1.pricing import router as pricing_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.reports import router as reports_router
from app.api.v1.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["System Health"])
api_router.include_router(scraping_router)
api_router.include_router(ingestion_router)
api_router.include_router(matching_router)
api_router.include_router(pricing_router)
api_router.include_router(intelligence_router)
api_router.include_router(alerts_router)
api_router.include_router(reports_router)
api_router.include_router(dashboard_router)


