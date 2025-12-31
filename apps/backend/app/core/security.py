from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from app.core.config import settings

# PyJWT is imported as 'jwt' - ensure it's installed: pip install PyJWT


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_access_token(username: str) -> str:
    """
    Create JWT access token with short lifetime (5 minutes idle timeout)
    
    Args:
        username: Username for the token
    """
    now = datetime.utcnow()
    expiry = now + timedelta(minutes=settings.SESSION_IDLE_MINUTES)
    
    payload = {
        "sub": username,
        "typ": "access",
        "iat": now,
        "exp": expiry
    }
    return jwt.encode(payload, settings.SESSION_SECRET, algorithm="HS256")


def create_refresh_token(username: str, login_time: Optional[datetime] = None) -> str:
    """
    Create JWT refresh token with absolute cap (30 minutes from login)
    
    Args:
        username: Username for the token
        login_time: Original login time (for absolute cap). If None, uses current time.
    """
    now = datetime.utcnow()
    login_time = login_time or now
    
    # Absolute cap: 30 minutes from login time
    expiry = login_time + timedelta(minutes=settings.SESSION_ABSOLUTE_MINUTES)
    
    # Calculate UTC timestamp correctly (naive UTC datetime -> UTC timestamp)
    # For naive UTC datetime, we need to calculate manually: (dt - epoch) in UTC
    epoch = datetime(1970, 1, 1)
    login_iat_timestamp = (login_time - epoch).total_seconds()
    
    payload = {
        "sub": username,
        "typ": "refresh",
        "iat": now,
        "exp": expiry,
        "login_iat": login_iat_timestamp  # Store login timestamp for absolute cap enforcement
    }
    return jwt.encode(payload, settings.SESSION_SECRET, algorithm="HS256")


def verify_access_token(token: str) -> Optional[str]:
    """
    Verify access token and return username
    
    Args:
        token: JWT access token to verify
    
    Returns:
        Username if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=["HS256"])
        
        # Verify it's an access token
        if payload.get("typ") != "access":
            return None
        
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> tuple[Optional[str], Optional[str]]:
    """
    Verify refresh token and return username and error message
    
    Args:
        token: JWT refresh token to verify
    
    Returns:
        (username, error_message) - username if valid, None and error message if invalid
    """
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=["HS256"])
        
        # Verify it's a refresh token
        if payload.get("typ") != "refresh":
            return None, "Invalid token type"
        
        username = payload.get("sub")
        if not username:
            return None, "No username in token"
        
        # Check absolute cap using login_iat
        login_iat = payload.get("login_iat")
        if login_iat:
            login_time = datetime.utcnow().replace(tzinfo=None)  # Will be compared with timestamp
            # Convert login_iat (timestamp) to datetime
            login_datetime = datetime.utcfromtimestamp(login_iat)
            absolute_expiry = login_datetime + timedelta(minutes=settings.SESSION_ABSOLUTE_MINUTES)
            
            if datetime.utcnow() > absolute_expiry:
                return None, "Absolute session cap exceeded"
        
        return username, None
    except jwt.ExpiredSignatureError:
        return None, "Refresh token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid refresh token"

