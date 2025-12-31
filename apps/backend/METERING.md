# OpenAI Usage Metering

سیستم metering برای ردیابی استفاده از OpenAI API و جلوگیری از هزینه‌های غیرضروری.

## فیلدهای Debug

در response `/chat`، یک فیلد `debug` وجود دارد که **فقط در ENV=development** نمایش داده می‌شود:

```json
{
  "session_id": "...",
  "answer": "...",
  "sources": [...],
  "refused": false,
  "openai_called": true,
  "debug": {
    "llm_called": true,
    "retrieval_hits": {
      "kb": 2,
      "website": 1
    }
  }
}
```

## فیلدها

### `llm_called` (boolean)
- `true`: OpenAI API صدا زده شده
- `false`: OpenAI API صدا زده نشده (refusal)

### `retrieval_hits` (object)
- `kb`: تعداد نتایج از Knowledge Base
- `website`: تعداد نتایج از Website Sources

## رفتار در Production

در `ENV=production`:
- فیلد `debug` **خودکار حذف می‌شود** از response
- فقط `openai_called` باقی می‌ماند (برای backward compatibility)

## Logging

تمام اطلاعات metering در server logs نیز ثبت می‌شوند:

```
Chat refused - session_id=..., kb_results=0, website_results=0, openai_called=False
Chat completed - session_id=..., llm_called=True, retrieval_hits={'kb': 2, 'website': 1}
```

## استفاده

### Development
```bash
# در development، debug field نمایش داده می‌شود
ENV=development
```

### Production
```bash
# در production، debug field حذف می‌شود
ENV=production
```

## مثال Response

### Development (با debug):
```json
{
  "session_id": "abc123",
  "answer": "پاسخ...",
  "sources": [...],
  "refused": false,
  "openai_called": true,
  "debug": {
    "llm_called": true,
    "retrieval_hits": {
      "kb": 2,
      "website": 1
    }
  }
}
```

### Production (بدون debug):
```json
{
  "session_id": "abc123",
  "answer": "پاسخ...",
  "sources": [...],
  "refused": false,
  "openai_called": true
}
```

## مزایا

1. ✅ **Proof**: می‌توانید ثابت کنید OpenAI بی‌خودی صدا نمی‌خورد
2. ✅ **Cost Tracking**: می‌توانید ببینید چرا هزینه بالا رفته
3. ✅ **Debugging**: می‌توانید مشکلات retrieval را پیدا کنید
4. ✅ **Security**: در production، debug info نمایش داده نمی‌شود



