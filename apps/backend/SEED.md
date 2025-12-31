# Database Seeding

راهنمای استفاده از seed script برای پر کردن database با داده‌های demo.

## استفاده

```bash
# از directory apps/backend
python -m app.db.seed
```

یا:

```bash
# از root directory پروژه
cd apps/backend
python -m app.db.seed
```

## داده‌های ایجاد شده

### Categories (4 عدد)
- اطلاعات عمومی
- خدمات و محصولات
- پشتیبانی فنی
- سوالات متداول

### QA Items (20 عدد)
- 5 سوال در "اطلاعات عمومی"
- 7 سوال در "خدمات و محصولات"
- 5 سوال در "پشتیبانی فنی"
- 4 سوال در "سوالات متداول"

### Website Source (1 عدد)
- URL: `https://example-demo-site.com`
- Status: **Disabled** (غیرفعال)
- برای تست و demo

## ویژگی‌ها

- ✅ **Idempotent**: می‌توانید چند بار اجرا کنید، داده‌های تکراری ایجاد نمی‌شود
- ✅ **Safe**: اگر داده‌ها قبلاً وجود داشته باشند، skip می‌شوند
- ✅ **Fast**: در کمتر از 2 ثانیه اجرا می‌شود

## مثال خروجی

```
🌱 Starting database seeding...

📁 Seeding categories...
✓ Created category: اطلاعات عمومی
✓ Created category: خدمات و محصولات
✓ Created category: پشتیبانی فنی
✓ Created category: سوالات متداول

❓ Seeding QA items...
  ✓ Created QA: ساعات کاری شما چیست؟...
  ✓ Created QA: آدرس دفتر مرکزی کجاست؟...
  ...

🌐 Seeding website source...
✓ Created fake website source: https://example-demo-site.com (disabled)

✅ Database seeding completed successfully!

📊 Summary:
   - Categories: 4
   - QA Items: 20
   - Website Sources: 1
```

## استفاده در Setup Scripts

می‌توانید seed را در setup scripts اضافه کنید:

```bash
# بعد از migration
alembic upgrade head
python -m app.db.seed
```

## نکات

- قبل از اجرای seed، مطمئن شوید که migration ها اجرا شده‌اند
- Seed script از database موجود استفاده می‌کند (از `.env` خوانده می‌شود)
- داده‌های seed برای demo و testing هستند



