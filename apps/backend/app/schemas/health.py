from pydantic import BaseModel
from typing import Optional


class ComponentStatus(BaseModel):
    status: str  # "ok" or "error"
    message: Optional[str] = None


class HealthResponse(BaseModel):
    backend: ComponentStatus
    db: ComponentStatus
    openai: ComponentStatus
    website_crawler: ComponentStatus

