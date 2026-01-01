# Observability & Logging

راهنمای سیستم observability و logging برای production.

## Structured Logging

لاگ‌ها به صورت **structured JSON** در فایل ذخیره می‌شوند و **human-readable** در console نمایش داده می‌شوند.

### فرمت لاگ‌ها

**Console (Human-readable):**
```
[2024-01-15 10:30:45] INFO     app.routers.chat [req:abc12345] - Chat completed successfully
```

**File (JSON):**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.routers.chat",
  "message": "Chat completed successfully",
  "request_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "session_id": "xyz789",
  "llm_called": true,
  "retrieval_hits": {"kb": 2, "website": 1}
}
```

## Request ID

هر request یک **request_id** منحصر به فرد دارد که:
- در header `X-Request-ID` برگردانده می‌شود
- در تمام لاگ‌های مربوط به آن request استفاده می‌شود
- می‌توانید از client ارسال کنید (یا خودکار generate می‌شود)

### استفاده

**Client-side:**
```javascript
// می‌توانید request_id خودتان بفرستید
fetch('/api/chat', {
  headers: {
    'X-Request-ID': 'my-custom-id'
  }
})
```

**Server-side:**
- همه لاگ‌ها به صورت خودکار `request_id` دارند
- می‌توانید با `request_id` تمام لاگ‌های یک request را پیدا کنید

## لاگ‌های OpenAI

لاگ‌های OpenAI شامل:
- ✅ **error_type**: نوع خطا (APITimeoutError, APIError, etc.)
- ✅ **timeout_seconds**: timeout استفاده شده
- ✅ **model**: مدل استفاده شده
- ✅ **error_code**: کد خطا (اگر موجود باشد)
- ✅ **error_message**: پیام خطا
- ✅ **request_id**: برای tracking

### مثال لاگ خطا:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "ERROR",
  "logger": "app.services.llm",
  "message": "OpenAI API timeout",
  "request_id": "abc123",
  "error_type": "APITimeoutError",
  "timeout_seconds": 30,
  "model": "gpt-3.5-turbo",
  "error_message": "Request timed out"
}
```

## لاگ‌های Crawler

لاگ‌های crawler شامل:
- ✅ **error_type**: نوع خطا (Timeout, RequestException, etc.)
- ✅ **url**: URL که خطا داده
- ✅ **timeout_seconds**: timeout استفاده شده
- ✅ **status_code**: HTTP status code (اگر موجود باشد)
- ✅ **error_message**: پیام خطا
- ✅ **request_id**: برای tracking

### مثال لاگ خطا:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "ERROR",
  "logger": "app.services.website_fetcher",
  "message": "Timeout fetching page",
  "request_id": "abc123",
  "error_type": "Timeout",
  "url": "https://example.com/page",
  "timeout_seconds": 10,
  "error_message": "Request timed out"
}
```

## فایل‌های لاگ

- `logs/app.log` - لاگ اصلی (JSON format)
- `logs/app.log.1`, `logs/app.log.2`, ... - backup files
- Max size: 10MB per file
- Max backups: 5 files

## جستجوی لاگ‌ها

### با request_id:
```bash
# Linux/Mac
grep "abc123" logs/app.log

# Windows PowerShell
Select-String -Path logs/app.log -Pattern "abc123"
```

### با jq (برای JSON):
```bash
# Linux/Mac
cat logs/app.log | jq 'select(.request_id == "abc123")'
```

### خطاهای OpenAI:
```bash
grep "OpenAI" logs/app.log | jq 'select(.level == "ERROR")'
```

### خطاهای Crawler:
```bash
grep "website_fetcher" logs/app.log | jq 'select(.level == "ERROR")'
```

## نکات مهم

1. ✅ **Structured**: همه لاگ‌ها structured هستند (JSON در file)
2. ✅ **Request ID**: هر request یک ID منحصر به فرد دارد
3. ✅ **Error Details**: خطاهای OpenAI و crawler جزئیات کامل دارند
4. ✅ **Production-Ready**: برای production و debugging مناسب است

## مثال‌های لاگ

### Chat Request:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.routers.chat",
  "message": "Chat completed successfully",
  "request_id": "abc123",
  "session_id": "xyz789",
  "llm_called": true,
  "retrieval_hits": {"kb": 2, "website": 1},
  "answer_length": 150,
  "sources_count": 3
}
```

### OpenAI Error:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "ERROR",
  "logger": "app.services.llm",
  "message": "OpenAI API timeout",
  "request_id": "abc123",
  "error_type": "APITimeoutError",
  "timeout_seconds": 30,
  "model": "gpt-3.5-turbo"
}
```

### Crawler Error:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "ERROR",
  "logger": "app.services.website_fetcher",
  "message": "Timeout fetching page",
  "request_id": "abc123",
  "error_type": "Timeout",
  "url": "https://example.com/page",
  "timeout_seconds": 10
}
```





