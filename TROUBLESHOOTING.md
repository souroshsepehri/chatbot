# Troubleshooting Guide

## Common Issues and Solutions

### 1. Chatbot Not Responding / Network Errors

**Symptoms:**
- Chat widget shows "خطای اتصال" or "Network error"
- Messages don't get responses

**Solutions:**

1. **Check if backend is running:**
   ```bash
   # Check if backend is accessible
   curl http://127.0.0.1:8000/health
   # or
   curl http://127.0.0.1:8001/health  # if using dev mode
   ```

2. **Verify backend port matches frontend config:**
   - Production mode: Backend should be on port 8000
   - Dev mode: Backend should be on port 8001
   - Check `apps/frontend/next.config.js` - should match backend port

3. **Check CORS configuration:**
   - Backend `FRONTEND_ORIGIN` should match frontend port
   - Production: `http://localhost:3000`
   - Dev: `http://localhost:3001`
   - Backend config supports both ports automatically

4. **Restart backend:**
   ```bash
   # Stop any running backend
   # Then start fresh:
   cd apps/backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

### 2. Admin Panel Infinite Redirect Loop

**Symptoms:**
- Admin panel keeps redirecting to login
- Console shows repeated auth errors

**Solutions:**

1. **Clear browser cookies:**
   - Open browser DevTools (F12)
   - Application/Storage tab
   - Clear cookies for `localhost:3000` or `localhost:3001`

2. **Check backend is running:**
   - Admin panel needs backend to authenticate
   - Verify: `curl http://127.0.0.1:8000/health`

3. **Verify admin user exists:**
   ```bash
   cd apps/backend
   python create_admin.py
   # Default: admin / admin123
   ```

4. **Check browser console:**
   - Look for specific error messages
   - Network tab: Check if API calls are failing

### 3. Port Mismatch Issues

**Problem:** Frontend and backend using different ports

**Solution:**

1. **For Production Mode:**
   - Backend: Port 8000
   - Frontend: Port 3000
   - Update `.env` in `apps/backend`: `FRONTEND_ORIGIN=http://localhost:3000`

2. **For Dev Mode:**
   - Backend: Port 8001
   - Frontend: Port 3001
   - Backend config automatically allows both ports

3. **Check Next.js rewrite:**
   - `apps/frontend/next.config.js` should have correct backend URL
   - Default: `http://127.0.0.1:8000` for production

### 4. Database Connection Errors

**Symptoms:**
- Backend logs show database errors
- API returns 500 errors

**Solutions:**

1. **Run migrations:**
   ```bash
   cd apps/backend
   alembic upgrade head
   ```

2. **Check database file exists:**
   ```bash
   # SQLite default location
   ls apps/backend/chatbot.db
   ```

3. **Create database if missing:**
   ```bash
   cd apps/backend
   python setup_db.py
   ```

### 5. Quick Health Check

Run these commands to verify everything:

```bash
# 1. Check backend health
curl http://127.0.0.1:8000/health

# 2. Check frontend is running
# Open browser: http://localhost:3000

# 3. Check API proxy
# Open browser: http://localhost:3000/api/health
# Should return same as backend /health

# 4. Test chat endpoint directly
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### 6. Clean Rebuild

If nothing works, try a clean rebuild:

```bash
# 1. Clean build artifacts
npm run clean

# 2. Reinstall frontend deps
cd apps/frontend
npm ci

# 3. Build frontend
npm run build

# 4. Start backend
cd ../backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 5. Start frontend (in another terminal)
cd ../frontend
npm run start
```

## Getting Help

If issues persist:

1. Check browser console (F12) for errors
2. Check backend logs for errors
3. Verify all services are running on correct ports
4. Check network tab in browser DevTools for failed requests

