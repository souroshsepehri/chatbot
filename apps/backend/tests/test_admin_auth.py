"""
Test admin authentication and session expiry
"""
import pytest
import jwt
from datetime import datetime, timedelta
from app.core.config import settings


def test_admin_endpoint_without_login_returns_401(client, seed_admin_user):
    """
    Test that admin endpoints return 401 without authentication
    """
    # Try to access admin endpoint without login
    response = client.get("/admin/kb/categories")
    
    assert response.status_code == 401
    
    # Try another admin endpoint
    response = client.get("/admin/logs")
    assert response.status_code == 401
    
    # Try POST endpoint
    response = client.post("/admin/kb/categories", json={"title": "Test"})
    assert response.status_code == 401


def test_admin_endpoint_after_session_expiry_returns_401(client, seed_admin_user):
    """
    Test that admin endpoints return 401 after session expiry
    """
    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    assert login_response.status_code == 200
    
    # Get session token (from cookies)
    cookies = login_response.cookies
    
    # Access admin endpoint immediately - should work
    response = client.get(
        "/admin/kb/categories",
        cookies=cookies
    )
    assert response.status_code == 200
    
    # Create an expired access token manually
    # Decode the current access token to get username
    current_access_token = login_response.cookies.get("access_token")
    decoded = jwt.decode(current_access_token, settings.SESSION_SECRET, algorithms=["HS256"])
    username = decoded.get("sub")
    
    # Create a token with expiry in the past
    expired_payload = {
        "sub": username,
        "typ": "access",
        "iat": datetime.utcnow() - timedelta(minutes=10),
        "exp": datetime.utcnow() - timedelta(minutes=1)  # Expired 1 minute ago
    }
    expired_token = jwt.encode(expired_payload, settings.SESSION_SECRET, algorithm="HS256")
    
    # Try to access admin endpoint with expired token
    expired_cookies = dict(cookies)
    expired_cookies["access_token"] = expired_token
    response = client.get(
        "/admin/kb/categories",
        cookies=expired_cookies
    )
    # Should return 401 after expiry
    assert response.status_code == 401

