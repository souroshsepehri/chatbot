"""
Lightweight greeting detection service.
Detects if a message is a greeting-only message (not a question with greeting).
"""
import re
from typing import List


class GreetingDetectorService:
    """Service for detecting greeting-only messages"""
    
    # Persian greetings
    PERSIAN_GREETINGS = [
        "سلام",
        "سلام علیکم",
        "درود",
        "وقت بخیر",
        "صبح بخیر",
        "عصر بخیر",
        "شب بخیر",
        "خداحافظ",
        "خداحفظ",
        "بدرود",
    ]
    
    # English greetings
    ENGLISH_GREETINGS = [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
    ]
    
    # Question markers (if present, it's not greeting-only)
    QUESTION_MARKERS = [
        "؟",  # Persian question mark
        "?",   # English question mark
        "چیست",
        "چیه",
        "چی",
        "چطور",
        "چگونه",
        "کجا",
        "کی",
        "چه",
        "کدام",
        "آیا",
        "what",
        "how",
        "where",
        "when",
        "who",
        "why",
        "which",
        "is",
        "are",
        "do",
        "does",
        "can",
        "could",
        "will",
        "would",
    ]
    
    # Informational keywords that indicate a real question
    INFO_KEYWORDS = [
        "قیمت",
        "هزینه",
        "خدمات",
        "محصولات",
        "سوال",
        "سوالی",
        "مشکل",
        "کمک",
        "راهنمایی",
        "اطلاعات",
        "price",
        "cost",
        "service",
        "product",
        "question",
        "help",
        "information",
        "info",
    ]
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Remove emojis and special characters (keep Persian/Arabic and English letters)
        text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        text = text.strip()
        
        # Lowercase (works for English, Persian stays as is mostly)
        text = text.lower()
        
        return text
    
    @staticmethod
    def is_greeting(message: str) -> bool:
        """
        Detect if message is a greeting-only message.
        
        Rules:
        1. Must contain a greeting word
        2. Must be short (reasonable length)
        3. Must NOT contain question markers
        4. Must NOT contain informational keywords that indicate a real question
        
        Examples:
        - "سلام" => True (greeting-only)
        - "سلام، قیمت خدمات زیمر چنده؟" => False (contains question + info keyword)
        - "سلام علیکم" => True (greeting-only)
        - "هوش مصنوعی چیست؟" => False (contains question marker)
        """
        if not message:
            return False
        
        normalized = GreetingDetectorService.normalize_text(message)
        
        # Check length - greetings are typically short
        # Allow up to 50 characters for greeting + small talk
        if len(normalized) > 50:
            return False
        
        # Check for question markers - if present, it's not greeting-only
        for marker in GreetingDetectorService.QUESTION_MARKERS:
            if marker in normalized:
                return False
        
        # Check for informational keywords - if present with greeting, it's a question
        has_info_keyword = False
        for keyword in GreetingDetectorService.INFO_KEYWORDS:
            if keyword in normalized:
                has_info_keyword = True
                break
        
        # If has info keyword, it's not greeting-only
        if has_info_keyword:
            return False
        
        # Check if message contains a greeting word
        all_greetings = GreetingDetectorService.PERSIAN_GREETINGS + GreetingDetectorService.ENGLISH_GREETINGS
        
        for greeting in all_greetings:
            # Check if greeting appears in the message
            # Use word boundary matching for better accuracy
            greeting_normalized = GreetingDetectorService.normalize_text(greeting)
            
            # Check if greeting is at the start or as a separate word
            if normalized.startswith(greeting_normalized):
                return True
            
            # Check if greeting appears as a word (with space before/after or at start/end)
            pattern = r'(^|\s)' + re.escape(greeting_normalized) + r'(\s|$)'
            if re.search(pattern, normalized):
                return True
        
        return False

