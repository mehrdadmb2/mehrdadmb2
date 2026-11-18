# راهنمای نصب نسخهٔ جدید پروفایل GitHub

این بسته، بازطراحی ریپوی پروفایل `mehrdadmb2/mehrdadmb2` است. فایل‌های پروژه‌های ArzPulse، PySmartHome-PC و IMDb Showcase را تغییر نمی‌دهد؛ فقط داده‌های عمومی آن‌ها را می‌خواند.

## روش پیشنهادی با PowerShell

1. از ریپوی `mehrdadmb2/mehrdadmb2` یک Clone محلی بگیر یا آخرین نسخهٔ آن را Pull کن.
2. ZIP جدید را در یک پوشهٔ جداگانه Extract کن.
3. PowerShell را در پوشهٔ Extract‌شده باز کن.
4. دستور زیر را با مسیر Clone خودت اجرا کن:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\APPLY-REFRESH.ps1 -RepoPath "C:\Users\YOUR_USER\source\mehrdadmb2"
```

اسکریپت قبل از جایگزینی، از فایل‌های هم‌نام نسخهٔ فعلی در پوشهٔ `.profile-refresh-backup` نسخهٔ پشتیبان می‌سازد. برای غیرفعال کردن پشتیبان‌گیری، پارامتر `-NoBackup` را اضافه کن.

## روش دستی

محتویات پوشهٔ بسته را با حفظ ساختار پوشه‌ها روی Clone خودت کپی کن و فایل‌های هم‌نام را جایگزین کن. پوشه‌های موجود `assets/qr`، فایل‌های `metrics*.svg`، فایل‌های snake، workflowهای Metrics/Snake/Blog و سایر تنظیمات فعلی حفظ می‌شوند.

## اعتبارسنجی و انتشار

از ریشهٔ Clone اجرا کن:

```powershell
python scripts/check_profile.py
python -m unittest discover -s tests -v
git status --short
git diff --check
git add -A
git commit -m "feat(profile): redesign README and add live project panels"
git push origin main
```

سپس به تب **Actions** در GitHub برو و این دو workflow را دستی اجرا کن:

- `Live Profile Data` برای دریافت قیمت طلا/تتر و اطلاعات سنسورها.
- `Featured Movie Posters` برای نمایش پوسترهای مجموعهٔ IMDb.

برای آمار Metrics، مثل قبل secret به نام `METRICS_TOKEN` لازم است. برای دو workflow جدید هیچ توکن یا Secret اضافه‌ای لازم نیست؛ فقط در `Settings → Actions → General → Workflow permissions` اجازهٔ نوشتن محتوا (`contents: write`) فعال باشد.

## نحوهٔ کار داده‌های زنده

- دادهٔ طلا و تتر از `ArzPulse/docs/data/latest.json` خوانده می‌شود و از ریال به تومان تبدیل می‌شود.
- دما و رطوبت از `PySmartHome-PC/data/status.json` خوانده می‌شود.
- قیمت/سنسور قدیمی با برچسب `STALE` مشخص می‌شود؛ مقدار قدیمی به‌عنوان دادهٔ تازه نمایش داده نمی‌شود.
- هر ۱۰ دقیقه تلاش برای تازه‌سازی داشبورد انجام می‌شود؛ زمان‌بندی GitHub Actions تضمین لحظه‌ای بودن ندارد.
- پوسترها از cache عمومی `imdb-showcase/docs/posters/` دریافت می‌شوند و هر ۱۲ ساعت نوسازی می‌شوند.
