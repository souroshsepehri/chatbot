"""
Test chat endpoint with KB sources - should call OpenAI and return answer
"""
import pytest
from unittest.mock import patch, MagicMock
from app.models.kb_qa import KBQA


def test_chat_with_kb_hit_returns_answer_and_calls_llm(client, db):
    """
    Test that /chat returns answer with sources and llm_called=true when KB has matching items
    """
    # Create a KB QA item
    kb_item = KBQA(
        question="ساعات کاری شما چیست؟",
        answer="ساعات کاری ما از 9 صبح تا 6 عصر است."
    )
    db.add(kb_item)
    db.commit()
    
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ساعات کاری ما از 9 صبح تا 6 عصر است."
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    # Patch the llm_service.client on the already-instantiated service
    with patch('app.routers.chat.llm_service.client', mock_client):
        response = client.post(
            "/chat",
            json={
                "message": "ساعات کاری شما چیست؟"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should NOT be refused
    assert data["refused"] is False
    
    # OpenAI SHOULD be called
    assert data["openai_called"] is True
    
    # Should have answer
    assert "answer" in data
    assert len(data["answer"]) > 0
    
    # Should have sources
    assert "sources" in data
    assert len(data["sources"]) > 0
    assert data["sources"][0]["type"] == "kb"
    assert data["sources"][0]["id"] == kb_item.id
    
    # Verify OpenAI was actually called
    mock_client.chat.completions.create.assert_called_once()

