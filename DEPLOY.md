# Production Deployment Guide - chatbot.zimmerai.com

This guide provides step-by-step instructions for deploying the chatbot application on `chatbot.zimmerai.com` using Nginx as a reverse proxy with SSL/TLS encryption.

## Prerequisites

- Ubuntu/Debian server with root or sudo access
- PM2 processes already running:
  - Frontend: `http://127.0.0.1:3000` (PM2: `chatbot-frontend`)
  - Backend: `http://127.0.0.1:8000` (PM2: `chatbot-backend`)

## Placeholder

Replace this placeholder:
- `<EMAIL>` - Your email address for Let's Encrypt notifications

---

## Step A: DNS Verification (BEFORE SSL Setup)

**⚠️ CRITICAL: Verify DNS is correctly configured before proceeding with SSL setup.**

### A.1. Determine Server Public IP

```bash
curl -s ifconfig.me
```

**Save this IP address** - you'll need it for DNS verification.

### A.2. Verify Subdomain DNS Resolution

Check that `chatbot.zimmerai.com` resolves to your server's public IP:

```bash
getent hosts chatbot.zimmerai.com
```

**Alternative using dig:**
```bash
dig +short chatbot.zimmerai.com
```

**Example output:**
```
# getent hosts chatbot.zimmerai.com
203.0.113.42    chatbot.zimmerai.com

# dig +short chatbot.zimmerai.com
203.0.113.42
```

### A.3. DNS Verification Check

**Compare the resolved IP with your server's public IP:**

```bash
SERVER_IP=$(curl -s ifconfig.me)
RESOLVED_IP=$(dig +short chatbot.zimmerai.com | head -n1)

echo "Server IP: $SERVER_IP"
echo "Resolved IP: $RESOLVED_IP"

if [ "$SERVER_IP" = "$RESOLVED_IP" ]; then
    echo "✅ DNS is correctly configured"
else
    echo "❌ ERROR: DNS mismatch!"
    echo "The subdomain chatbot.zimmerai.com resolves to $RESOLVED_IP"
    echo "But your server IP is $SERVER_IP"
    echo ""
    echo "STOP HERE and fix your DNS A record:"
    echo "  - Go to your domain DNS settings"
    echo "  - Create/update A record: chatbot.zimmerai.com -> $SERVER_IP"
    echo "  - Wait for DNS propagation (can take up to 48 hours)"
    echo "  - Re-run this verification before proceeding"
    exit 1
fi
```

**⚠️ If resolved IP != server IP, STOP and fix DNS A record before continuing.**

---

## Step B: Install Nginx

```bash
# Update package list
sudo apt update

# Install Nginx
sudo apt install -y nginx

# Enable and start Nginx
sudo systemctl enable --now nginx

# Verify Nginx is running
sudo systemctl status nginx
```

---

## Step C: Apply Nginx Configuration

### C.1. Copy Configuration File

```bash
# Copy the config file
sudo cp deploy/nginx/chatbot.zimmerai.com.conf /etc/nginx/sites-available/chatbot.zimmerai.com
```

### C.2. Enable the Site

```bash
# Create symlink to enable the site
sudo ln -sf /etc/nginx/sites-available/chatbot.zimmerai.com /etc/nginx/sites-enabled/chatbot.zimmerai.com

# Remove default Nginx site (optional, but recommended)
sudo rm -f /etc/nginx/sites-enabled/default
```

### C.3. Test and Reload Nginx

```bash
# Test Nginx configuration for syntax errors
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If test passes, reload Nginx:**
```bash
sudo systemctl reload nginx
```

---

## Step D: Install SSL Certificate with Certbot

### D.1. Install Certbot

```bash
# Install Certbot and Nginx plugin
sudo apt install -y certbot python3-certbot-nginx
```

### D.2. Obtain SSL Certificate

```bash
# Obtain SSL certificate (certbot will automatically configure Nginx)
sudo certbot --nginx -d chatbot.zimmerai.com -m <EMAIL> --agree-tos --redirect
```

**Example:**
```bash
sudo certbot --nginx -d chatbot.zimmerai.com -m admin@zimmerai.com --agree-tos --redirect
```

**What this does:**
- Obtains SSL certificate from Let's Encrypt
- Automatically configures Nginx HTTPS server block
- Sets up HTTP to HTTPS redirect
- Configures automatic renewal

### D.3. Verify Certificate Renewal

```bash
# Test certificate renewal (dry run)
sudo certbot renew --dry-run
```

**Expected output:**
```
Congratulations, all renewals succeeded. The following certs have been renewed:
  /etc/letsencrypt/live/chatbot.zimmerai.com/fullchain.pem (success)
```

**Note:** Certbot automatically sets up a systemd timer for renewal. Verify it's enabled:
```bash
sudo systemctl status certbot.timer
```

---

## Step E: Firewall Hardening with UFW (Optional but Recommended)

**Important:** Backend and frontend already bind to `127.0.0.1`, so ports 3000/8000 are not publicly reachable anyway. Firewall provides additional security.

### E.1. Configure UFW Rules

```bash
# Allow OpenSSH (CRITICAL - do this first!)
sudo ufw allow OpenSSH

# Allow Nginx (HTTP and HTTPS)
sudo ufw allow 'Nginx Full'

# Enable firewall
sudo ufw --force enable

# Verify rules
sudo ufw status numbered
```

**Expected firewall rules:**
- ✅ OpenSSH (port 22) - allowed
- ✅ Nginx Full (ports 80, 443) - allowed
- Note: Ports 3000/8000 are not publicly reachable (bind to 127.0.0.1)

---

## Step F: Post-Deployment Verification

### F.1. Verify HTTP Redirect

```bash
# Check HTTP redirects to HTTPS
curl -I http://chatbot.zimmerai.com
```

**Expected output:**
```
HTTP/1.1 301 Moved Permanently
Location: https://chatbot.zimmerai.com/
```

### F.2. Verify HTTPS Frontend

```bash
# Check HTTPS frontend
curl -I https://chatbot.zimmerai.com
```

**Expected output:**
```
HTTP/2 200
...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### F.3. Verify Backend API

```bash
# Check backend health endpoint via Nginx
curl -I https://chatbot.zimmerai.com/api/health
```

**Expected output:**
```
HTTP/2 200
...
```

### F.4. Verify PM2 Processes

```bash
# Check PM2 processes are running
pm2 status
```

**Expected output:**
```
┌─────┬──────────────────────┬─────────┬─────────┬──────────┐
│ id  │ name                 │ status  │ restart │ uptime   │
├─────┼──────────────────────┼─────────┼─────────┼──────────┤
│ 0   │ chatbot-backend      │ online  │ 0       │ 2h       │
│ 1   │ chatbot-frontend     │ online  │ 0       │ 2h       │
└─────┴──────────────────────┴─────────┴─────────┴──────────┘
```

### F.5. Test Full Stack

```bash
# Test frontend
curl https://chatbot.zimmerai.com

# Test backend API
curl https://chatbot.zimmerai.com/api/health

# Test chat endpoint (should return JSON)
curl -X POST https://chatbot.zimmerai.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

---

## Troubleshooting

### Nginx Configuration Errors

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Check access logs
sudo tail -f /var/log/nginx/access.log

# Restart Nginx if needed
sudo systemctl restart nginx
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Manually renew certificate
sudo certbot renew

# Check certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Backend/Frontend Not Accessible

```bash
# Verify services are running locally
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3000

# Check PM2 logs
pm2 logs chatbot-backend
pm2 logs chatbot-frontend

# Restart PM2 processes
pm2 restart all
```

### Firewall Issues

```bash
# Check firewall status
sudo ufw status verbose

# Check if ports are blocked
sudo netstat -tulpn | grep -E ':(3000|8000)'

# Temporarily disable firewall for testing (NOT recommended in production)
# sudo ufw disable
```

### DNS Issues

```bash
# Verify DNS resolution from server
dig +short chatbot.zimmerai.com

# Check DNS from external location
# Use online tools like: https://dnschecker.org

# Verify DNS propagation
dig chatbot.zimmerai.com @8.8.8.8
```

---

## Security Checklist

- ✅ DNS A record correctly points to server IP
- ✅ Nginx configured with security headers
- ✅ SSL certificate installed and auto-renewal configured
- ✅ HTTP redirects to HTTPS
- ✅ Firewall (UFW) configured to allow only ports 22, 80, 443
- ✅ Backend and frontend bind to 127.0.0.1 (not 0.0.0.0)
- ✅ PM2 processes running and healthy
- ✅ All proxy headers correctly set (X-Real-IP, X-Forwarded-For, etc.)

---

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild frontend
cd apps/frontend
npm install
npm run build
cd ../..

# Restart PM2 processes
pm2 restart all

# Verify services
pm2 status
curl https://chatbot.zimmerai.com/api/health
```

### Renew SSL Certificate Manually

```bash
# Certbot auto-renews, but you can manually renew:
sudo certbot renew

# Reload Nginx after renewal
sudo systemctl reload nginx
```

### View Logs

```bash
# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PM2 logs
pm2 logs chatbot-backend
pm2 logs chatbot-frontend

# Application logs
tail -f apps/backend/logs/app.log
```

---

## Quick Reference

```bash
# Check DNS
dig +short chatbot.zimmerai.com

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check SSL certificate
sudo certbot certificates

# Check PM2 status
pm2 status

# View all logs
pm2 logs
sudo tail -f /var/log/nginx/error.log
```

---

## Notes

- **No public access to ports 3000/8000**: Services bind to `127.0.0.1` and are only accessible via Nginx
- **WebSocket support**: Nginx configuration includes WebSocket upgrade headers for Next.js and chat functionality
- **Timeouts**: Backend API has 120s timeouts for LLM chat requests; frontend has 60s timeouts
- **Security headers**: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, and HSTS are configured
- **X-Frame-Options**: Set to DENY for maximum security (prevents iframe embedding)
