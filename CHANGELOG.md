# Changelog

## Recent Updates

### Strict Domain Restriction Implementation
- ✅ Implemented strict domain-restricted answering logic
- ✅ Enhanced text normalization with Persian character support (ي→ی, ك→ک, etc.)
- ✅ Advanced similarity matching using Jaccard similarity and trigrams
- ✅ Strict confidence threshold (default: 0.70)
- ✅ Hard answer guard - OpenAI is NEVER called when no matches found
- ✅ Comprehensive test coverage

### UI/UX Improvements
- ✅ Removed "Categories" feature from admin panel
- ✅ Updated refusal message to "پاسخی برای این سوال ندارم"
- ✅ Removed "از مدیر بخواهید این سوال را اضافه کند" message
- ✅ New sessions show only greeting without refusal message

### Code Quality
- ✅ Fixed all deprecation warnings:
  - Pydantic Config → ConfigDict
  - SQLAlchemy declarative_base import updated
  - FastAPI on_event → lifespan context manager
- ✅ Updated pytest to 9.0.2 (compatible with pytest-asyncio)
- ✅ Improved test database session handling for Windows

### Bug Fixes
- ✅ Fixed website source background task DB session issue
- ✅ Added missing `settings` import in website_ingest.py
- ✅ Fixed greeting behavior for new sessions
- ✅ Added phrase filtering in LLM responses

### Features Removed
- ❌ Categories feature (KB items no longer have categories)
- ❌ Category-related API endpoints removed
- ❌ Category management UI removed

### Features Added
- ✅ Intent matching system for greetings and common responses
- ✅ Greeting management in admin panel
- ✅ Advanced similarity matching for better paraphrase detection
- ✅ Comprehensive logging with request IDs

## Configuration Changes

### Environment Variables
- `MIN_CONFIDENCE_SCORE`: Default changed from `0.3` to `0.70`
- `GREETING_MESSAGE`: New configurable greeting message

### Dependencies
- `pytest`: Updated to `>=8.2.0,<10.0.0`
- `pytest-asyncio`: Added `>=0.21.0`

## Migration Notes

### Database
- Categories table removed (if you had categories, they need to be migrated)
- KB items no longer have `category_id` field
- Run `alembic upgrade head` to apply migrations

### Behavior Changes
- Questions with similarity < 0.70 will be refused (previously 0.3)
- New sessions show only greeting, not refusal message
- Refusal message changed to "پاسخی برای این سوال ندارم"

