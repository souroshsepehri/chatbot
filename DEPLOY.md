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

### 5. Nginx Production Setup

#### 5.1. Install Nginx and Certbot
```bash
# Update package list
sudo apt update

# Install Nginx
sudo apt install -y nginx

# Install Certbot for SSL certificates
sudo apt install -y certbot python3-certbot-nginx

# Check Nginx status
sudo systemctl status nginx
```

#### 5.2. Configure Nginx

**Replace `DOMAIN` with your actual domain (e.g., `chatbot.example.com`).**
**If you don't have a domain, use your server IP address and skip SSL steps.**

```bash
# Copy the template config
sudo cp deploy/nginx/chatbot.conf /etc/nginx/sites-available/chatbot

# Edit the config and replace DOMAIN placeholder
sudo nano /etc/nginx/sites-available/chatbot
# Replace all occurrences of "DOMAIN" with your actual domain or IP

# If using IP address instead of domain, replace:
# server_name DOMAIN;  ->  server_name YOUR_SERVER_IP;

# Enable the site
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/

# Remove default nginx site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

#### 5.3. SSL Certificate Setup (Skip if using IP only)

**Replace `DOMAIN` and `EMAIL` with your actual values:**

```bash
# Obtain SSL certificate with Let's Encrypt
sudo certbot --nginx -d DOMAIN --email EMAIL --agree-tos --non-interactive

# Example:
# sudo certbot --nginx -d chatbot.example.com --email admin@example.com --agree-tos --non-interactive
```

**After SSL certificate is obtained:**

1. Edit the config again to uncomment HTTPS server block:
```bash
sudo nano /etc/nginx/sites-available/chatbot
# Uncomment the HTTPS server block (lines starting with # server {)
# Replace DOMAIN in SSL certificate paths if needed
```

2. Test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### 5.4. Configure SSL Auto-Renewal

```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Certbot automatically sets up renewal via systemd timer
# Verify it's enabled:
sudo systemctl status certbot.timer

# Check renewal schedule
sudo systemctl list-timers | grep certbot
```

#### 5.5. Verify Deployment

```bash
# Test backend health endpoint
curl http://DOMAIN/api/health
# or if using IP:
curl http://YOUR_SERVER_IP/api/health

# Test frontend
curl http://DOMAIN
# or if using IP:
curl http://YOUR_SERVER_IP

# Test with HTTPS (if SSL configured)
curl https://DOMAIN/api/health
curl https://DOMAIN
```

### 6. Firewall Hardening (UFW)

**Important:** Backend and frontend already bind to 127.0.0.1, but firewall provides additional security.

```bash
# Check UFW status
sudo ufw status

# Allow OpenSSH (CRITICAL - do this first!)
sudo ufw allow OpenSSH

# Allow Nginx (HTTP and HTTPS)
sudo ufw allow 'Nginx Full'

# Deny direct access to application ports (they're behind Nginx)
# Port 3000 (frontend) - already bound to 127.0.0.1, but explicit deny for safety
sudo ufw deny 3000

# Port 8000 (backend) - already bound to 127.0.0.1, but explicit deny for safety
sudo ufw deny 8000

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status numbered

# Check firewall is active
sudo ufw status verbose
```

**Firewall Rules Summary:**
- ✅ OpenSSH (port 22) - allowed
- ✅ Nginx Full (ports 80, 443) - allowed
- ❌ Port 3000 - denied (frontend only accessible via Nginx)
- ❌ Port 8000 - denied (backend only accessible via Nginx)

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
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Check if Nginx is running
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx

# Verify backend/frontend are accessible locally
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3000

# Check firewall isn't blocking
sudo ufw status
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
5. ✅ Replace `DOMAIN` placeholder in `deploy/nginx/chatbot.conf` before deployment
6. ✅ Configure firewall (UFW) to only allow ports 22, 80, 443
7. ✅ Backend and frontend bind to 127.0.0.1 - only accessible via Nginx

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





