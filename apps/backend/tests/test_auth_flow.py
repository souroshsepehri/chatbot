"""
Test admin authentication flow with access/refresh tokens
"""
import pytest
import jwt
from datetime import datetime, timedelta
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings


def test_admin_requires_auth(client, seed_admin_user):
    """Test that admin endpoints return 401 without cookies"""
    # Try to access admin endpoint without cookies
    response = client.get("/admin/logs")
    
    assert response.status_code == 401
    
    # Try another admin endpoint
    response = client.get("/admin/kb/categories")
    assert response.status_code == 401


def test_refresh_flow(client, seed_admin_user):
    """Test complete refresh flow: login -> access expires -> refresh -> retry"""
    # 1. Login
    login_response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    assert login_response.status_code == 200
    assert login_response.json() == {"ok": True}
    
    # Check cookies are set
    assert "access_token" in login_response.cookies
    assert "refresh_token" in login_response.cookies
    
    # 2. Call /auth/me - should work
    response = client.get(
        "/auth/me",
        cookies=login_response.cookies
    )
    assert response.status_code == 200
    
    # 3. Simulate access token expiry by creating an expired token
    # Decode the current access token to get username
    current_access_token = login_response.cookies.get("access_token")
    decoded = jwt.decode(current_access_token, settings.SESSION_SECRET, algorithms=["HS256"])
    username = decoded.get("sub")
    
    # Create an expired access token manually
    expired_payload = {
        "sub": username,
        "typ": "access",
        "iat": datetime.utcnow() - timedelta(minutes=10),
        "exp": datetime.utcnow() - timedelta(minutes=1)  # Expired 1 minute ago
    }
    expired_access_token = jwt.encode(expired_payload, settings.SESSION_SECRET, algorithm="HS256")
    
    # Try to access /auth/me with expired token - should fail
    expired_cookies = dict(login_response.cookies)
    expired_cookies["access_token"] = expired_access_token
    response = client.get(
        "/auth/me",
        cookies=expired_cookies
    )
    assert response.status_code == 401
    
    # 4. Call /auth/refresh with refresh token - should work
    # Extract refresh token and verify it has login_iat
    refresh_token_value = login_response.cookies.get("refresh_token")
    assert refresh_token_value is not None, "Refresh token should be set"
    
    # Call /auth/refresh with refresh token - should work
    refresh_cookies = {
        "refresh_token": refresh_token_value
    }
    refresh_response = client.post(
        "/auth/refresh",
        cookies=refresh_cookies
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json() == {"ok": True}
    
    # Check new access token cookie is set
    assert "access_token" in refresh_response.cookies
    
    # 5. Call /auth/me again with refreshed cookies - should work
    updated_cookies = dict(login_response.cookies)
    updated_cookies.update(dict(refresh_response.cookies))
    
    response = client.get(
        "/auth/me",
        cookies=updated_cookies
    )
    assert response.status_code == 200


def test_refresh_expires_after_absolute_cap(client, seed_admin_user):
    """Test that refresh token expires after absolute cap"""
    # Login to get a refresh token structure
    login_response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    assert login_response.status_code == 200
    
    # Get the refresh token and decode it to get username
    refresh_token = login_response.cookies.get("refresh_token")
    decoded = jwt.decode(refresh_token, settings.SESSION_SECRET, algorithms=["HS256"], options={"verify_exp": False})
    username = decoded.get("sub")
    
    # Create a refresh token with login_iat in the past (beyond absolute cap)
    # Since SESSION_ABSOLUTE_MINUTES is 30 by default, we'll create a token
    # where login was 31 minutes ago, which should exceed the absolute cap
    past_login_time = datetime.utcnow() - timedelta(minutes=settings.SESSION_ABSOLUTE_MINUTES + 1)
    expired_refresh_payload = {
        "sub": username,
        "typ": "refresh",
        "iat": datetime.utcnow() - timedelta(minutes=5),  # Token issued 5 minutes ago
        "exp": datetime.utcnow() + timedelta(minutes=10),  # Token itself not expired (exp in future)
        "login_iat": past_login_time.timestamp()  # But login was beyond absolute cap
    }
    expired_refresh_token = jwt.encode(expired_refresh_payload, settings.SESSION_SECRET, algorithm="HS256")
    
    # Try to refresh with expired refresh token (absolute cap exceeded)
    expired_cookies = dict(login_response.cookies)
    expired_cookies["refresh_token"] = expired_refresh_token
    
    refresh_response = client.post(
        "/auth/refresh",
        cookies=expired_cookies
    )
    assert refresh_response.status_code == 401
    assert "Absolute session cap exceeded" in refresh_response.json()["detail"] or \
           "Refresh token expired" in refresh_response.json()["detail"]


def test_refresh_requires_refresh_token(client, seed_admin_user):
    """Test that /auth/refresh cannot be called without refresh_token"""
    # Login to get tokens (this sets cookies in the client)
    login_response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    assert login_response.status_code == 200
    
    # Clear the client's cookie jar to ensure no cookies are sent
    # TestClient uses httpx which maintains a cookie jar
    client.cookies.clear()
    
    # Try to refresh with NO cookies at all - should fail with "No refresh token provided"
    refresh_response = client.post(
        "/auth/refresh"
        # No cookies parameter - should result in no refresh_token cookie
    )
    assert refresh_response.status_code == 401
    detail = refresh_response.json()["detail"]
    assert "No refresh token provided" in detail or "refresh token" in detail.lower()

