# Production Deployment Guide - Subdomain with Nginx + SSL

This guide provides step-by-step instructions for deploying the chatbot application on a subdomain using Nginx as a reverse proxy with SSL/TLS encryption.

## Prerequisites

- Ubuntu/Debian server with root or sudo access
- Domain name with DNS access
- PM2 processes already running:
  - Frontend: `http://127.0.0.1:3000` (PM2: `chatbot-frontend`)
  - Backend: `http://127.0.0.1:8000` (PM2: `chatbot-backend`)

## Placeholders

Replace these placeholders throughout this guide:
- `<SUBDOMAIN>` - Your subdomain (e.g., `chatbot.example.com`)
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

You must verify that your subdomain resolves to your server's public IP. Use one or both of these methods:

**Option 1: Using `getent`**
```bash
getent hosts <SUBDOMAIN>
```

**Option 2: Using `dig`**
```bash
dig +short <SUBDOMAIN>
```

**Example output:**
```
# getent hosts chatbot.example.com
203.0.113.42    chatbot.example.com

# dig +short chatbot.example.com
203.0.113.42
```

### A.3. DNS Verification Check

**Compare the resolved IP with your server's public IP:**

```bash
SERVER_IP=$(curl -s ifconfig.me)
RESOLVED_IP=$(dig +short <SUBDOMAIN> | head -n1)

echo "Server IP: $SERVER_IP"
echo "Resolved IP: $RESOLVED_IP"

if [ "$SERVER_IP" = "$RESOLVED_IP" ]; then
    echo "✅ DNS is correctly configured"
else
    echo "❌ ERROR: DNS mismatch!"
    echo "The subdomain <SUBDOMAIN> resolves to $RESOLVED_IP"
    echo "But your server IP is $SERVER_IP"
    echo ""
    echo "STOP HERE and fix your DNS A record:"
    echo "  - Go to your domain DNS settings"
    echo "  - Create/update A record: <SUBDOMAIN> -> $SERVER_IP"
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

# Enable Nginx to start on boot
sudo systemctl enable nginx

# Start Nginx service
sudo systemctl start nginx

# Verify Nginx is running
sudo systemctl status nginx
```

---

## Step C: Apply Nginx Configuration

### C.1. Copy Configuration Template

```bash
# Copy the subdomain config template
sudo cp deploy/nginx/chatbot-subdomain.conf /etc/nginx/sites-available/<SUBDOMAIN>
```

### C.2. Replace Placeholders

```bash
# Edit the config file
sudo nano /etc/nginx/sites-available/<SUBDOMAIN>
```

**Replace all occurrences of `<SUBDOMAIN>` with your actual subdomain:**
- `server_name <SUBDOMAIN>;` → `server_name chatbot.example.com;`

**Save and exit** (Ctrl+X, then Y, then Enter).

### C.3. Enable the Site

```bash
# Create symlink to enable the site
sudo ln -s /etc/nginx/sites-available/<SUBDOMAIN> /etc/nginx/sites-enabled/

# Remove default Nginx site (optional, but recommended)
sudo rm /etc/nginx/sites-enabled/default
```

### C.4. Test and Reload Nginx

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
sudo certbot --nginx -d <SUBDOMAIN> -m <EMAIL> --agree-tos --redirect
```

**Example:**
```bash
sudo certbot --nginx -d chatbot.example.com -m admin@example.com --agree-tos --redirect
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
  /etc/letsencrypt/live/<SUBDOMAIN>/fullchain.pem (success)
```

**Note:** Certbot automatically sets up a systemd timer for renewal. Verify it's enabled:
```bash
sudo systemctl status certbot.timer
```

---

## Step E: Firewall Hardening with UFW (Optional but Recommended)

**Important:** Backend and frontend already bind to `127.0.0.1`, but firewall provides additional security.

### E.1. Configure UFW Rules

```bash
# Check current UFW status
sudo ufw status

# Allow OpenSSH (CRITICAL - do this first!)
sudo ufw allow OpenSSH

# Allow Nginx (HTTP and HTTPS)
sudo ufw allow 'Nginx Full'

# Explicitly deny direct access to application ports
# (Services bind to 127.0.0.1 anyway, but explicit deny for safety)
sudo ufw deny 3000
sudo ufw deny 8000

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status numbered
```

**Expected firewall rules:**
- ✅ OpenSSH (port 22) - allowed
- ✅ Nginx Full (ports 80, 443) - allowed
- ❌ Port 3000 - denied (frontend only accessible via Nginx)
- ❌ Port 8000 - denied (backend only accessible via Nginx)

---

## Step F: Post-Deployment Verification

### F.1. Verify HTTP Redirect

```bash
# Check HTTP redirects to HTTPS
curl -I http://<SUBDOMAIN>
```

**Expected output:**
```
HTTP/1.1 301 Moved Permanently
Location: https://<SUBDOMAIN>/
```

### F.2. Verify HTTPS Frontend

```bash
# Check HTTPS frontend
curl -I https://<SUBDOMAIN>
```

**Expected output:**
```
HTTP/2 200
...
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### F.3. Verify Backend API

```bash
# Check backend health endpoint via Nginx
curl -I https://<SUBDOMAIN>/api/health
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
curl https://<SUBDOMAIN>

# Test backend API
curl https://<SUBDOMAIN>/api/health

# Test chat endpoint (should return JSON)
curl -X POST https://<SUBDOMAIN>/api/chat \
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
dig +short <SUBDOMAIN>

# Check DNS from external location
# Use online tools like: https://dnschecker.org

# Verify DNS propagation
dig <SUBDOMAIN> @8.8.8.8
```

---

## Security Checklist

- ✅ DNS A record correctly points to server IP
- ✅ Nginx configured with security headers
- ✅ SSL certificate installed and auto-renewal configured
- ✅ HTTP redirects to HTTPS
- ✅ Firewall (UFW) configured to deny ports 3000/8000
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
curl https://<SUBDOMAIN>/api/health
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
dig +short <SUBDOMAIN>

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
- **Gzip**: Disabled by default in the configuration (can be enabled if needed)
