from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.website_source import WebsiteSource
from app.models.website_page import WebsitePage
from app.services.website_fetcher import WebsiteFetcherService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class WebsiteIngestService:
    """Service for ingesting website content into database"""
    
    def __init__(self):
        self.fetcher = WebsiteFetcherService()
    
    def ingest_website(self, db: Session, website_source_id: int, request_id: str = None) -> dict:
        """Ingest all pages from a website source"""
        website_source = db.query(WebsiteSource).filter(
            WebsiteSource.id == website_source_id
        ).first()
        
        if not website_source:
            logger.warning(
                "Website source not found",
                extra={
                    "request_id": request_id,
                    "website_source_id": website_source_id,
                }
            )
            return {"success": False, "message": "Website source not found"}
        
        logger.info(
            "Starting website ingestion",
            extra={
                "request_id": request_id,
                "website_source_id": website_source_id,
                "base_url": website_source.base_url,
            }
        )
        
        # Update status to running
        website_source.crawl_status = "running"
        db.commit()
        
        try:
            # Validate base_url domain
            from urllib.parse import urlparse
            parsed_base = urlparse(website_source.base_url)
            if not parsed_base.scheme or not parsed_base.netloc:
                logger.error(
                    "Invalid base URL",
                    extra={
                        "request_id": request_id,
                        "website_source_id": website_source_id,
                        "base_url": website_source.base_url,
                    }
                )
                website_source.crawl_status = "failed"
                website_source.last_crawled_at = datetime.utcnow()
                db.commit()
                return {"success": False, "message": "Invalid base URL"}
            
            base_domain = parsed_base.netloc
            
            # Get URLs to crawl (already limited by MAX_CRAWL_PAGES)
            urls = self.fetcher.crawl_from_base(website_source.base_url)
            
            if not urls:
                logger.warning(
                    "No URLs found to crawl",
                    extra={
                        "request_id": request_id,
                        "website_source_id": website_source_id,
                        "base_url": website_source.base_url,
                    }
                )
                website_source.crawl_status = "failed"
                website_source.last_crawled_at = datetime.utcnow()
                db.commit()
                return {"success": False, "message": "No URLs found to crawl"}
            
            logger.info(
                "Found URLs to crawl",
                extra={
                    "request_id": request_id,
                    "website_source_id": website_source_id,
                    "urls_count": len(urls),
                    "max_pages": settings.MAX_CRAWL_PAGES,
                }
            )
            
            # Fetch and store each page
            pages_ingested = 0
            pages_updated = 0
            pages_failed = 0
            
            for url in urls:
                # Double-check domain restriction
                parsed_url = urlparse(url)
                if parsed_url.netloc != base_domain:
                    logger.warning(
                        "Skipping URL from different domain",
                        extra={
                            "request_id": request_id,
                            "url": url,
                            "expected_domain": base_domain,
                            "actual_domain": parsed_url.netloc,
                        }
                    )
                    pages_failed += 1
                    continue
                
                result = self.fetcher.fetch_page(url, request_id=request_id)
                if not result:
                    logger.debug(
                        "Failed to fetch page",
                        extra={
                            "request_id": request_id,
                            "url": url,
                        }
                    )
                    pages_failed += 1
                    continue
                
                title, content_text, content_hash = result
                
                # Check if page already exists
                existing_page = db.query(WebsitePage).filter(
                    WebsitePage.website_source_id == website_source_id,
                    WebsitePage.url == url
                ).first()
                
                if existing_page:
                    # Update if content changed
                    if existing_page.content_hash != content_hash:
                        existing_page.title = title
                        existing_page.content_text = content_text
                        existing_page.content_hash = content_hash
                        existing_page.updated_at = datetime.utcnow()
                        pages_updated += 1
                else:
                    # Create new page
                    new_page = WebsitePage(
                        website_source_id=website_source_id,
                        url=url,
                        title=title,
                        content_text=content_text,
                        content_hash=content_hash
                    )
                    db.add(new_page)
                    pages_ingested += 1
                
                # Commit periodically to avoid long transactions
                if (pages_ingested + pages_updated) % 10 == 0:
                    db.commit()
            
            # Final commit
            db.commit()
            
            # Update website source status
            if pages_ingested > 0 or pages_updated > 0:
                website_source.crawl_status = "done"
            else:
                website_source.crawl_status = "failed"
            
            website_source.last_crawled_at = datetime.utcnow()
            db.commit()
            
            logger.info(
                "Website ingestion completed",
                extra={
                    "request_id": request_id,
                    "website_source_id": website_source_id,
                    "pages_ingested": pages_ingested,
                    "pages_updated": pages_updated,
                    "pages_failed": pages_failed,
                    "status": website_source.crawl_status,
                }
            )
            
            return {
                "success": True,
                "message": f"Ingested {pages_ingested} new pages, updated {pages_updated} pages, failed {pages_failed} pages",
                "pages_count": pages_ingested + pages_updated
            }
            
        except Exception as e:
            logger.error(
                "Error ingesting website",
                extra={
                    "request_id": request_id,
                    "website_source_id": website_source_id,
                    "base_url": website_source.base_url,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True
            )
            website_source.crawl_status = "failed"
            website_source.last_crawled_at = datetime.utcnow()
            db.commit()
            return {"success": False, "message": str(e)}

