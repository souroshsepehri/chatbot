from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import SessionLocal
from app.db.session import get_db
from app.routers.dependencies import get_current_admin
from app.models.admin_user import AdminUser
from app.models.website_source import WebsiteSource
from app.models.website_page import WebsitePage
from app.schemas.admin_website import (
    WebsiteSourceCreate, WebsiteSourceUpdate, WebsiteSourceResponse,
    CrawlStatusResponse
)
from app.services.website_ingest import WebsiteIngestService
import logging

router = APIRouter()
ingest_service = WebsiteIngestService()
logger = logging.getLogger(__name__)


def ingest_website_background(source_id: int, request_id: str = None):
    """Background task wrapper that creates its own DB session"""
    db = SessionLocal()
    try:
        ingest_service.ingest_website(db, source_id, request_id=request_id)
    except Exception as e:
        logger.error(
            "Error in background website ingestion",
            extra={
                "request_id": request_id,
                "website_source_id": source_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True
        )
    finally:
        db.close()


@router.get("", response_model=List[WebsiteSourceResponse])
async def list_website_sources(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """List all website sources"""
    sources = db.query(WebsiteSource).all()
    result = []
    for source in sources:
        pages_count = db.query(WebsitePage).filter(
            WebsitePage.website_source_id == source.id
        ).count()
        source_dict = {
            **source.__dict__,
            "pages_count": pages_count
        }
        result.append(WebsiteSourceResponse(**source_dict))
    return result


@router.post("", response_model=WebsiteSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_website_source(
    source_data: WebsiteSourceCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Create a new website source"""
    source = WebsiteSource(
        base_url=source_data.base_url,
        enabled=source_data.enabled
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    
    return WebsiteSourceResponse(
        id=source.id,
        base_url=source.base_url,
        enabled=source.enabled,
        created_at=source.created_at,
        last_crawled_at=source.last_crawled_at,
        crawl_status=source.crawl_status,
        pages_count=0
    )


@router.put("/{source_id}", response_model=WebsiteSourceResponse)
async def update_website_source(
    source_id: int,
    source_data: WebsiteSourceUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Update a website source"""
    source = db.query(WebsiteSource).filter(WebsiteSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Website source not found")
    
    if source_data.enabled is not None:
        source.enabled = source_data.enabled
    
    db.commit()
    db.refresh(source)
    
    pages_count = db.query(WebsitePage).filter(
        WebsitePage.website_source_id == source.id
    ).count()
    
    return WebsiteSourceResponse(
        id=source.id,
        base_url=source.base_url,
        enabled=source.enabled,
        created_at=source.created_at,
        last_crawled_at=source.last_crawled_at,
        crawl_status=source.crawl_status,
        pages_count=pages_count
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_website_source(
    source_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Delete a website source"""
    source = db.query(WebsiteSource).filter(WebsiteSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Website source not found")
    
    db.delete(source)
    db.commit()
    return None


@router.post("/{source_id}/recrawl", response_model=CrawlStatusResponse)
async def recrawl_website(
    source_id: int,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Trigger website re-crawl"""
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    source = db.query(WebsiteSource).filter(WebsiteSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Website source not found")
    
    logger.info(
        "Triggering website recrawl",
        extra={
            "request_id": request_id,
            "website_source_id": source_id,
            "base_url": source.base_url,
        }
    )
    
    # Run ingestion in background with request_id
    # Note: We pass source_id and request_id, but create a new DB session in the background task
    # to avoid session closure issues
    background_tasks.add_task(ingest_website_background, source_id, request_id)
    
    return CrawlStatusResponse(
        status="running",
        last_crawled_at=source.last_crawled_at,
        pages_count=db.query(WebsitePage).filter(
            WebsitePage.website_source_id == source_id
        ).count(),
        message="Crawl started in background"
    )


@router.get("/{source_id}/status", response_model=CrawlStatusResponse)
async def get_crawl_status(
    source_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Get crawl status for a website source"""
    source = db.query(WebsiteSource).filter(WebsiteSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Website source not found")
    
    pages_count = db.query(WebsitePage).filter(
        WebsitePage.website_source_id == source_id
    ).count()
    
    return CrawlStatusResponse(
        status=source.crawl_status,
        last_crawled_at=source.last_crawled_at,
        pages_count=pages_count
    )

