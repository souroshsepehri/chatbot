from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class KBQA(Base):
    __tablename__ = "kb_qa"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False, index=True)
    answer = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

