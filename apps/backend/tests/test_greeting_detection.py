"""
Tests for greeting detection and source-gated answering.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.models.kb_qa import KBQA
from app.models.chat_log import ChatLog
from app.services.greeting_detector import GreetingDetectorService


def test_greeting_only_returns_greeting_response(client, db):
    """Test that 'سلام' returns greeting-only response with refused=false, sources=[]"""
    # Mock OpenAI to ensure it's NOT called for greeting
    with patch('app.services.llm.OpenAI') as mock_openai:
        response = client.post(
            "/chat",
            json={
                "message": "سلام"
            }
        )
        
        # OpenAI should NOT be called for greeting
        assert not mock_openai.called
    
    assert response.status_code == 200
    data = response.json()
    
    # Should NOT be refused (greeting is valid)
    assert data["refused"] is False
    assert data["openai_called"] is False
    assert len(data["sources"]) == 0
    assert "سلام" in data["answer"] or "چطور" in data["answer"]
    
    # Check chat log
    log = db.query(ChatLog).first()
    assert log is not None
    assert log.refused == "false"
    assert log.sources_json["kb_ids"] == []
    assert log.sources_json["website_page_ids"] == []


def test_greeting_with_question_not_treated_as_greeting_only(client, db):
    """Test that 'سلام، زیمر چه خدماتی دارد؟' is NOT greeting-only; with empty KB => refused=true"""
    # No KB items, no website sources
    
    # Mock OpenAI to ensure it's NOT called (no sources)
    with patch('app.services.llm.OpenAI') as mock_openai:
        response = client.post(
            "/chat",
            json={
                "message": "سلام، زیمر چه خدماتی دارد؟"
            }
        )
        
        # OpenAI should NOT be called (no sources found)
        assert not mock_openai.called
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be refused (no sources, not greeting-only)
    assert data["refused"] is True
    assert data["openai_called"] is False
    assert len(data["sources"]) == 0
    assert "اطلاعات کافی" in data["answer"] or "پایگاه دانش" in data["answer"]


def test_non_greeting_with_empty_kb_refuses(client, db):
    """Test that 'هوش مصنوعی چیست؟' with empty KB+no website => refused=true"""
    # No KB items, no website sources
    
    # Mock OpenAI to ensure it's NOT called
    with patch('app.services.llm.OpenAI') as mock_openai:
        response = client.post(
            "/chat",
            json={
                "message": "هوش مصنوعی چیست؟"
            }
        )
        
        # OpenAI should NOT be called (no sources)
        assert not mock_openai.called
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be refused
    assert data["refused"] is True
    assert data["openai_called"] is False
    assert len(data["sources"]) == 0


def test_greeting_does_not_bypass_gating(client, db):
    """Test that greeting detection does not bypass source gating for non-greeting messages"""
    # Create KB item with exact question to ensure high similarity
    kb_item = KBQA(
        question="ساعات کاری شما چیست؟",
        answer="ساعات کاری ما از شنبه تا پنجشنبه از ساعت 9 صبح تا 6 عصر است."
    )
    db.add(kb_item)
    db.commit()
    
    # Test 1: Pure greeting should return greeting (not use KB)
    with patch('app.services.llm.OpenAI') as mock_openai:
        response = client.post(
            "/chat",
            json={
                "message": "سلام"
            }
        )
        # Should NOT call OpenAI for greeting
        assert not mock_openai.called
    
    data = response.json()
    assert data["refused"] is False
    assert data["openai_called"] is False
    assert len(data["sources"]) == 0
    
    # Test 2: Question (without greeting) should use KB
    with patch('app.routers.chat.llm_service.client') as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ساعات کاری ما از شنبه تا پنجشنبه است."
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        
        response = client.post(
            "/chat",
            json={
                "message": "ساعات کاری شما چیست؟"  # Exact match to KB question
            }
        )
        
        # Should call OpenAI (has KB match above threshold)
        assert mock_client.chat.completions.create.called
    
    data = response.json()
    assert data["refused"] is False
    assert data["openai_called"] is True
    assert len(data["sources"]) > 0
    assert data["sources"][0]["type"] == "kb"
    
    # Test 3: Question with greeting prefix should NOT be treated as greeting-only
    # (This tests that greeting detector correctly identifies it as non-greeting)
    from app.services.greeting_detector import GreetingDetectorService
    assert GreetingDetectorService.is_greeting("سلام، ساعات کاری شما چیست؟") is False


def test_greeting_detector_function():
    """Test the greeting detector function directly"""
    # Should detect greetings
    assert GreetingDetectorService.is_greeting("سلام") is True
    assert GreetingDetectorService.is_greeting("سلام علیکم") is True
    assert GreetingDetectorService.is_greeting("درود") is True
    assert GreetingDetectorService.is_greeting("hi") is True
    assert GreetingDetectorService.is_greeting("hello") is True
    
    # Should NOT detect questions with greetings
    assert GreetingDetectorService.is_greeting("سلام، قیمت خدمات زیمر چنده؟") is False
    assert GreetingDetectorService.is_greeting("سلام، زیمر چه خدماتی دارد؟") is False
    
    # Should NOT detect questions
    assert GreetingDetectorService.is_greeting("هوش مصنوعی چیست؟") is False
    assert GreetingDetectorService.is_greeting("ساعات کاری شما چیست؟") is False
    
    # Should handle variants
    assert GreetingDetectorService.is_greeting("سلام!") is True
    assert GreetingDetectorService.is_greeting("سلام 😊") is True
    assert GreetingDetectorService.is_greeting("  سلام  ") is True


def test_response_contract_refused_false_sources_empty_only_for_greeting(client, db):
    """Test that refused=false AND sources=[] only happens for greeting-only messages"""
    # Test 1: Greeting should have refused=false, sources=[]
    with patch('app.services.llm.OpenAI') as mock_openai:
        response = client.post(
            "/chat",
            json={
                "message": "سلام"
            }
        )
        assert not mock_openai.called
    
    data = response.json()
    assert data["refused"] is False
    assert len(data["sources"]) == 0
    
    # Test 2: Non-greeting with no sources should have refused=true, sources=[]
    with patch('app.services.llm.OpenAI') as mock_openai:
        response = client.post(
            "/chat",
            json={
                "message": "سوال تستی"
            }
        )
        assert not mock_openai.called
    
    data = response.json()
    assert data["refused"] is True
    assert len(data["sources"]) == 0
    
    # Test 3: Non-greeting with sources should have refused=false, sources non-empty
    kb_item = KBQA(
        question="ساعات کاری شما چیست؟",
        answer="ساعات کاری ما از شنبه تا پنجشنبه از ساعت 9 صبح تا 6 عصر است."
    )
    db.add(kb_item)
    db.commit()
    
    with patch('app.services.llm.OpenAI') as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ساعات کاری ما از شنبه تا پنجشنبه است."
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        
        response = client.post(
            "/chat",
            json={
                "message": "ساعات کاری شما چیه؟"
            }
        )
    
    data = response.json()
    assert data["refused"] is False
    assert len(data["sources"]) > 0  # Must have sources when not refused (except greeting)

