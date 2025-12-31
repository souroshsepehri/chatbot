# Backend API

FastAPI backend for the Domain-Restricted Chatbot Platform.

## نصب (Installation)

```bash
pip install -r requirements.txt
```

## Migration

برای اعمال تغییرات دیتابیس:

```bash
alembic upgrade head
```

## Seed Database (داده‌های Demo)

برای پر کردن database با داده‌های demo (20 QA، 1 website source):

```bash
python -m app.db.seed
```

این دستور برای demo و testing مفید است. برای جزئیات بیشتر: `SEED.md`

## اجرای Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## اجرای Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

قبل از اجرا، فایل `.env` را در دایرکتوری `apps/backend` ایجاد کنید:

```env
DATABASE_URL=sqlite:///./chatbot.db
USE_POSTGRES=false
OPENAI_API_KEY=your-openai-api-key
SESSION_SECRET=your-secret-key-change-in-production
FRONTEND_ORIGIN=http://localhost:3000
MIN_CONFIDENCE_SCORE=0.70
GREETING_MESSAGE=سلام! چطور می‌تونم کمکتون کنم؟
```

## ساخت Admin User

برای ایجاد کاربر ادمین اولیه:

```bash
python create_admin.py
```

یا به صورت دستی:

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
```

## Database Migrations

### ایجاد Migration جدید:
```bash
alembic revision --autogenerate -m "description"
```

### اعمال Migrations:
```bash
alembic upgrade head
```

### Rollback:
```bash
alembic downgrade -1
```

## تست‌ها

برای اجرای همه تست‌ها:

```bash
# روش 1: pytest مستقیم
pytest -q

# روش 2: با script
.\scripts\test_all.ps1  # Windows
./scripts/test_all.sh   # Linux/Mac
```

تست‌های اجباری:
- ✅ chat بدون source → refusal و llm_called=false
- ✅ chat با kb hit → جواب + sources و llm_called=true
- ✅ admin بدون login → 401
- ✅ admin بعد از 5 دقیقه → 401
- ✅ website crawl فقط same-domain
- ✅ /health/components db check واقعی
- ✅ strict domain restriction (similarity >= 0.70)
- ✅ Persian character normalization
- ✅ greeting behavior for new sessions

برای جزئیات بیشتر: `README_TESTS.md`

