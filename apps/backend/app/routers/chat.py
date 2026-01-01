from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.chat_log import ChatLog
from app.schemas.chat import ChatRequest, ChatResponse, SourceInfo
from app.services.retrieval import RetrievalService
from app.services.answer_guard import AnswerGuardService
from app.services.llm import LLMService
from app.services.intent_matcher import IntentMatcherService
from app.core.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

# Generic Persian error message for clients
GENERIC_ERROR_MESSAGE = "متأسفانه خطایی رخ داد. لطفا دوباره تلاش کنید."

router = APIRouter()
llm_service = LLMService()


@router.get("/greeting")
async def get_greeting():
    """Get a greeting message for new chat sessions"""
    return {"message": settings.GREETING_MESSAGE}


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Chat endpoint with strict answer guard and intent matching"""
    # Get request_id from middleware
    request_id = getattr(http_request.state, "request_id", "unknown")
    
    try:
        # Generate or use session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # TEST: Uncomment the line below to test exception handling
        # raise ValueError("Test exception for error handling")
        
        # Check if this is the first message in the session (for greeting)
        is_new_session = not request.session_id or db.query(ChatLog).filter(
            ChatLog.session_id == session_id
        ).first() is None
        
        # Check for intent match (for logging only - not used for answering)
        matched_intent = IntentMatcherService.match_intent(db, request.message)
        intent_name = matched_intent.name if matched_intent else None
        
        # STRICT: Bot only answers from KB or website sources, never from intents
        # Retrieve relevant sources
        retrieval_result = RetrievalService.retrieve_all(db, request.message)
        
        # Collect retrieval hits for metering
        retrieval_hits = {
            "kb": len(retrieval_result["kb_results"]),
            "website": len(retrieval_result["website_results"])
        }
        
        # STRICT ANSWER GUARD: Check if we should refuse
        if AnswerGuardService.should_refuse(retrieval_result):
            refusal_message = AnswerGuardService.REFUSAL_MESSAGE
            openai_called = False
            refusal_reason = AnswerGuardService.get_refusal_reason(retrieval_result)
            
            # Log the refusal with detailed reason
            logger.info(
                "Chat refused - strict domain restriction",
                extra={
                    "session_id": session_id,
                    "query_preview": request.message[:100],
                    "kb_results": retrieval_hits['kb'],
                    "website_results": retrieval_hits['website'],
                    "openai_called": openai_called,
                    "max_confidence": retrieval_result["max_confidence"],
                    "refusal_reason": refusal_reason,
                    "threshold": settings.MIN_CONFIDENCE_SCORE,
                }
            )
            
            # If this is a new session, just show greeting without refusal message
            if is_new_session:
                refusal_with_greeting = settings.GREETING_MESSAGE
                refused = False  # Don't mark as refused for new sessions
            else:
                refusal_with_greeting = refusal_message
                refused = True
            
            # Build sources JSON for refusal (empty sources)
            sources_json = {
                "kb_ids": [],
                "website_page_ids": [],
                "sources": []
            }
            
            chat_log = ChatLog(
                session_id=session_id,
                user_message=request.message,
                bot_message=refusal_with_greeting,
                sources_json=sources_json,
                refused="true" if refused else "false",
                intent=intent_name
            )
            db.add(chat_log)
            db.commit()
            
            # Build debug info (only in development)
            debug_info = None
            if settings.ENV == "development":
                debug_info = {
                    "llm_called": openai_called,
                    "retrieval_hits": retrieval_hits
                }
            
            return ChatResponse(
                session_id=session_id,
                answer=refusal_with_greeting,
                sources=[],
                refused=refused,
                openai_called=openai_called,
                missing_info={
                    "query": request.message,
                    "kb_results_count": retrieval_hits["kb"],
                    "website_results_count": retrieval_hits["website"],
                    "max_confidence": retrieval_result["max_confidence"],
                    "reason": refusal_reason,
                    "threshold": settings.MIN_CONFIDENCE_SCORE
                } if refused else None,
                debug=debug_info
            )
        
        # Build context from retrieved sources
        context = AnswerGuardService.build_context(retrieval_result)
        
        # Build source info list with scores and snippets
        sources = []
        for kb_item, score in retrieval_result["kb_results"]:
            sources.append(SourceInfo(
                type="kb",
                id=kb_item.id,
                title=kb_item.question,
                snippet=kb_item.answer[:200] if kb_item.answer else None,  # First 200 chars as snippet
                score=round(score, 3)
            ))
        
        for page, score in retrieval_result["website_results"]:
            # Extract snippet from content (first 200 chars)
            snippet = page.content_text[:200] if page.content_text else None
            sources.append(SourceInfo(
                type="web",
                id=page.id,
                title=page.title,
                url=page.url,
                snippet=snippet,
                score=round(score, 3)
            ))
        
        # Generate answer using LLM
        openai_called = True
        logger.info(
            "Calling OpenAI for answer generation",
            extra={
                "session_id": session_id,
                "query_preview": request.message[:100],
                "kb_results": retrieval_hits['kb'],
                "website_results": retrieval_hits['website'],
                "openai_called": openai_called,
            }
        )
        
        answer = llm_service.generate_answer(request.message, context, sources, request_id=request_id)
        
        # Include greeting if this is a new session
        if is_new_session:
            answer = f"{settings.GREETING_MESSAGE}\n\n{answer}"
        
        # Build sources JSON for logging (include all source info)
        sources_json = {
            "kb_ids": [s.id for s in sources if s.type == "kb"],
            "website_page_ids": [s.id for s in sources if s.type == "web"],
            "sources": [
                {
                    "type": s.type,
                    "id": s.id,
                    "title": s.title,
                    "url": s.url,
                    "score": s.score
                }
                for s in sources
            ]
        }
        
        # Log the chat with metering info
        logger.info(
            "Chat completed successfully",
            extra={
                "session_id": session_id,
                "llm_called": openai_called,
                "retrieval_hits": retrieval_hits,
                "answer_length": len(answer),
                "sources_count": len(sources),
                "refused": False,
            }
        )
        
        chat_log = ChatLog(
            session_id=session_id,
            user_message=request.message,
            bot_message=answer,
            sources_json=sources_json,
            refused="false",
            intent=intent_name
        )
        db.add(chat_log)
        db.commit()
        
        # Build debug info (only in development)
        debug_info = None
        if settings.ENV == "development":
            debug_info = {
                "llm_called": openai_called,
                "retrieval_hits": retrieval_hits
            }
        
        return ChatResponse(
            session_id=session_id,
            answer=answer,
            sources=sources,
            refused=False,
            openai_called=openai_called,
            debug=debug_info
        )
    
    except Exception as e:
        # Log full exception with traceback
        logger.exception(
            "Error in chat endpoint",
            extra={
                "session_id": session_id if 'session_id' in locals() else "unknown",
                "user_message_preview": request.message[:100] if hasattr(request, 'message') else "unknown",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
            }
        )
        
        # Build error response based on environment
        if settings.ENV in ["development", "testing"]:
            # Development/testing: include exception details
            error_detail = {
                "message": GENERIC_ERROR_MESSAGE,
                "request_id": request_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
        else:
            # Production: only generic message + request_id
            error_detail = {
                "message": GENERIC_ERROR_MESSAGE,
                "request_id": request_id,
            }
        
        # Return JSONResponse with appropriate status code
        # Use 500 for server errors, but could be 400 for client errors
        status_code = 500
        if isinstance(e, (ValueError, TypeError)):
            status_code = 400
        
        return JSONResponse(
            status_code=status_code,
            content=error_detail,
            headers={"X-Request-ID": request_id}
        )

