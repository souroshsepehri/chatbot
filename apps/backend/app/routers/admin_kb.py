from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.routers.dependencies import get_current_admin
from app.models.admin_user import AdminUser
from app.models.kb_qa import KBQA
from app.schemas.admin_kb import (
    KBQACreate, KBQAUpdate, KBQAResponse
)

router = APIRouter()


# KB QA
@router.get("/qa", response_model=List[KBQAResponse])
async def list_kb_qa(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """List all KB QA items"""
    return db.query(KBQA).all()


@router.post("/qa", response_model=KBQAResponse, status_code=status.HTTP_201_CREATED)
async def create_kb_qa(
    qa_data: KBQACreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Create a new KB QA item"""
    qa = KBQA(
        question=qa_data.question,
        answer=qa_data.answer
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)
    return qa


@router.put("/qa/{qa_id}", response_model=KBQAResponse)
async def update_kb_qa(
    qa_id: int,
    qa_data: KBQAUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Update a KB QA item"""
    qa = db.query(KBQA).filter(KBQA.id == qa_id).first()
    if not qa:
        raise HTTPException(status_code=404, detail="KB QA item not found")
    
    if qa_data.question is not None:
        qa.question = qa_data.question
    if qa_data.answer is not None:
        qa.answer = qa_data.answer
    
    db.commit()
    db.refresh(qa)
    return qa


@router.delete("/qa/{qa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb_qa(
    qa_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Delete a KB QA item"""
    qa = db.query(KBQA).filter(KBQA.id == qa_id).first()
    if not qa:
        raise HTTPException(status_code=404, detail="KB QA item not found")
    
    db.delete(qa)
    db.commit()
    return None

