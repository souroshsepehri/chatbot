# Nginx Commands Reference

## Testing Configuration

```bash
# Test nginx configuration for syntax errors
sudo nginx -t
```

**Expected output if successful:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If there are errors**, it will show the line number and error message.

## Reloading Nginx

```bash
# Reload nginx configuration (graceful - doesn't drop connections)
sudo systemctl reload nginx

# OR alternative command:
sudo nginx -s reload
```

**Other useful nginx commands:**

```bash
# Check nginx status
sudo systemctl status nginx

# Start nginx
sudo systemctl start nginx

# Stop nginx
sudo systemctl stop nginx

# Restart nginx (drops connections)
sudo systemctl restart nginx

# View nginx error logs
sudo tail -f /var/log/nginx/error.log

# View nginx access logs
sudo tail -f /var/log/nginx/access.log

# Check if nginx is running
sudo systemctl is-active nginx
```

## Complete Setup Process

1. **Copy configuration:**
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/chatbot
   sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
   ```

2. **Edit domain name:**
   ```bash
   sudo nano /etc/nginx/sites-available/chatbot
   # Replace 'yourdomain.com' with your actual domain
   ```

3. **Test configuration:**
   ```bash
   sudo nginx -t
   ```

4. **If test passes, reload:**
   ```bash
   sudo systemctl reload nginx
   ```

5. **Verify it's working:**
   ```bash
   sudo systemctl status nginx
   ```

## Troubleshooting

If `nginx -t` fails:
- Check the error message for the line number
- Common issues: missing semicolons, wrong paths, syntax errors
- Verify all paths in the config exist

If reload fails:
- Check nginx error log: `sudo tail -f /var/log/nginx/error.log`
- Make sure backend (port 8000) and frontend (port 3000) are running
- Check if ports 80/443 are already in use: `sudo netstat -tulpn | grep -E ':(80|443)'`





