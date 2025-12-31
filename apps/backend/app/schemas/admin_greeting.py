from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class GreetingCreate(BaseModel):
    message: str
    enabled: bool = True
    priority: int = 0


class GreetingUpdate(BaseModel):
    message: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class GreetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    message: str
    enabled: bool
    priority: int
    created_at: datetime
    updated_at: datetime



