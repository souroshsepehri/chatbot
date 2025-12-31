from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from app.db.session import get_db
from app.schemas.health import HealthResponse, ComponentStatus
from app.services.llm import LLMService
from app.models.website_source import WebsiteSource
import logging

router = APIRouter()
llm_service = LLMService()
logger = logging.getLogger(__name__)


@router.get("")
async def health():
    """Basic health check"""
    return {"status": "ok"}


@router.get("/components", response_model=HealthResponse)
async def health_components(db: Session = Depends(get_db)):
    """Detailed component health check with real checks"""
    
    # Backend - always ok if we reach here
    backend_status = ComponentStatus(status="ok", message="Backend is running")
    
    # Database - real query check
    db_status = ComponentStatus(status="ok")
    try:
        # Execute a real query to check database connectivity
        result = db.execute(text("SELECT 1 as test")).scalar()
        if result != 1:
            db_status = ComponentStatus(status="error", message="Database query returned unexpected result")
        else:
            db_status = ComponentStatus(status="ok", message="Database connection healthy")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = ComponentStatus(status="error", message=f"Database error: {str(e)}")
    
    # OpenAI - lightweight ping with short timeout
    openai_status = ComponentStatus(status="ok")
    try:
        # Use a lightweight ping with short timeout (3 seconds)
        ok, msg = llm_service.test_connection(timeout=3)
        if not ok:
            openai_status = ComponentStatus(status="error", message=msg)
        else:
            openai_status = ComponentStatus(status="ok", message="OpenAI API accessible")
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        openai_status = ComponentStatus(status="error", message=f"OpenAI error: {str(e)}")
    
    # Website crawler - check last crawl status from database
    crawler_status = ComponentStatus(status="ok")
    try:
        # Get the most recent crawl status (prioritize sources with last_crawled_at)
        recent_source = db.query(WebsiteSource).filter(
            WebsiteSource.last_crawled_at.isnot(None)
        ).order_by(
            WebsiteSource.last_crawled_at.desc()
        ).first()
        
        # If no source with last_crawled_at, get any source to check status
        if not recent_source:
            recent_source = db.query(WebsiteSource).first()
        
        if recent_source:
            # Check if there's a recent crawl (within last 24 hours) or if status is running
            if recent_source.crawl_status == "running":
                crawler_status = ComponentStatus(
                    status="ok",
                    message=f"Crawler is running (last: {recent_source.base_url})"
                )
            elif recent_source.crawl_status == "failed":
                # Check if failure is recent (within 1 hour)
                if recent_source.last_crawled_at:
                    # Handle timezone-aware datetime
                    last_crawled = recent_source.last_crawled_at
                    if last_crawled.tzinfo is not None:
                        # Convert to UTC naive for comparison
                        last_crawled_naive = last_crawled.replace(tzinfo=None)
                    else:
                        last_crawled_naive = last_crawled
                    
                    time_since_failure = datetime.utcnow() - last_crawled_naive
                    if time_since_failure < timedelta(hours=1):
                        crawler_status = ComponentStatus(
                            status="error",
                            message=f"Recent crawl failure: {recent_source.base_url}"
                        )
                    else:
                        hours_ago = int(time_since_failure.total_seconds() / 3600)
                        crawler_status = ComponentStatus(
                            status="ok",
                            message=f"Crawler available (last failure {hours_ago}h ago)"
                        )
                else:
                    crawler_status = ComponentStatus(
                        status="ok",
                        message="Crawler service available"
                    )
            elif recent_source.crawl_status == "done":
                crawler_status = ComponentStatus(
                    status="ok",
                    message=f"Crawler healthy (last success: {recent_source.base_url})"
                )
            else:  # idle
                crawler_status = ComponentStatus(
                    status="ok",
                    message="Crawler service available (idle)"
                )
        else:
            # No website sources configured
            crawler_status = ComponentStatus(
                status="ok",
                message="Crawler service available (no sources configured)"
            )
    except Exception as e:
        logger.error(f"Crawler health check failed: {e}")
        crawler_status = ComponentStatus(status="error", message=f"Crawler check error: {str(e)}")
    
    return HealthResponse(
        backend=backend_status,
        db=db_status,
        openai=openai_status,
        website_crawler=crawler_status
    )

