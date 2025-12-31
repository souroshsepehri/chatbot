# Nginx Setup Guide

## Installation

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install nginx
```

### CentOS/RHEL:
```bash
sudo yum install nginx
```

## Configuration

1. **Copy the configuration file:**
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/chatbot
   sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
   ```

2. **Edit the configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/chatbot
   ```
   
   Replace `yourdomain.com` with your actual domain name.

3. **Test the configuration:**
   ```bash
   sudo nginx -t
   ```

4. **Reload nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

## Important Notes

- Replace `yourdomain.com` with your actual domain
- For HTTPS, uncomment the HTTPS server block and configure SSL certificates
- Make sure your backend (port 8000) and frontend (port 3000) are running
- The `/api/` path will be proxied to the backend
- All other paths will be proxied to the frontend

## Frontend Configuration

When using nginx, set the frontend environment variable:

```bash
# In apps/frontend/.env.production or .env.local
NEXT_PUBLIC_API_URL=/api
```

This tells the frontend to use the `/api` prefix which nginx will proxy to the backend.

For development (without nginx), use:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## SSL Certificate Setup (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Troubleshooting

- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Check if ports are open: `sudo netstat -tulpn | grep -E ':(80|443)'`
- Verify backend/frontend are running: `pm2 status`

