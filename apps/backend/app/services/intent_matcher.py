"""Service for matching user messages to intents"""
from sqlalchemy.orm import Session
from app.models.intent import Intent
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class IntentMatcherService:
    """Service for matching user messages to configured intents"""
    
    @staticmethod
    def match_intent(db: Session, user_message: str) -> Optional[Intent]:
        """
        Match user message to an intent based on keywords
        
        Args:
            db: Database session
            user_message: User's message to match
            
        Returns:
            Matched Intent if found, None otherwise
        """
        # Get all enabled intents, ordered by priority (highest first)
        intents = db.query(Intent).filter(
            Intent.enabled == True
        ).order_by(Intent.priority.desc()).all()
        
        user_message_lower = user_message.lower().strip()
        
        for intent in intents:
            # Split keywords by comma and check if any keyword matches
            keywords = [k.strip().lower() for k in intent.keywords.split(',') if k.strip()]
            
            for keyword in keywords:
                # Simple keyword matching (can be enhanced with regex or fuzzy matching)
                if keyword in user_message_lower:
                    logger.debug(
                        f"Intent matched: {intent.name} (keyword: {keyword})",
                        extra={"user_message": user_message[:100]}
                    )
                    return intent
        
        return None
    
    @staticmethod
    def get_greeting(db: Session) -> Optional[str]:
        """
        Get a random enabled greeting message
        
        Args:
            db: Database session
            
        Returns:
            Greeting message if found, None otherwise
        """
        from app.models.greeting import Greeting
        import random
        
        greetings = db.query(Greeting).filter(
            Greeting.enabled == True
        ).order_by(Greeting.priority.desc()).all()
        
        if not greetings:
            return None
        
        # Return highest priority greeting, or random if multiple with same priority
        highest_priority = greetings[0].priority
        top_greetings = [g for g in greetings if g.priority == highest_priority]
        
        selected = random.choice(top_greetings)
        return selected.message





