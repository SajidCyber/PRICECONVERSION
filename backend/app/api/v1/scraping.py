"""Scraping Operations API Router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundError
from app.models.job import ScrapingJob
from app.schemas.common import APIResponse, MetaInfo
from app.schemas.scraper import AdapterInfo, ScrapingJobCreate, ScrapingJobResponse
from app.services.scraper.registry import scraper_registry
from app.services.scraper.runner import ScrapingRunnerService

router = APIRouter(prefix="/scraping", tags=["Web Scraping Operations"])


@router.get("/adapters", response_model=APIResponse[List[AdapterInfo]])
def list_scraper_adapters() -> APIResponse[List[AdapterInfo]]:
    """Returns the list of registered scraping adapters and public catalog feeds."""
    adapters = scraper_registry.list_adapters()
    return APIResponse(success=True, data=adapters)


@router.post("/jobs", response_model=APIResponse[ScrapingJobResponse], status_code=status.HTTP_201_CREATED)
async def trigger_scraping_job(
    payload: ScrapingJobCreate,
    db: Session = Depends(get_db),
) -> APIResponse[ScrapingJobResponse]:
    """Triggers an immediate scraping run for a registered marketplace adapter."""
    job = await ScrapingRunnerService.run_job(
        db=db,
        marketplace_id=payload.marketplace_id,
        category=payload.category,
        target_url=payload.target_url,
        max_items=payload.max_items,
    )

    response_data = ScrapingJobResponse(
        id=job.id,
        marketplace_id=job.marketplace_id,
        status=job.status,
        target_category=job.target_category,
        target_url=job.target_url,
        items_discovered=job.items_discovered,
        items_extracted=job.items_extracted,
        error_count=job.error_count,
        error_log=job.error_log,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
    return APIResponse(success=True, data=response_data)


@router.get("/jobs", response_model=APIResponse[List[ScrapingJobResponse]])
def list_scraping_jobs(
    marketplace_id: Optional[str] = Query(None, description="Filter by marketplace ID"),
    status: Optional[str] = Query(None, description="Filter by status ('success', 'running', 'failed')"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> APIResponse[List[ScrapingJobResponse]]:
    """Lists historical and active scraping execution jobs."""
    query = db.query(ScrapingJob)
    if marketplace_id:
        query = query.filter(ScrapingJob.marketplace_id == marketplace_id)
    if status:
        query = query.filter(ScrapingJob.status == status)

    total = query.count()
    jobs = query.order_by(ScrapingJob.created_at.desc()).offset(offset).limit(limit).all()

    data = [
        ScrapingJobResponse(
            id=j.id,
            marketplace_id=j.marketplace_id,
            status=j.status,
            target_category=j.target_category,
            target_url=j.target_url,
            items_discovered=j.items_discovered,
            items_extracted=j.items_extracted,
            error_count=j.error_count,
            error_log=j.error_log,
            created_at=j.created_at,
            started_at=j.started_at,
            finished_at=j.finished_at,
        )
        for j in jobs
    ]
    return APIResponse(success=True, data=data, meta=MetaInfo(total=total, limit=limit, offset=offset))


@router.get("/jobs/{job_id}", response_model=APIResponse[ScrapingJobResponse])
def get_scraping_job(job_id: str, db: Session = Depends(get_db)) -> APIResponse[ScrapingJobResponse]:
    """Retrieves detailed telemetry for a specific scraping job."""
    job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
    if not job:
        raise EntityNotFoundError("ScrapingJob", job_id)

    response_data = ScrapingJobResponse(
        id=job.id,
        marketplace_id=job.marketplace_id,
        status=job.status,
        target_category=job.target_category,
        target_url=job.target_url,
        items_discovered=job.items_discovered,
        items_extracted=job.items_extracted,
        error_count=job.error_count,
        error_log=job.error_log,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
    return APIResponse(success=True, data=response_data)
