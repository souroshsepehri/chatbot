from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.routers.dependencies import get_current_admin
from app.models.admin_user import AdminUser
from app.models.greeting import Greeting
from app.schemas.admin_greeting import (
    GreetingCreate, GreetingUpdate, GreetingResponse
)

router = APIRouter()


@router.get("", response_model=List[GreetingResponse])
async def list_greetings(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """List all greetings, ordered by priority"""
    return db.query(Greeting).order_by(Greeting.priority.desc(), Greeting.id.desc()).all()


@router.post("", response_model=GreetingResponse, status_code=status.HTTP_201_CREATED)
async def create_greeting(
    greeting_data: GreetingCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Create a new greeting"""
    greeting = Greeting(
        message=greeting_data.message,
        enabled=greeting_data.enabled,
        priority=greeting_data.priority
    )
    db.add(greeting)
    db.commit()
    db.refresh(greeting)
    return greeting


@router.put("/{greeting_id}", response_model=GreetingResponse)
async def update_greeting(
    greeting_id: int,
    greeting_data: GreetingUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Update a greeting"""
    greeting = db.query(Greeting).filter(Greeting.id == greeting_id).first()
    if not greeting:
        raise HTTPException(status_code=404, detail="Greeting not found")
    
    if greeting_data.message is not None:
        greeting.message = greeting_data.message
    if greeting_data.enabled is not None:
        greeting.enabled = greeting_data.enabled
    if greeting_data.priority is not None:
        greeting.priority = greeting_data.priority
    
    db.commit()
    db.refresh(greeting)
    return greeting


@router.delete("/{greeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_greeting(
    greeting_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Delete a greeting"""
    greeting = db.query(Greeting).filter(Greeting.id == greeting_id).first()
    if not greeting:
        raise HTTPException(status_code=404, detail="Greeting not found")
    
    db.delete(greeting)
    db.commit()
    return None



