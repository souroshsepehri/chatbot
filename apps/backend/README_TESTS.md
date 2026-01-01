# Test Suite

راهنمای اجرای تست‌های اجباری پروژه.

## تست‌های اجباری

پروژه شامل 6+ تست اجباری است که باید همگی pass شوند:

1. ✅ **chat بدون هیچ source → refusal و llm_called=false**
   - `test_chat_refusal_when_kb_empty_and_website_disabled`
   - `test_chat_refusal_when_kb_empty_and_no_website_sources`

2. ✅ **chat با kb hit → جواب + sources و llm_called=true**
   - `test_chat_with_kb_hit_returns_answer_and_calls_llm`

3. ✅ **admin بدون login → 401**
   - `test_admin_endpoint_without_login_returns_401`

4. ✅ **admin بعد از 5 دقیقه → 401**
   - `test_admin_endpoint_after_session_expiry_returns_401`

5. ✅ **website crawl فقط same-domain**
   - `test_crawl_only_same_domain`
   - `test_crawl_respects_max_pages`

6. ✅ **/health/components db check واقعی**
   - `test_health_components_db_check_is_real`
   - `test_health_components_checks_all_components`

## اجرای تست‌ها

### روش 1: pytest مستقیم

```bash
# از directory apps/backend
pytest -q
```

یا:

```bash
python -m pytest tests/ -q
```

### روش 2: Scripts

**Windows:**
```powershell
.\scripts\test_all.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/test_all.sh
./scripts/test_all.sh
```

### روش 3: با verbose output

```bash
pytest -v
```

## ساختار تست‌ها

```
tests/
├── conftest.py              # Test fixtures (client, db)
├── test_chat_refusal.py     # Chat refusal tests
├── test_chat_with_sources.py # Chat with sources tests
├── test_admin_auth.py       # Admin authentication tests
├── test_website_crawl.py     # Website crawling tests
└── test_health_check.py     # Health check tests
```

## نکات مهم

- ✅ همه تست‌ها از in-memory SQLite استفاده می‌کنند
- ✅ OpenAI API mock می‌شود (نیازی به API key واقعی نیست)
- ✅ هر تست database جداگانه دارد (isolated)
- ✅ تست‌ها باید سریع اجرا شوند (< 10 ثانیه)

## Troubleshooting

### ModuleNotFoundError
```bash
# مطمئن شوید dependencies نصب شده‌اند
pip install -r requirements.txt
```

### Database errors
```bash
# مطمئن شوید migration ها اجرا شده‌اند
alembic upgrade head
```

### Import errors
```bash
# مطمئن شوید از directory صحیح اجرا می‌کنید
cd apps/backend
pytest -q
```





