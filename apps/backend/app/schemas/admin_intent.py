from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class IntentCreate(BaseModel):
    name: str
    keywords: str  # Comma-separated keywords
    response: str
    enabled: bool = True
    priority: int = 0


class IntentUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[str] = None
    response: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class IntentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    keywords: str
    response: str
    enabled: bool
    priority: int
    created_at: datetime
    updated_at: datetime



