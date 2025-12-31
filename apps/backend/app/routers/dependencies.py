from fastapi import Depends, HTTPException, status, Cookie, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import verify_access_token
from app.models.admin_user import AdminUser
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_current_admin(
    request: Request,
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    Dependency to get current admin user - requires valid access token
    
    - If access token is valid: return admin
    - If access token is expired: return 401 (frontend will call /auth/refresh)
    - DO NOT auto-refresh here - keep refresh explicit via /auth/refresh endpoint
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    if not access_token:
        logger.debug("No access token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify access token
    username = verify_access_token(access_token)
    
    if not username:
        logger.debug("Access token invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # Verify user exists
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    except Exception as e:
        logger.error(
            "Database error in get_current_admin",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error. Please check database configuration."
        )
    
    if not admin:
        logger.warning(
            "User not found in database",
            extra={"username": username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return admin

