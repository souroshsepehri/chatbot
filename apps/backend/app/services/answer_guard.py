from typing import Dict, Any, List
from app.services.retrieval import RetrievalService
from app.core.config import settings


class AnswerGuardService:
    """Strict guard to ensure answers ONLY come from retrieved sources"""
    
    REFUSAL_MESSAGE = "اطلاعات کافی در پایگاه دانش یا صفحات وب‌سایت ندارم. لطفاً سوال خود را به شکل دیگری مطرح کنید یا با پشتیبانی تماس بگیرید."
    
    @staticmethod
    def should_refuse(retrieval_result: Dict[str, Any]) -> bool:
        """
        Determine if we should refuse to answer.
        STRICT RULES:
        - Refuse if total sources < MIN_SOURCES
        - Refuse if max confidence below threshold
        - Refuse if no results found
        """
        kb_results = retrieval_result.get("kb_results", [])
        website_results = retrieval_result.get("website_results", [])
        total_sources = len(kb_results) + len(website_results)
        
        # Refuse if not enough sources
        if total_sources < settings.MIN_SOURCES:
            return True
        
        # Refuse if max confidence below threshold
        if retrieval_result.get("max_confidence", 0.0) < settings.MIN_CONFIDENCE_SCORE:
            return True
        
        # No results at all
        if not retrieval_result.get("has_results", False):
            return True
        
        return False
    
    @staticmethod
    def get_refusal_reason(retrieval_result: Dict[str, Any]) -> str:
        """Get detailed reason for refusal (for logging)"""
        if not retrieval_result["has_results"]:
            return "NO_MATCHING_SOURCE"
        
        if retrieval_result["max_confidence"] < settings.MIN_CONFIDENCE_SCORE:
            return f"LOW_CONFIDENCE_{retrieval_result['max_confidence']:.2f}_BELOW_{settings.MIN_CONFIDENCE_SCORE}"
        
        return "UNKNOWN"
    
    @staticmethod
    def build_context(retrieval_result: Dict[str, Any]) -> str:
        """Build context string from retrieved sources"""
        context_parts = []
        
        # Add KB context
        kb_results = retrieval_result["kb_results"]
        if kb_results:
            context_parts.append("=== Knowledge Base ===")
            for kb_item, score in kb_results:
                context_parts.append(f"Q: {kb_item.question}")
                context_parts.append(f"A: {kb_item.answer}")
                context_parts.append("")
        
        # Add website context
        website_results = retrieval_result["website_results"]
        if website_results:
            context_parts.append("=== Website Content ===")
            for page, score in website_results:
                context_parts.append(f"Title: {page.title or 'Untitled'}")
                context_parts.append(f"URL: {page.url}")
                # Use first 500 chars of content
                content_preview = page.content_text[:500] + ("..." if len(page.content_text) > 500 else "")
                context_parts.append(f"Content: {content_preview}")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def extract_source_ids(retrieval_result: Dict[str, Any]) -> Dict[str, List[int]]:
        """Extract source IDs for logging"""
        kb_ids = [kb_item.id for kb_item, _ in retrieval_result["kb_results"]]
        website_page_ids = [page.id for page, _ in retrieval_result["website_results"]]
        
        return {
            "kb_ids": kb_ids,
            "website_page_ids": website_page_ids
        }

