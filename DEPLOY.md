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

**Recommended: Use your cloud provider's control panel as the source of truth for your server's public IPv4 address.**

**Alternative methods (if provider panel unavailable):**

**Option 1: Get default route interface IP (may show NAT IP):**
```bash
ip route get 1.1.1.1 | awk '{print $7; exit}'
```

**Option 2: Show all local IPs (interpret carefully):**
```bash
hostname -I
```
*Note: This shows all local IP addresses. The first IPv4 address is typically the primary interface, but may be a private IP if behind NAT.*

**⚠️ Important:** For Let's Encrypt SSL certificate validation, the DNS A record must point to the server's **public IPv4 address** as shown in your cloud provider's control panel (AWS, DigitalOcean, Linode, etc.). If your server is behind NAT, use the public IP assigned by your provider, not the private IP.

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

**Compare the resolved IP with your server's public IP from the provider panel:**

```bash
# Get resolved IP from DNS
RESOLVED_IP=$(dig +short chatbot.zimmerai.com | head -n1)

echo "Resolved IP: $RESOLVED_IP"
echo ""
echo "Compare this with your server's public IPv4 from your cloud provider panel."
echo "If they don't match, STOP and fix your DNS A record."
```

**Manual verification:**
1. Check your cloud provider's control panel for the server's public IPv4 address
2. Compare it with the resolved IP from DNS
3. If they match: ✅ DNS is correctly configured
4. If they don't match: ❌ Fix your DNS A record before proceeding

**⚠️ If resolved IP != server public IP, STOP and fix DNS A record before continuing.**

### A.4. Special Cases: NAT and Cloudflare Proxy

**If behind NAT:**
- Use the public IP shown in your cloud provider panel (not the private IP)
- The DNS A record must point to this public IP
- Let's Encrypt will validate against this public IP

**If using Cloudflare (or similar proxy):**
- **For Let's Encrypt SSL:** The DNS A record must be set to **DNS only** (gray cloud, not proxied/orange cloud)
  - Proxied DNS (orange cloud) hides your server IP and will cause Let's Encrypt validation to fail
  - After SSL is set up, you can optionally enable proxying, but initial SSL setup requires DNS-only mode
- Verify DNS-only mode: `dig +short chatbot.zimmerai.com` should return your server's public IP, not Cloudflare's IPs

---

## Step B: Install Nginx

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

---

## Step C: Apply Nginx Configuration

```bash
sudo cp deploy/nginx/chatbot.zimmerai.com.conf /etc/nginx/sites-available/chatbot.zimmerai.com
sudo ln -sf /etc/nginx/sites-available/chatbot.zimmerai.com /etc/nginx/sites-enabled/chatbot.zimmerai.com
# optional disable default site if enabled
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step D: Install Certbot and Issue SSL

**Replace `<EMAIL>` with your email address:**

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d chatbot.zimmerai.com -m <EMAIL> --agree-tos --redirect
sudo certbot renew --dry-run
```

**Example:**
```bash
sudo certbot --nginx -d chatbot.zimmerai.com -m admin@zimmerai.com --agree-tos --redirect
```

---

## Step E: Post-Deployment Checks

```bash
curl -I http://chatbot.zimmerai.com
curl -I https://chatbot.zimmerai.com
curl -I https://chatbot.zimmerai.com/api/health
pm2 status
```

---

## Step F: UFW Firewall Hardening (Optional but Recommended)

**Note:** Backend and frontend bind to `127.0.0.1`, so ports 3000/8000 are not publicly reachable anyway.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
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
