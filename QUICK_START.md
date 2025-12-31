# Quick Start Guide

راهنمای سریع برای شروع با PM2 (حتی روی لوکال).

## مشکلات رایج و راه حل

### ❌ مشکل 1: Frontend build نشده

**خطا:**
```
Error: ENOENT: no such file or directory, open '.next/BUILD_ID'
```

**راه حل:**
```bash
cd apps/frontend
npm run build
cd ../..
```

### ❌ مشکل 2: PM2 ecosystem file پیدا نمی‌شود

**خطا:**
```
[PM2][ERROR] File pm2.ecosystem.config.js not found
```

**راه حل:**
از **root directory** پروژه اجرا کنید (نه از `apps/frontend` یا `apps/backend`):
```bash
# از root directory
cd "D:\chatbot zimmer"  # یا مسیر پروژه شما
pm2 start pm2.ecosystem.config.js
```

### ❌ مشکل 3: Backend virtual environment پیدا نمی‌شود

**راه حل:**
```bash
cd apps/backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
deactivate
cd ../..
```

## راه‌اندازی سریع

### روش 1: استفاده از Script (Recommended)

**Windows PowerShell:**
```powershell
# از root directory
.\start-pm2.ps1
```

**Linux/Mac:**
```bash
# از root directory
chmod +x start-pm2.sh
./start-pm2.sh
```

### روش 2: دستی

```bash
# 1. Build frontend
cd apps/frontend
npm install
npm run build
cd ../..

# 2. Setup backend (if needed)
cd apps/backend
python -m venv venv
# Activate venv and install dependencies
cd ../..

# 3. Create logs directory
mkdir -p logs

# 4. Start with PM2 (از root directory)
pm2 start pm2.ecosystem.config.js

# 5. Check status
pm2 status
pm2 logs
```

## دستورات مفید

```bash
# Status
pm2 status

# Logs
pm2 logs
pm2 logs chatbot-backend
pm2 logs chatbot-frontend

# Restart
pm2 restart all
pm2 restart chatbot-backend
pm2 restart chatbot-frontend

# Stop
pm2 stop all

# Delete
pm2 delete all
```

## بررسی مشکلات

### Frontend کار نمی‌کند؟
```bash
# Check if build exists
ls apps/frontend/.next

# Rebuild if needed
cd apps/frontend
npm run build
```

### Backend کار نمی‌کند؟
```bash
# Check logs
pm2 logs chatbot-backend

# Check if venv exists
ls apps/backend/venv

# Test manually
cd apps/backend
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Port در حال استفاده است؟
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :8000
lsof -i :3000
```

## نکات مهم

1. ✅ همیشه از **root directory** پروژه PM2 را اجرا کنید
2. ✅ قبل از start، frontend را **build** کنید
3. ✅ مطمئن شوید که `.env` files تنظیم شده‌اند
4. ✅ Logs در `logs/` directory ذخیره می‌شوند

## Environment Variables

### Backend (`apps/backend/.env`)
```env
ENV=production
DATABASE_URL=sqlite:///./chatbot.db
OPENAI_API_KEY=your-key
SESSION_SECRET=your-secret
FRONTEND_ORIGIN=http://localhost:3000
```

### Frontend (`apps/frontend/.env.local`)
```env
# Optional: Only needed for local development
# Frontend always uses /api (relative path)
# Next.js rewrite rule will proxy /api/* to BACKEND_URL
BACKEND_URL=http://localhost:8000
```

**نکته:** Frontend همیشه از `/api` استفاده می‌کند. در local development، Next.js rewrite rule `/api/*` را به `BACKEND_URL` proxy می‌کند.

