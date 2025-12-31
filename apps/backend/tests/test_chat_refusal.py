"""
Test that chat endpoint refuses answers when KB is empty and website sources are disabled,
and that OpenAI is NOT called in such cases.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.models.website_source import WebsiteSource


def test_chat_refusal_when_kb_empty_and_website_disabled(client, db):
    """
    Test that /chat returns refusal and openai_called=false when:
    - KB is empty
    - Website sources are disabled
    """
    # Ensure KB is empty (no setup needed, it's already empty)
    
    # Create a disabled website source
    disabled_source = WebsiteSource(
        base_url="https://example.com",
        enabled=False
    )
    db.add(disabled_source)
    db.commit()
    
    # Mock OpenAI to ensure it's NOT called
    with patch('app.services.llm.OpenAI') as mock_openai:
        # Make chat request
        response = client.post(
            "/chat",
            json={
                "message": "سوال تستی"
            }
        )
        
        # OpenAI should NOT be instantiated or called
        assert not mock_openai.called, "OpenAI should NOT be called when retrieval has no results"
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be refused
    assert data["refused"] is True
    assert "موجود نیست" in data["answer"] or "پایگاه دانش" in data["answer"]
    
    # OpenAI should NOT be called
    assert data["openai_called"] is False
    
    # Should have missing_info with reason
    assert "missing_info" in data
    assert data["missing_info"]["kb_results_count"] == 0
    assert data["missing_info"]["website_results_count"] == 0
    assert "reason" in data["missing_info"]
    assert "threshold" in data["missing_info"]


def test_chat_refusal_when_kb_empty_and_no_website_sources(client, db):
    """
    Test that /chat returns refusal when KB is empty and no website sources exist
    """
    # No KB items, no website sources
    
    # Mock OpenAI to ensure it's NOT called
    with patch('app.services.llm.OpenAI') as mock_openai:
        response = client.post(
            "/chat",
            json={
                "message": "سوال تستی"
            }
        )
        
        # OpenAI should NOT be instantiated or called
        assert not mock_openai.called, "OpenAI should NOT be called when KB is empty and no website sources"
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["refused"] is True
    assert data["openai_called"] is False
    assert data["missing_info"]["kb_results_count"] == 0
    assert data["missing_info"]["website_results_count"] == 0
    assert "reason" in data["missing_info"]
    assert "threshold" in data["missing_info"]

