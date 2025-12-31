from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class WebsiteSource(Base):
    __tablename__ = "website_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    base_url = Column(String, nullable=False, unique=True, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    crawl_status = Column(String, default="idle")  # idle, running, failed, done
    
    pages = relationship("WebsitePage", back_populates="website_source", cascade="all, delete-orphan")

