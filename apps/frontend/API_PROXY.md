# API Proxy Configuration

این پروژه از **relative path** برای API calls استفاده می‌کند تا با nginx reverse proxy سازگار باشد.

## معماری

### Frontend → API Calls
- Frontend **همیشه** از `/api` استفاده می‌کند (relative path)
- هیچ‌وقت مستقیماً به `http://localhost:8000` یا port خاصی متصل نمی‌شود

### Development (Local)
- Next.js rewrite rule `/api/*` را به `BACKEND_URL` proxy می‌کند
- Default: `http://localhost:8000`

### Production (Server)
- Nginx reverse proxy `/api/*` را به backend proxy می‌کند
- Frontend کد تغییر نمی‌کند

## فایل‌های مرتبط

### `lib/api.ts`
```typescript
// همیشه از /api استفاده می‌کند
function getApiUrl(): string {
  return '/api'
}
```

### `next.config.js`
```javascript
async rewrites() {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
  return [
    {
      source: '/api/:path*',
      destination: `${backendUrl}/:path*`,
    },
  ]
}
```

## Environment Variables

### Development
```env
# Optional: برای local development
BACKEND_URL=http://localhost:8000
```

### Production
```env
# در production با nginx، این variable نیاز نیست
# Nginx خودش /api/* را به backend proxy می‌کند
```

## مزایا

1. ✅ **یکسان در Development و Production**: Frontend کد تغییر نمی‌کند
2. ✅ **سازگار با Nginx**: Nginx فقط `/api/*` را proxy می‌کند
3. ✅ **بدون Hardcode**: هیچ URL یا port در کد hardcode نشده
4. ✅ **امن**: Frontend هیچ‌وقت مستقیماً به backend متصل نمی‌شود

## مثال

### Request Flow

**Development:**
```
Browser → /api/chat
  ↓
Next.js Rewrite → http://localhost:8000/chat
  ↓
Backend (Port 8000)
```

**Production:**
```
Browser → /api/chat
  ↓
Nginx → http://localhost:8000/chat
  ↓
Backend (Port 8000)
```

## Troubleshooting

### API calls fail in development
- مطمئن شوید `BACKEND_URL` در `.env.local` تنظیم شده
- مطمئن شوید backend روی port 8000 در حال اجرا است

### API calls fail in production
- مطمئن شوید nginx config درست است
- مطمئن شوید nginx `/api/*` را به backend proxy می‌کند



