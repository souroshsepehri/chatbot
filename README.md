# Domain-Restricted Chatbot Platform

Production-ready chatbot platform with strict domain restrictions. The bot only answers questions using information from the internal knowledge base and configured website sources. No general ChatGPT answers allowed.

## Architecture

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + Alembic
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **LLM**: OpenAI Chat Completions API (strictly context-bound)
- **Orchestration**: LangChain (lightweight, for retrieval + tool calling)
- **Process Manager**: PM2 (runs both frontend and backend)
- **Database**: PostgreSQL (production) or SQLite (local dev)

## Features

### Core Functionality
- ✅ **Strict Answer Guard**: Bot refuses to answer if information is not in KB or website sources (threshold: 0.70)
- ✅ **Knowledge Base Management**: CRUD operations for Q&A pairs
- ✅ **Website Data Source**: Crawl and index website content as a second knowledge source
- ✅ **Chat Logging**: All conversations logged with sources used
- ✅ **Admin Panel**: Full admin interface for managing KB, website sources, greetings, intents, and logs
- ✅ **Advanced Similarity Matching**: Persian character normalization, Jaccard similarity, trigram matching
- ✅ **Intent Matching**: Keyword-based intent matching for greetings and common responses

### Security
- ✅ **Admin Authentication**: JWT-based sessions with 5-minute idle timeout
- ✅ **Password Hashing**: bcrypt for secure password storage
- ✅ **CORS Protection**: Configured for frontend origin
- ✅ **Input Validation**: Pydantic schemas for all inputs

### Retrieval System
- ✅ **Advanced Similarity Matching**: 
  - Persian character normalization (ي→ی, ك→ک, etc.)
  - Token-based Jaccard similarity (40% weight)
  - Trigram Jaccard similarity (30% weight) for paraphrases
  - Substring matching (20% weight)
  - Token overlap ratio (10% weight)
- ✅ **Source Attribution**: Every answer cites which KB items or website pages were used
- ✅ **Strict Confidence Threshold**: Default 0.70 - only answers if similarity >= threshold
- ✅ **Refusal Message**: Shows "پاسخی برای این سوال ندارم" when no answer available

## Project Structure

```
.
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── core/          # Config, security, logging
│   │   │   ├── db/            # Database session and base
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   ├── routers/       # API endpoints
│   │   │   └── services/      # Business logic
│   │   ├── alembic/           # Database migrations
│   │   └── requirements.txt
│   └── frontend/
│       ├── app/                # Next.js App Router
│       ├── components/         # React components
│       └── lib/                # Utilities and API client
├── pm2.ecosystem.config.js     # PM2 configuration
└── README.md
```

## Quick Deploy (5 Steps)

برای deploy روی سرور، فقط این 5 مرحله را انجام دهید:

1. **Clone**: `git clone <repo> chatbot && cd chatbot`
2. **Env**: تنظیم `.env` و `.env.local`
3. **Migrate**: `alembic upgrade head`
4. **PM2**: `pm2 start pm2.ecosystem.config.js`
5. **Nginx**: کپی config و reload

برای جزئیات کامل: `DEPLOY.md`

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, SQLite works for dev)
- PM2: `npm install -g pm2`

### Backend Setup

1. Navigate to backend directory:
```bash
cd apps/backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables (create `.env` file):
```bash
DATABASE_URL=sqlite:///./chatbot.db  # or postgresql://user:pass@localhost/dbname
USE_POSTGRES=false
OPENAI_API_KEY=your-openai-api-key
SESSION_SECRET=your-secret-key-change-in-production
FRONTEND_ORIGIN=http://localhost:3000
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. (Optional) Seed database with demo data:
```bash
python -m app.db.seed
```

This creates 4 categories, 20 QA items, and 1 fake website source for quick demo.

7. Create initial admin user (run Python script):
```python
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.core.security import hash_password

db = SessionLocal()
admin = AdminUser(
    username="admin",
    password_hash=hash_password("admin123")
)
db.add(admin)
db.commit()
print("Admin user created: admin / admin123")
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd apps/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set environment variables (create `.env.local` file):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Build for production:
```bash
npm run build
```

## Running the Application

### Development Mode

**Backend:**
```bash
cd apps/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

**Frontend:**
```bash
cd apps/frontend
npm run dev
```

**Or use the combined dev command:**
```bash
npm run dev:all
```

This starts:
- Backend on `http://127.0.0.1:8001` (dev port)
- Frontend on `http://localhost:3001` (dev port)

### Local Production-like Mode (Clean Build)

For testing production builds locally:

1. **Clean build artifacts:**
```bash
npm run clean
```

2. **Reinstall dependencies (optional):**
```bash
npm run clean:install
```

3. **Build frontend:**
```bash
npm run build:all
```

4. **Start both services:**
```bash
npm run start:all
```

This starts:
- Backend on `http://127.0.0.1:8000` (production port)
- Frontend on `http://localhost:3000` (production port)

**Testing URLs:**

- **Chatbot UI Demo**: `http://localhost:3000/chat` - Dedicated chatbot test page
- **Admin Panel**: `http://localhost:3000/admin/login` - Admin login page
- **Backend Health**: `http://localhost:8000/health` - Backend health check

**Note:** The frontend automatically proxies `/api/*` requests to the backend via Next.js rewrites, so you don't need to configure CORS or hardcode backend URLs in the frontend code.

### Production Mode with PM2

1. Start both services:
```bash
pm2 start pm2.ecosystem.config.js
```

2. Check status:
```bash
pm2 status
```

3. View logs:
```bash
pm2 logs chatbot-backend
pm2 logs chatbot-frontend
```

4. Stop services:
```bash
pm2 stop all
```

5. Restart services:
```bash
pm2 restart all
```

## Database Migrations

### Create a new migration:
```bash
cd apps/backend
alembic revision --autogenerate -m "description"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback:
```bash
alembic downgrade -1
```

## API Endpoints

### Public
- `POST /chat` - Chat endpoint (strict answer guard)
- `GET /health` - Basic health check
- `GET /health/components` - Detailed component status

### Admin (requires authentication)
- `POST /auth/login` - Admin login
- `POST /auth/logout` - Admin logout
- `GET /auth/me` - Get current user

- `GET /admin/kb/qa` - List KB QA items
- `POST /admin/kb/qa` - Create KB QA item
- `PUT /admin/kb/qa/{id}` - Update KB QA item
- `DELETE /admin/kb/qa/{id}` - Delete KB QA item

- `GET /admin/logs` - List chat logs (with pagination and search)
- `GET /admin/greeting` - List greeting messages
- `POST /admin/greeting` - Create greeting message
- `PUT /admin/greeting/{id}` - Update greeting message
- `DELETE /admin/greeting/{id}` - Delete greeting message
- `GET /admin/intent` - List intents
- `POST /admin/intent` - Create intent
- `PUT /admin/intent/{id}` - Update intent
- `DELETE /admin/intent/{id}` - Delete intent
- `GET /admin/website` - List website sources
- `POST /admin/website` - Create website source
- `PUT /admin/website/{id}` - Update website source
- `DELETE /admin/website/{id}` - Delete website source
- `POST /admin/website/{id}/recrawl` - Trigger re-crawl
- `GET /admin/website/{id}/status` - Get crawl status

## Acceptance Tests

The following tests must pass:

1. ✅ **No sources = refusal**: If KB and website have no relevant info, `/chat` refuses WITHOUT calling OpenAI
2. ✅ **Sources exist = answer**: If relevant sources exist, `/chat` calls OpenAI once and answer cites sources
3. ✅ **Admin auth required**: All `/admin/*` endpoints return 401 without auth
4. ✅ **Session expiry**: Admin session expires after 5 minutes; requests after timeout return 401
5. ✅ **Health checks**: Health page shows component statuses; DB check actually queries DB
6. ✅ **Website crawling**: Website ingestion only crawls same-domain pages and respects max page limit
7. ✅ **Widget UI**: Chat widget stays fixed size; messages scroll internally

## Configuration

### Environment Variables

**Backend:**
- `DATABASE_URL` - Database connection string
- `USE_POSTGRES` - Set to "true" for PostgreSQL
- `OPENAI_API_KEY` - OpenAI API key (required)
- `OPENAI_MODEL` - Model to use (default: gpt-4o-mini)
- `SESSION_SECRET` - Secret for JWT signing
- `SESSION_EXPIRY_MINUTES` - Session timeout (default: 5)
- `FRONTEND_ORIGIN` - Frontend URL for CORS
- `MAX_CRAWL_PAGES` - Max pages to crawl (default: 100)
- `MIN_CONFIDENCE_SCORE` - Minimum retrieval confidence (default: 0.70)
- `GREETING_MESSAGE` - Default greeting message for new sessions

**Frontend:**
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.11+)
- Verify virtual environment is activated
- Check database connection string
- Ensure all dependencies are installed

### Frontend won't build
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and `.next`, then `npm install` again
- Check for TypeScript errors: `npm run lint`

### PM2 issues
- Check PM2 is installed: `pm2 --version`
- View detailed logs: `pm2 logs --lines 100`
- Restart services: `pm2 restart all`

### Database issues
- For SQLite: ensure write permissions on database file location
- For PostgreSQL: verify connection string and database exists
- Run migrations: `alembic upgrade head`

## Recent Changes

See [CHANGELOG.md](CHANGELOG.md) for detailed change history.

### Key Updates
- ✅ Strict domain restriction with 0.70 confidence threshold
- ✅ Advanced similarity matching with Persian normalization
- ✅ Removed categories feature
- ✅ Updated refusal message: "پاسخی برای این سوال ندارم"
- ✅ Intent matching system for greetings
- ✅ All deprecation warnings fixed

## License

MIT

