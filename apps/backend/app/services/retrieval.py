from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.kb_qa import KBQA
from app.models.website_page import WebsitePage
from app.models.website_source import WebsiteSource
from app.core.config import settings
import re
import unicodedata
import difflib


class RetrievalService:
    """Strict domain-restricted retrieval with fuzzy similarity matching"""
    
    # Persian character normalization map
    PERSIAN_NORMALIZATION = {
        'ي': 'ی',  # Arabic Yeh -> Persian Yeh
        'ك': 'ک',  # Arabic Kaf -> Persian Kaf
        'ة': 'ه',  # Arabic Teh Marbuta -> Heh
        'أ': 'ا',  # Arabic Alef with Hamza -> Alef
        'إ': 'ا',  # Arabic Alef with Hamza Below -> Alef
        'آ': 'ا',  # Arabic Alef with Madda -> Alef
        'ؤ': 'و',  # Arabic Waw with Hamza -> Waw
        'ئ': 'ی',  # Arabic Yeh with Hamza -> Yeh
    }
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Comprehensive text normalization:
        - Lowercase
        - Trim whitespace
        - Remove punctuation
        - Persian character normalization (ي/ی, ك/ک, etc.)
        - Normalize Unicode characters
        """
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Persian character normalization
        for arabic_char, persian_char in RetrievalService.PERSIAN_NORMALIZATION.items():
            normalized = normalized.replace(arabic_char, persian_char)
        
        # Normalize Unicode (NFD -> NFC)
        normalized = unicodedata.normalize('NFC', normalized)
        
        # Remove punctuation (keep spaces and Persian/Arabic characters)
        # Remove common punctuation but keep Persian/Arabic letters and numbers
        normalized = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', ' ', normalized)
        
        # Normalize whitespace (multiple spaces to single space)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Trim
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def tokenize(text: str) -> set:
        """Tokenize text into word set"""
        normalized = RetrievalService.normalize_text(text)
        if not normalized:
            return set()
        # Split on whitespace and filter empty strings
        tokens = [t for t in normalized.split() if t]
        return set(tokens)
    
    @staticmethod
    def get_trigrams(text: str) -> set:
        """Get character trigrams for fuzzy matching"""
        normalized = RetrievalService.normalize_text(text)
        if len(normalized) < 3:
            return set()
        trigrams = set()
        for i in range(len(normalized) - 2):
            trigrams.add(normalized[i:i+3])
        return trigrams
    
    @staticmethod
    def jaccard_similarity(set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def calculate_score(query: str, text: str) -> float:
        """
        Calculate comprehensive similarity score using multiple methods:
        - Token overlap (Jaccard similarity)
        - Trigram similarity
        - Substring matching
        Returns score between 0.0 and 1.0
        """
        if not query or not text:
            return 0.0
        
        query_norm = RetrievalService.normalize_text(query)
        text_norm = RetrievalService.normalize_text(text)
        
        if not query_norm or not text_norm:
            return 0.0
        
        # 1. Exact match (highest priority)
        if query_norm == text_norm:
            return 1.0
        
        # 2. Substring match
        if query_norm in text_norm:
            # Longer query = higher confidence
            substring_score = min(0.9, 0.5 + (len(query_norm) / max(len(text_norm), 1)) * 0.4)
        elif text_norm in query_norm:
            substring_score = 0.6
        else:
            substring_score = 0.0
        
        # 3. Token-based Jaccard similarity
        query_tokens = RetrievalService.tokenize(query)
        text_tokens = RetrievalService.tokenize(text)
        token_jaccard = RetrievalService.jaccard_similarity(query_tokens, text_tokens)
        
        # 4. Trigram similarity (for fuzzy matching of paraphrases)
        query_trigrams = RetrievalService.get_trigrams(query)
        text_trigrams = RetrievalService.get_trigrams(text)
        trigram_jaccard = RetrievalService.jaccard_similarity(query_trigrams, text_trigrams)
        
        # 5. Token overlap ratio (how many query tokens appear in text)
        if query_tokens:
            overlap_ratio = len(query_tokens & text_tokens) / len(query_tokens)
        else:
            overlap_ratio = 0.0
        
        # 6. Difflib ratio (sequence matching for fuzzy similarity)
        difflib_ratio = difflib.SequenceMatcher(None, query_norm, text_norm).ratio()
        
        # Weighted combination:
        # - Token Jaccard: 35% (most important for semantic similarity)
        # - Trigram Jaccard: 25% (catches paraphrases and word order variations)
        # - Difflib ratio: 20% (sequence matching for fuzzy similarity)
        # - Substring: 10% (catches partial matches)
        # - Overlap ratio: 10% (ensures most query words appear)
        hybrid_score = (
            token_jaccard * 0.35 +
            trigram_jaccard * 0.25 +
            difflib_ratio * 0.20 +
            substring_score * 0.10 +
            overlap_ratio * 0.10
        )
        
        return min(hybrid_score, 1.0)
    
    @staticmethod
    def retrieve_kb(db: Session, query: str, top_k: int = None) -> List[Tuple[KBQA, float]]:
        """Retrieve top K KB items by relevance"""
        if top_k is None:
            top_k = settings.KB_TOP_K
        
        # Get all KB items
        all_kb = db.query(KBQA).all()
        
        # Score each item
        scored = []
        for kb_item in all_kb:
            # Score on question + answer
            question_score = RetrievalService.calculate_score(query, kb_item.question)
            answer_score = RetrievalService.calculate_score(query, kb_item.answer)
            combined_score = max(question_score, answer_score * 0.8)  # Question weighted more
            
            if combined_score >= settings.MIN_CONFIDENCE_SCORE:
                scored.append((kb_item, combined_score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:top_k]
    
    @staticmethod
    def retrieve_website(db: Session, query: str, top_k: int = None) -> List[Tuple[WebsitePage, float]]:
        """Retrieve top K website pages by relevance (only from enabled sources)"""
        if top_k is None:
            top_k = settings.WEBSITE_TOP_K
        
        # Get enabled website sources
        enabled_sources = db.query(WebsiteSource).filter(WebsiteSource.enabled == True).all()
        source_ids = [s.id for s in enabled_sources]
        
        if not source_ids:
            return []
        
        # Get pages from enabled sources
        pages = db.query(WebsitePage).filter(
            WebsitePage.website_source_id.in_(source_ids)
        ).all()
        
        # Score each page
        scored = []
        for page in pages:
            # Score on title + content
            title_score = RetrievalService.calculate_score(query, page.title or "")
            content_score = RetrievalService.calculate_score(query, page.content_text[:1000])  # First 1000 chars
            combined_score = max(title_score, content_score * 0.7)  # Title weighted more
            
            if combined_score >= settings.MIN_CONFIDENCE_SCORE:
                scored.append((page, combined_score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:top_k]
    
    @staticmethod
    def retrieve_all(db: Session, query: str) -> Dict[str, Any]:
        """Retrieve from both KB and website sources"""
        kb_results = RetrievalService.retrieve_kb(db, query)
        website_results = RetrievalService.retrieve_website(db, query)
        
        # Check if we have any results
        has_results = len(kb_results) > 0 or len(website_results) > 0
        
        # Calculate overall confidence (max of top results)
        max_confidence = 0.0
        if kb_results:
            max_confidence = max(max_confidence, kb_results[0][1])
        if website_results:
            max_confidence = max(max_confidence, website_results[0][1])
        
        return {
            "kb_results": kb_results,
            "website_results": website_results,
            "has_results": has_results,
            "max_confidence": max_confidence
        }

