# Deployment Guide - راهنمای کامل

راهنمای کامل deploy کردن Domain-Restricted Chatbot Platform با PM2.

**برای راهنمای سریع و ساده: `DEPLOY.md`**

این فایل شامل جزئیات کامل است. اگر فقط می‌خواهید سریع deploy کنید، به `DEPLOY.md` مراجعه کنید.

## پیش از Deploy

قبل از deploy، حتماً health checks را اجرا کنید:

```bash
# Linux/Mac
chmod +x scripts/doctor.sh
./scripts/doctor.sh

# Windows
.\scripts\doctor.ps1
```

این script موارد زیر را بررسی می‌کند:
- ✅ Environment variables
- ✅ Frontend build
- ✅ Backend dependencies
- ✅ PM2 configuration
- ✅ Backend health endpoints

## Smoke Tests (بعد از Deploy)

بعد از deploy، این تست‌ها را اجرا کنید:

```bash
# 1. Health check
curl http://localhost:8000/health
curl http://localhost:8000/health/components

# 2. Admin login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}' \
  -c cookies.txt

# 3. Refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -b cookies.txt \
  -c cookies.txt

# 4. Admin endpoint (requires access token)
curl http://localhost:8000/api/admin/logs \
  -b cookies.txt
```

**نکته:** در production، `localhost:8000` را با domain واقعی جایگزین کنید.

## پیش‌نیازها

### سرور
- Ubuntu 20.04+ یا Debian 11+ (یا هر Linux distribution)
- Python 3.11+
- Node.js 18+
- PM2: `npm install -g pm2`
- PostgreSQL (اختیاری، SQLite هم کار می‌کند)
- Nginx (برای reverse proxy)

### نصب PM2
```bash
npm install -g pm2
```

## اجرای Production روی Local (تست قبل از Deploy)

برای تست production mode روی local machine:

**Windows:**
```powershell
.\scripts\run_prod_local.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/run_prod_local.sh
./scripts/run_prod_local.sh
```

این script:
1. Environment variables را از `.env.production` load می‌کند
2. Database migration را اجرا می‌کند
3. Frontend را build می‌کند
4. Backend و Frontend را با PM2 start می‌کند

برای جزئیات بیشتر: `scripts/README.md`

## مراحل Deploy

### 1. آماده‌سازی سرور

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Node.js
sudo apt install python3.11 python3.11-venv python3-pip -y
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2 globally
sudo npm install -g pm2

# Install PostgreSQL (optional)
sudo apt install postgresql postgresql-contrib -y
```

### 2. Clone و Setup پروژه

```bash
# Clone repository
git clone <your-repo-url> chatbot
cd chatbot

# Create logs directory
mkdir -p logs
```

### 3. Backend Setup

```bash
cd apps/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Edit with your values
```

**مهم: فایل `.env` را با مقادیر واقعی پر کنید:**

```env
ENV=production
DATABASE_URL=postgresql://user:password@localhost/chatbot_db
OPENAI_API_KEY=sk-your-actual-key
SESSION_SECRET=your-very-strong-random-secret-here
FRONTEND_ORIGIN=https://yourdomain.com
MAX_CRAWL_PAGES=100
CRAWL_TIMEOUT_SECONDS=10
```

### 4. Database Setup

#### اگر از PostgreSQL استفاده می‌کنید:

```bash
sudo -u postgres psql
CREATE DATABASE chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
\q
```

#### Run migrations:

```bash
cd apps/backend
source venv/bin/activate
alembic upgrade head
```

#### Create admin user:

```bash
python create_admin.py
```

### 5. Frontend Setup

```bash
cd apps/frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.example .env.local
nano .env.local  # Edit with your values
```

**مهم: فایل `.env.local` را با مقادیر واقعی پر کنید:**

```env
# No NEXT_PUBLIC_API_BASE_URL needed!
# Frontend always uses /api (relative path)
# Nginx will proxy /api/* to backend
```

**Build برای production:**

```bash
npm run build
```

### 6. PM2 Setup

#### بررسی ecosystem file:

```bash
# از root directory پروژه
cat pm2.ecosystem.config.js
```

#### Start با PM2:

**مهم:** قبل از start، مطمئن شوید که:
1. Frontend build شده است: `cd apps/frontend && npm run build`
2. Backend virtual environment آماده است
3. Environment variables تنظیم شده‌اند

```bash
# از root directory پروژه
pm2 start pm2.ecosystem.config.js

# یا با استفاده از script (recommended):
# Windows PowerShell:
.\start-pm2.ps1

# Linux/Mac:
chmod +x start-pm2.sh
./start-pm2.sh

# یا با نام مشخص:
pm2 start pm2.ecosystem.config.js --only chatbot-backend
pm2 start pm2.ecosystem.config.js --only chatbot-frontend
```

**نکته:** اگر frontend build نشده باشد، PM2 خطا می‌دهد. حتماً قبل از start، `npm run build` را در `apps/frontend` اجرا کنید.

#### بررسی status:

```bash
pm2 status
pm2 logs
pm2 logs chatbot-backend
pm2 logs chatbot-frontend
```

#### Save PM2 configuration:

```bash
pm2 save
pm2 startup  # Follow instructions to enable on boot
```

### 7. Nginx Setup (Reverse Proxy)

#### نصب Nginx:

```bash
sudo apt install nginx -y
```

#### ایجاد config file:

```bash
sudo nano /etc/nginx/sites-available/chatbot
```

**محتوای config file:**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check (optional, bypass nginx)
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

#### Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### 8. SSL Setup (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

**مهم:** بعد از SSL، `FRONTEND_ORIGIN` را در `.env` به `https://yourdomain.com` تغییر دهید و PM2 را restart کنید.

## دستورات PM2

### مدیریت Services

```bash
# Start all
pm2 start pm2.ecosystem.config.js

# Stop all
pm2 stop all

# Restart all
pm2 restart all

# Stop specific
pm2 stop chatbot-backend
pm2 stop chatbot-frontend

# Restart specific
pm2 restart chatbot-backend
pm2 restart chatbot-frontend

# Delete from PM2
pm2 delete chatbot-backend
pm2 delete chatbot-frontend
```

### Monitoring

```bash
# Status
pm2 status

# Logs (all)
pm2 logs

# Logs (specific)
pm2 logs chatbot-backend
pm2 logs chatbot-frontend

# Monitor (real-time)
pm2 monit

# Info
pm2 info chatbot-backend
pm2 info chatbot-frontend
```

### Auto-restart on Boot

```bash
# Generate startup script
pm2 startup

# Save current process list
pm2 save
```

## Troubleshooting

### Backend نمی‌شود start

```bash
# Check logs
pm2 logs chatbot-backend

# Check if port 8000 is in use
sudo lsof -i :8000

# Check Python virtual environment
cd apps/backend
source venv/bin/activate
which python
python --version

# Test manually
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend نمی‌شود start

```bash
# Check logs
pm2 logs chatbot-frontend

# Check if port 3000 is in use
sudo lsof -i :3000

# Check if build exists
ls -la apps/frontend/.next

# Rebuild if needed
cd apps/frontend
npm run build
```

### Database Connection Error

```bash
# Check PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"

# Test connection
psql -U chatbot_user -d chatbot_db -h localhost
```

### Environment Variables

```bash
# Check backend env
cd apps/backend
cat .env

# Check frontend env
cd apps/frontend
cat .env.local

# Reload PM2 after env changes
pm2 restart all
```

## Update/Deploy جدید

```bash
# Pull latest code
git pull origin main

# Backend
cd apps/backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
pm2 restart chatbot-backend

# Frontend
cd apps/frontend
npm install
npm run build
pm2 restart chatbot-frontend
```

## Backup

### Database Backup (PostgreSQL)

```bash
# Backup
pg_dump -U chatbot_user chatbot_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U chatbot_user chatbot_db < backup_20240101.sql
```

### Database Backup (SQLite)

```bash
# Backup
cp apps/backend/chatbot.db backup_$(date +%Y%m%d).db
```

## Security Checklist

- [ ] `SESSION_SECRET` قوی و random است
- [ ] `OPENAI_API_KEY` در `.env` است (نه در code)
- [ ] `FRONTEND_ORIGIN` به domain واقعی تنظیم شده
- [ ] SSL/HTTPS فعال است
- [ ] Firewall تنظیم شده (فقط 80, 443, 22 باز)
- [ ] Database password قوی است
- [ ] Admin user password قوی است
- [ ] `.env` files در `.gitignore` هستند

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Components health
curl http://localhost:8000/health/components

# Frontend (should return HTML)
curl http://localhost:3000
```

### PM2 Monitoring

```bash
# Real-time monitoring
pm2 monit

# Process info
pm2 describe chatbot-backend
pm2 describe chatbot-frontend
```

## Rollback

اگر مشکلی پیش آمد:

```bash
# Stop all
pm2 stop all

# Checkout previous version
git checkout <previous-commit-hash>

# Rebuild and restart
cd apps/frontend && npm run build && cd ../..
pm2 restart all
```

## Support

برای مشکلات:
1. Check logs: `pm2 logs`
2. Check health: `curl http://localhost:8000/health/components`
3. Check nginx: `sudo nginx -t && sudo systemctl status nginx`
4. Check PM2: `pm2 status`

