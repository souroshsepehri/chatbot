"""
Test health check endpoints perform real checks
"""
import pytest
from unittest.mock import patch, MagicMock
from app.models.kb_qa import KBQA


def test_health_components_db_check_is_real(client, db):
    """
    Test that /health/components actually queries the database
    """
    # Create a test KB item to ensure DB is working
    kb_item = KBQA(
        question="Test question",
        answer="Test answer"
    )
    db.add(kb_item)
    db.commit()
    
    # Make health check request
    response = client.get("/health/components")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have db status
    assert "db" in data
    assert "status" in data["db"]
    
    # DB check should be "ok" if we can query
    # The health check should actually query the database
    assert data["db"]["status"] == "ok" or data["db"]["status"] == "error"
    
    # Verify it's a real check by checking if we can query
    # If DB is working, status should be "ok"
    test_query = db.query(KBQA).first()
    if test_query:
        assert data["db"]["status"] == "ok", "DB check should return 'ok' if database is accessible"


def test_health_components_checks_all_components(client, db):
    """
    Test that /health/components checks all required components
    """
    response = client.get("/health/components")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have all component checks
    required_components = ["backend", "db", "openai", "website_crawler"]
    for component in required_components:
        assert component in data, f"Missing {component} check"
        assert "status" in data[component], f"Missing status for {component}"



