from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatLogResponse(BaseModel):
    id: int
    session_id: str
    user_message: str
    bot_message: str
    sources_json: Optional[Dict[str, Any]] = None
    refused: bool
    intent: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('refused', mode='before')
    @classmethod
    def convert_refused(cls, v):
        """Convert refused string to boolean"""
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class ChatLogListResponse(BaseModel):
    logs: List[ChatLogResponse]
    total: int
    limit: int
    offset: int

