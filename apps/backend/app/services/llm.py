from typing import List, Dict, Any, Tuple
from openai import OpenAI
from openai import APITimeoutError, APIError
from app.core.config import settings
from app.schemas.chat import SourceInfo
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Service for OpenAI API calls with strict context enforcement"""
    
    SYSTEM_PROMPT = """شما یک ربات چت با محدودیت دامنه هستید. شما باید STRICTLY فقط از اطلاعات موجود در پایگاه دانش و منابع وب‌سایت استفاده کنید.

قوانین STRICT (بدون استثنا):
1. فقط از اطلاعات ارائه شده در متن زیر استفاده کنید
2. اگر پاسخ به سوال در متن زیر نیست، باید بگویید: "در منابع موجود نیست"
3. از دانش عمومی استفاده نکنید - حتی اگر می‌دانید پاسخ چیست
4. فرضیات نسازید - فقط از متن ارائه شده استفاده کنید
5. توضیحات اضافی یا پیش‌فرض‌ها اضافه نکنید
6. اگر متن شامل اطلاعات کافی برای پاسخ نیست، صراحتاً بگویید "در منابع موجود نیست"
7. باید منابع را در پاسخ خود ذکر کنید (مثلاً "طبق پایگاه دانش" یا "بر اساس صفحه وب‌سایت [URL]")

متن:
{context}

منابع استفاده شده:
{sources_list}

یادآوری CRITICAL: 
- اگر نمی‌توانید پاسخ را مستقیماً از متن بالا استخراج کنید، باید بگویید "در منابع موجود نیست"
- همیشه منابع را در پاسخ خود ذکر کنید
- هیچ استثنایی وجود ندارد - فقط از منابع ارائه شده استفاده کنید."""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set")
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )
    
    def generate_answer(
        self,
        user_message: str,
        context: str,
        sources: List[SourceInfo],
        request_id: str = None
    ) -> str:
        """Generate answer using OpenAI with strict context enforcement"""
        try:
            # Build sources list for prompt
            sources_list = []
            for i, source in enumerate(sources, 1):
                if source.type == "kb":
                    sources_list.append(f"{i}. پایگاه دانش: {source.title} (ID: {source.id})")
                elif source.type == "web":
                    sources_list.append(f"{i}. وب‌سایت: {source.title} (URL: {source.url})")
            
            sources_text = "\n".join(sources_list) if sources_list else "هیچ منبعی یافت نشد"
            
            system_prompt = self.SYSTEM_PROMPT.format(
                context=context,
                sources_list=sources_text
            )
            
            logger.info(
                "Calling OpenAI API",
                extra={
                    "model": settings.OPENAI_MODEL,
                    "timeout": settings.OPENAI_TIMEOUT,
                    "message_length": len(user_message),
                    "context_length": len(context),
                    "sources_count": len(sources),
                }
            )
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # Lower temperature for more focused answers
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            logger.info(
                "OpenAI API call successful",
                extra={
                    "model": settings.OPENAI_MODEL,
                    "answer_length": len(answer),
                    "tokens_used": getattr(response.usage, "total_tokens", None),
                }
            )
            
            # Remove unwanted phrases that LLM might add
            unwanted_phrases = [
                "از مدیر بخواهید این سوال را اضافه کند",
                "از مدیر بخواهید",
                "لطفا از مدیر بخواهید",
                "از پنل مدیریت",
                "در پنل مدیریت اضافه کنید"
            ]
            for phrase in unwanted_phrases:
                answer = answer.replace(phrase, "").strip()
                # Also remove if it's part of a sentence
                answer = answer.replace(f"{phrase}.", "").strip()
                answer = answer.replace(f"{phrase}،", "").strip()
            
            # Clean up multiple spaces and newlines
            import re
            answer = re.sub(r'\s+', ' ', answer).strip()
            
            # Post-process: ensure answer doesn't violate rules
            if not self._validate_answer(answer, context):
                return "در منابع موجود نیست"
            
            return answer
            
        except APITimeoutError as e:
            logger.error(
                "OpenAI API timeout",
                extra={
                    "error_type": "APITimeoutError",
                    "timeout_seconds": settings.OPENAI_TIMEOUT,
                    "model": settings.OPENAI_MODEL,
                    "error_message": str(e),
                }
            )
            return "زمان اتصال به پایان رسید. لطفا دوباره تلاش کنید."
        except APIError as e:
            logger.error(
                "OpenAI API error",
                extra={
                    "error_type": "APIError",
                    "error_code": getattr(e, "code", None),
                    "error_message": str(e),
                    "model": settings.OPENAI_MODEL,
                }
            )
            return "خطایی رخ داده است. لطفا دوباره تلاش کنید."
        except Exception as e:
            logger.error(
                "Unexpected error in LLM service",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "model": settings.OPENAI_MODEL,
                },
                exc_info=True
            )
            return "خطایی رخ داده است. لطفا دوباره تلاش کنید."
    
    def _validate_answer(self, answer: str, context: str) -> bool:
        """
        Strict validation: ensure answer uses context.
        Returns False if answer seems to be general knowledge or hallucination.
        """
        if not answer or not context:
            return False
        
        # If answer is the refusal message, it's valid
        refusal_indicators = [
            "در منابع موجود نیست",
            "پاسخی برای این سوال ندارم",
            "موجود نیست",
            "پایگاه دانش",
            "don't have",
            "not available",
            "no information"
        ]
        if any(indicator in answer.lower() for indicator in refusal_indicators):
            return True
        
        # Check if answer contains significant overlap with context
        # Normalize both for comparison
        from app.services.retrieval import RetrievalService
        
        context_normalized = RetrievalService.normalize_text(context)
        answer_normalized = RetrievalService.normalize_text(answer)
        
        # Get tokens
        context_tokens = RetrievalService.tokenize(context)
        answer_tokens = RetrievalService.tokenize(answer)
        
        if not context_tokens:
            return False
        
        # Calculate overlap ratio
        overlap = len(context_tokens & answer_tokens)
        overlap_ratio = overlap / len(answer_tokens) if answer_tokens else 0.0
        
        # Require at least 20% word overlap (stricter than before)
        # This ensures the answer is actually using context words
        if overlap_ratio < 0.20:
            return False
        
        # Additional check: answer should not be too generic
        # Generic answers often have very few context words
        if overlap < 2:  # At least 2 words from context
            return False
        
        return True
    
    def test_connection(self, timeout: int = 5) -> Tuple[bool, str]:
        """Test OpenAI connection with lightweight ping"""
        try:
            # Use a lightweight API call - list models with short timeout
            # This is much faster than a full completion request
            self.client.models.list(timeout=timeout)
            return True, "ok"
        except APITimeoutError as e:
            logger.warning(
                "OpenAI connection test timeout",
                extra={
                    "error_type": "APITimeoutError",
                    "timeout_seconds": timeout,
                    "error_message": str(e),
                }
            )
            return False, f"Connection timeout after {timeout}s"
        except APIError as e:
            logger.warning(
                "OpenAI connection test API error",
                extra={
                    "error_type": "APIError",
                    "error_code": getattr(e, "code", None),
                    "error_message": str(e),
                }
            )
            return False, f"API error: {str(e)}"
        except Exception as e:
            logger.warning(
                "OpenAI connection test failed",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )
            return False, f"Connection error: {str(e)}"

