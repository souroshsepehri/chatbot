from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    user_message = Column(Text, nullable=False)
    bot_message = Column(Text, nullable=False)
    sources_json = Column(JSON, nullable=True)  # {"kb_ids": [1,2], "website_page_ids": [3,4]}
    refused = Column(String, default="false")  # Boolean stored as string for SQLite compatibility
    intent = Column(String, nullable=True)  # Intent name if matched, null otherwise
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

