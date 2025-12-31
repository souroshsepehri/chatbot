from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Environment
    ENV: str = "development"  # production | development
    
    # Database
    DATABASE_URL: str = "sqlite:///./chatbot.db"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # Security
    SESSION_SECRET: str = "change-this-secret-key-in-production"
    SESSION_IDLE_MINUTES: int = 5  # Access token lifetime (rolling idle timeout)
    SESSION_ABSOLUTE_MINUTES: int = 30  # Refresh token lifetime (absolute cap)
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    
    # Cookie settings
    COOKIE_SECURE: bool = False  # Set to True in production with HTTPS
    COOKIE_SAMESITE: str = "Lax"  # Lax, Strict, or None
    COOKIE_DOMAIN: Optional[str] = None  # Optional domain for cookies
    
    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    
    # Website Crawling
    MAX_CRAWL_PAGES: int = 100
    CRAWL_TIMEOUT_SECONDS: int = 10
    CRAWL_RATE_LIMIT_DELAY: float = 1.0
    
    # Retrieval
    KB_TOP_K: int = 5
    WEBSITE_TOP_K: int = 3
    MIN_CONFIDENCE_SCORE: float = 0.70  # Strict threshold: only answer if similarity >= 0.70
    
    # Rate Limiting
    CHAT_RATE_LIMIT: int = 10
    CHAT_RATE_WINDOW: int = 60
    
    # OpenAI Model (optional, with default)
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TIMEOUT: int = 30
    
    # Greeting message (shown on first message in new session)
    GREETING_MESSAGE: str = "سلام! چطور می‌تونم کمکتون کنم؟"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """CORS origins list - includes FRONTEND_ORIGIN and common dev ports"""
        origins = [self.FRONTEND_ORIGIN]
        # Also allow common dev ports for local development
        if self.FRONTEND_ORIGIN == "http://localhost:3000":
            origins.append("http://localhost:3001")
        elif self.FRONTEND_ORIGIN == "http://localhost:3001":
            origins.append("http://localhost:3000")
        return origins
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

