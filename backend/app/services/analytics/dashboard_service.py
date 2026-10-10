"""Dashboard Summary and KPI Aggregation Service."""

from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models import (
    AlertNotification,
    Marketplace,
    PriceAlert,
    PriceObservation,
    Product,
    ProductListing,
    ScrapingJob,
)
from app.schemas.dashboard import DashboardSummaryResponse, ScrapingHealthDTO
from app.services.analytics.positioning import MarketPositioningService


class DashboardService:
    """Aggregates executive KPIs, system health metrics, active alerts, and cross-border opportunities."""

    @classmethod
    def get_summary(cls, db: Session) -> DashboardSummaryResponse:
        """Computes platform-wide analytics and returns unified executive summary."""
        total_prods = db.query(Product).count()
        total_mkts = db.query(Marketplace).count()
        total_listings = db.query(ProductListing).count()
        total_obs = db.query(PriceObservation).count()
        active_alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).count()
        unack_notifs = db.query(AlertNotification).filter(AlertNotification.is_acknowledged == False).count()

        # Anomalies and Arbitrage opportunities
        anomalies = MarketPositioningService.detect_anomalies(db, threshold_pct=Decimal("15.0"))
        opportunities_resp = MarketPositioningService.detect_export_opportunities(
            db, min_margin_pct=Decimal("5.0")
        )

        # Scraping Health
        jobs = db.query(ScrapingJob).all()
        total_jobs = len(jobs)
        completed_jobs = sum(1 for j in jobs if j.status in ["completed", "success"])
        failed_jobs = sum(1 for j in jobs if j.status == "failed")
        active_jobs = sum(1 for j in jobs if j.status in ["queued", "running"])
        total_extracted = sum(j.items_extracted or 0 for j in jobs)

        success_rate = (
            Decimal(f"{((completed_jobs / (completed_jobs + failed_jobs)) * 100):.1f}")
            if (completed_jobs + failed_jobs) > 0
            else Decimal("100.0")
        )

        scraping_health = ScrapingHealthDTO(
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            active_jobs=active_jobs,
            success_rate_pct=success_rate,
            total_records_extracted=total_extracted,
        )

        # Recent activities
        recent_activities: List[Dict[str, Any]] = []

        # 1. Latest alerts
        recent_notifs = (
            db.query(AlertNotification)
            .order_by(AlertNotification.triggered_at.desc())
            .limit(5)
            .all()
        )
        for n in recent_notifs:
            recent_activities.append({
                "type": "alert_triggered",
                "title": f"Alert Triggered ({n.alert.alert_type if n.alert else 'alert'})",
                "message": n.message,
                "timestamp": n.triggered_at.isoformat(),
                "severity": n.alert.severity if n.alert else "medium",
            })

        # 2. Latest scraping jobs
        recent_jobs = (
            db.query(ScrapingJob)
            .order_by(ScrapingJob.created_at.desc())
            .limit(5)
            .all()
        )
        for j in recent_jobs:
            recent_activities.append({
                "type": "scraping_job",
                "title": f"Scraping Job: {j.marketplace_id}",
                "message": f"Job status {j.status}, extracted {j.items_extracted} records.",
                "timestamp": j.created_at.isoformat(),
                "severity": "high" if j.status == "failed" else "low",
            })

        # Sort combined activity timeline DESC
        recent_activities.sort(key=lambda a: a["timestamp"], reverse=True)
        recent_activities = recent_activities[:10]

        return DashboardSummaryResponse(
            total_products=total_prods,
            total_marketplaces=total_mkts,
            total_listings=total_listings,
            total_observations=total_obs,
            active_alerts_count=active_alerts,
            unacknowledged_notifications_count=unack_notifs,
            total_anomalies_count=len(anomalies),
            total_export_opportunities_count=opportunities_resp.total_opportunities_found,
            scraping_health=scraping_health,
            recent_activities=recent_activities,
        )
