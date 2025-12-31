from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.routers import auth, chat, admin_kb, admin_logs, admin_website, admin_greeting, admin_intent, health
import logging

setup_logging()
logger = logging.getLogger(__name__)

# Validate critical settings on startup
try:
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
        logger.warning("OPENAI_API_KEY is not set. Chat functionality will not work.")
    if settings.SESSION_SECRET == "change-this-secret-key-in-production":
        logger.warning("SESSION_SECRET is using default value. Change it in production!")
except Exception as e:
    logger.error(f"Error loading settings: {e}")
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            logger.error("Please run: python setup_db.py or alembic upgrade head")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error checking database: {e}")
    
    yield
    
    # Shutdown (if needed)
    # Currently no shutdown logic required


app = FastAPI(
    title="Domain-Restricted Chatbot API",
    description="Production-ready chatbot with KB and website sources",
    version="1.0.0",
    lifespan=lifespan
)

# Request ID middleware (must be first)
app.add_middleware(RequestIDMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(admin_kb.router, prefix="/admin/kb", tags=["admin-kb"])
app.include_router(admin_logs.router, prefix="/admin/logs", tags=["admin-logs"])
app.include_router(admin_website.router, prefix="/admin/website", tags=["admin-website"])
app.include_router(admin_greeting.router, prefix="/admin/greeting", tags=["admin-greeting"])
app.include_router(admin_intent.router, prefix="/admin/intent", tags=["admin-intent"])
app.include_router(health.router, prefix="/health", tags=["health"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    request_id = getattr(request.state, "request_id", "unknown")
    # Don't include request_id in extra - the filter will add it automatically
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id}
    )


@app.get("/")
async def root():
    return {"message": "Domain-Restricted Chatbot API", "version": "1.0.0"}

