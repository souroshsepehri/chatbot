from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class WebsitePage(Base):
    __tablename__ = "website_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    website_source_id = Column(Integer, ForeignKey("website_sources.id"), nullable=False, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    content_text = Column(Text, nullable=False)
    content_hash = Column(String, nullable=True, index=True)  # For deduplication
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    website_source = relationship("WebsiteSource", back_populates="pages")
    
    __table_args__ = (
        Index('idx_website_source_url', 'website_source_id', 'url'),
    )

