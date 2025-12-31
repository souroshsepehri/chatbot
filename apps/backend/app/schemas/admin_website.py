from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class WebsiteSourceCreate(BaseModel):
    base_url: str
    enabled: bool = True


class WebsiteSourceUpdate(BaseModel):
    enabled: Optional[bool] = None


class WebsiteSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    base_url: str
    enabled: bool
    created_at: datetime
    last_crawled_at: Optional[datetime]
    crawl_status: str
    pages_count: Optional[int] = None


class WebsitePageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    website_source_id: int
    url: str
    title: Optional[str]
    updated_at: datetime


class CrawlStatusResponse(BaseModel):
    status: str
    last_crawled_at: Optional[datetime]
    pages_count: int
    message: Optional[str] = None

