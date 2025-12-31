from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.routers.dependencies import get_current_admin
from app.models.admin_user import AdminUser
from app.models.intent import Intent
from app.schemas.admin_intent import (
    IntentCreate, IntentUpdate, IntentResponse
)

router = APIRouter()


@router.get("", response_model=List[IntentResponse])
async def list_intents(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """List all intents, ordered by priority"""
    return db.query(Intent).order_by(Intent.priority.desc(), Intent.id.desc()).all()


@router.post("", response_model=IntentResponse, status_code=status.HTTP_201_CREATED)
async def create_intent(
    intent_data: IntentCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Create a new intent"""
    # Check if name already exists
    existing = db.query(Intent).filter(Intent.name == intent_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Intent with this name already exists")
    
    intent = Intent(
        name=intent_data.name,
        keywords=intent_data.keywords,
        response=intent_data.response,
        enabled=intent_data.enabled,
        priority=intent_data.priority
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)
    return intent


@router.put("/{intent_id}", response_model=IntentResponse)
async def update_intent(
    intent_id: int,
    intent_data: IntentUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Update an intent"""
    intent = db.query(Intent).filter(Intent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    # Check name uniqueness if name is being updated
    if intent_data.name and intent_data.name != intent.name:
        existing = db.query(Intent).filter(Intent.name == intent_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Intent with this name already exists")
        intent.name = intent_data.name
    
    if intent_data.keywords is not None:
        intent.keywords = intent_data.keywords
    if intent_data.response is not None:
        intent.response = intent_data.response
    if intent_data.enabled is not None:
        intent.enabled = intent_data.enabled
    if intent_data.priority is not None:
        intent.priority = intent_data.priority
    
    db.commit()
    db.refresh(intent)
    return intent


@router.delete("/{intent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_intent(
    intent_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Delete an intent"""
    intent = db.query(Intent).filter(Intent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    db.delete(intent)
    db.commit()
    return None



