# Production Local Scripts

اسکریپت‌های اجرای production mode روی local machine (مشابه سرور).

## فایل‌ها

- `run_prod_local.ps1` - برای Windows PowerShell
- `run_prod_local.sh` - برای Linux/Mac

## نحوه استفاده

### Windows

```powershell
# از root directory پروژه
.\scripts\run_prod_local.ps1

# با options
.\scripts\run_prod_local.ps1 -SkipBuild    # Skip frontend build
.\scripts\run_prod_local.ps1 -SkipMigrate  # Skip database migration
```

### Linux/Mac

```bash
# از root directory پروژه
chmod +x scripts/run_prod_local.sh
./scripts/run_prod_local.sh

# با options
./scripts/run_prod_local.sh --skip-build    # Skip frontend build
./scripts/run_prod_local.sh --skip-migrate  # Skip database migration
```

## مراحل اجرا

Script به ترتیب این کارها را انجام می‌دهد:

1. **Load Environment Variables**
   - ابتدا `.env.production` را جستجو می‌کند
   - اگر پیدا نشد، از `.env` استفاده می‌کند
   - Backend: `apps/backend/.env.production` یا `.env`
   - Frontend: `apps/frontend/.env.production.local` یا `.env.local`

2. **Database Migration**
   - اجرای `alembic upgrade head`
   - استفاده از virtual environment اگر موجود باشد

3. **Build Frontend**
   - نصب dependencies اگر `node_modules` وجود نداشته باشد
   - اجرای `npm run build`

4. **Start with PM2**
   - Stop کردن processes موجود
   - Start کردن با `pm2.ecosystem.config.js`

## فایل‌های Environment

### Backend (`apps/backend/.env.production`)

```env
ENV=production
DATABASE_URL=sqlite:///./chatbot.db
OPENAI_API_KEY=your-key
SESSION_SECRET=your-secret
FRONTEND_ORIGIN=http://localhost:3000
MAX_CRAWL_PAGES=100
CRAWL_TIMEOUT_SECONDS=10
```

### Frontend (`apps/frontend/.env.production.local`)

```env
# Optional: Only needed for local development without nginx
# Frontend always uses /api (relative path)
# Next.js rewrite rule will proxy /api/* to BACKEND_URL
BACKEND_URL=http://localhost:8000
```

**نکته مهم:** Frontend همیشه از `/api` استفاده می‌کند (relative path). در production با nginx، nginx خودش `/api/*` را به backend proxy می‌کند. در local development، Next.js rewrite rule این کار را انجام می‌دهد.

## نکات مهم

- ✅ Script از root directory پروژه اجرا می‌شود
- ✅ Environment variables از فایل‌های `.env.production` load می‌شوند
- ✅ اگر `.env.production` نباشد، از `.env` استفاده می‌کند
- ✅ PM2 باید نصب باشد: `npm install -g pm2`
- ✅ Virtual environment برای backend باید موجود باشد

## Troubleshooting

### PM2 not found
```bash
npm install -g pm2
```

### Frontend build fails
```bash
cd apps/frontend
npm install
npm run build
```

### Migration fails
```bash
cd apps/backend
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
alembic upgrade head
```

### Environment variables not loaded
- مطمئن شوید فایل `.env.production` یا `.env` در `apps/backend` وجود دارد
- مطمئن شوید فایل `.env.production.local` یا `.env.local` در `apps/frontend` وجود دارد

