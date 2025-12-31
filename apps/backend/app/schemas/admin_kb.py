from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class KBQACreate(BaseModel):
    question: str
    answer: str


class KBQAUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None


class KBQAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    question: str
    answer: str
    created_at: datetime
    updated_at: datetime

