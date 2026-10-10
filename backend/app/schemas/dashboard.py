"""Pydantic schemas for Executive Dashboard Overview and Platform KPIs."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ScrapingHealthDTO(BaseModel):
    """Aggregated status of scraping infrastructure and jobs."""

    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    active_jobs: int
    success_rate_pct: Decimal
    total_records_extracted: int


class DashboardSummaryResponse(BaseModel):
    """Executive KPI summary and platform health status."""

    total_products: int
    total_marketplaces: int
    total_listings: int
    total_observations: int
    active_alerts_count: int
    unacknowledged_notifications_count: int
    total_anomalies_count: int
    total_export_opportunities_count: int
    scraping_health: ScrapingHealthDTO
    recent_activities: List[Dict[str, Any]]
