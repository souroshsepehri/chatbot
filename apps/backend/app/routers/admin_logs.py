from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.session import get_db
from app.routers.dependencies import get_current_admin
from app.models.admin_user import AdminUser
from app.models.chat_log import ChatLog
from app.schemas.admin_logs import ChatLogResponse, ChatLogListResponse

router = APIRouter()


@router.get("", response_model=ChatLogListResponse)
async def list_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """List chat logs with pagination and search"""
    query = db.query(ChatLog)
    
    if search:
        query = query.filter(
            or_(
                ChatLog.user_message.contains(search),
                ChatLog.bot_message.contains(search)
            )
        )
    
    total = query.count()
    
    logs = query.order_by(ChatLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return ChatLogListResponse(
        logs=logs,
        total=total,
        limit=limit,
        offset=offset
    )

