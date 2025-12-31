from pydantic import BaseModel, model_validator
from typing import List, Optional, Dict, Any
from app.core.config import settings


class SourceInfo(BaseModel):
    type: str  # "kb" or "website"
    id: int
    title: Optional[str] = None
    url: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SourceInfo]
    refused: bool
    openai_called: bool
    missing_info: Optional[Dict[str, Any]] = None
    # Debug fields - only included in development
    debug: Optional[Dict[str, Any]] = None
    
    @model_validator(mode='after')
    def remove_debug_in_production(self):
        """Remove debug fields in production"""
        if settings.ENV == "production":
            self.debug = None
        return self

