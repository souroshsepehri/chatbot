# Deploy Guide - مرحله نهایی

راهنمای ساده و مستقیم برای deploy روی سرور. بعد از انجام تمام P0 tasks، deploy فقط 5 مرحله است.

## مراحل Deploy

### 1. Clone
```bash
git clone <your-repo-url> chatbot
cd chatbot
```

### 2. Environment Variables

**Backend:**
```bash
cd apps/backend
cp .env.example .env
# ویرایش .env با مقادیر واقعی
nano .env
```

**Frontend:**
```bash
cd apps/frontend
cp .env.example .env.local
# ویرایش .env.local با مقادیر واقعی
nano .env.local
```

### 3. Database Migration
```bash
cd apps/backend

# ایجاد virtual environment
python3 -m venv venv
source venv/bin/activate  # یا .\venv\Scripts\activate در Windows

# نصب dependencies
pip install -r requirements.txt

# Migration
alembic upgrade head

# (اختیاری) Seed برای demo
python -m app.db.seed
```

### 4. PM2 Start
```bash
# از root directory پروژه
cd ../..

# Build frontend
cd apps/frontend
npm install
npm run build
cd ../..

# Start با PM2 (idempotent - safe to run multiple times)
bash scripts/pm2-ensure.sh

# بررسی status
pm2 status
pm2 logs
```

### 4.1. After Git Pull (Updates)
```bash
# After pulling updates, ensure both services are running
bash scripts/pm2-ensure.sh

# Verify services
curl 127.0.0.1:8000/health
curl 127.0.0.1:3000
```

### 5. Nginx
```bash
# کپی config
sudo cp nginx.conf /etc/nginx/sites-available/chatbot
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Checklist قبل از Deploy

- ✅ همه تست‌ها pass می‌شوند: `pytest -q`
- ✅ Frontend build می‌شود: `npm run build`
- ✅ PM2 ecosystem file درست است
- ✅ Environment variables تنظیم شده‌اند
- ✅ Database migration آماده است

## Troubleshooting

### PM2 کار نمی‌کند؟
```bash
# Use the ensure script to fix missing processes
bash scripts/pm2-ensure.sh

# Check logs
pm2 logs chatbot-backend
pm2 logs chatbot-frontend

# Manual restart if needed
pm2 restart all
```

### Nginx کار نمی‌کند؟
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Database مشکل دارد؟
```bash
cd apps/backend
alembic upgrade head
```

## نکات مهم

1. ✅ همیشه از root directory پروژه PM2 را اجرا کنید
2. ✅ Environment variables را قبل از start تنظیم کنید
3. ✅ Frontend را قبل از PM2 start build کنید
4. ✅ Nginx config را test کنید قبل از reload

## دستورات مفید

```bash
# PM2
pm2 status
pm2 logs
pm2 restart all
pm2 stop all

# Nginx
sudo nginx -t
sudo systemctl status nginx
sudo systemctl reload nginx

# Logs
tail -f logs/app.log
pm2 logs chatbot-backend
```





