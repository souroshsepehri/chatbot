from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    verify_access_token,
    verify_refresh_token
)
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.core.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _set_cookie(response: Response, key: str, value: str, max_age: int):
    """Helper to set HTTP-only cookie with consistent settings"""
    cookie_kwargs = {
        "key": key,
        "value": value,
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE.lower(),
        "max_age": max_age,
        "path": "/"
    }
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN
    response.set_cookie(**cookie_kwargs)


def _delete_cookie(response: Response, key: str):
    """Helper to delete cookie"""
    cookie_kwargs = {
        "key": key,
        "path": "/"
    }
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(**cookie_kwargs)


@router.post("/login")
async def login(
    login_data: LoginRequest,
    response: Response,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Admin login - issues both access and refresh tokens"""
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == login_data.username).first()
    except Exception as e:
        logger.error(
            "Database error during login",
            extra={
                "error": str(e),
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please check database configuration."
        )
    
    if not admin or not verify_password(login_data.password, admin.password_hash):
        logger.warning(
            "Failed login attempt",
            extra={
                "username": login_data.username,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Store login time for absolute cap
    login_time = datetime.utcnow()
    
    try:
        # Create both tokens
        access_token = create_access_token(admin.username)
        refresh_token = create_refresh_token(admin.username, login_time=login_time)
    except Exception as e:
        logger.error(
            "Error creating tokens",
            extra={
                "username": admin.username,
                "error": str(e),
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating authentication tokens. Please check SESSION_SECRET configuration."
        )
    
    try:
        # Set both as HTTP-only cookies
        _set_cookie(response, "access_token", access_token, max_age=settings.SESSION_IDLE_MINUTES * 60)
        _set_cookie(response, "refresh_token", refresh_token, max_age=settings.SESSION_ABSOLUTE_MINUTES * 60)
    except Exception as e:
        logger.error(
            "Error setting cookies",
            extra={
                "username": admin.username,
                "error": str(e),
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting authentication cookies."
        )
    
    logger.info(
        "Admin logged in",
        extra={
            "username": admin.username,
            "login_time": login_time.isoformat(),
        }
    )
    
    return {"ok": True}


@router.post("/refresh")
async def refresh(
    response: Response,
    http_request: Request,
    refresh_token_cookie: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )
    
    # Verify refresh token
    username, error_msg = verify_refresh_token(refresh_token_cookie)
    
    if not username:
        logger.warning(
            "Refresh token invalid",
            extra={
                "error": error_msg,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Invalid refresh token"
        )
    
    # Verify user still exists
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin:
        logger.warning(
            "User not found during refresh",
            extra={
                "username": username,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Issue new access token (refresh token stays the same)
    new_access_token = create_access_token(username)
    
    # Set new access token cookie
    _set_cookie(response, "access_token", new_access_token, max_age=settings.SESSION_IDLE_MINUTES * 60)
    
    logger.debug(
        "Access token refreshed",
        extra={
            "username": username,
        }
    )
    
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response):
    """Admin logout - clears both cookies"""
    _delete_cookie(response, "access_token")
    _delete_cookie(response, "refresh_token")
    return {"ok": True}


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    access_token: str = Cookie(None, alias="access_token")
):
    """Get current user info - requires valid access token"""
    username = verify_access_token(access_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return UserInfo(username=username)

