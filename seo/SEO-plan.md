# برنامه عملیاتی SEO (اودسان کافی) — اولویت‌بندی شده و آماده اجرا

این برنامه برای وب‌سایت فروشگاه قهوه (Django، HTML، CSS — زبان فارسی راست‌به‌چپ) تدوین شده است و شامل اقدامات کوتاه‌مدت، میان‌مدت و بلندمدت همراه با هدف، تاثیر، سختی، و مسیر دقیق فایل‌ها/قالب‌های مورد ویرایش است.

## اهداف کلیدی
- افزایش رتبه برای کلمات «دانه»، «قهوه»، «خرید دانه قهوه» و تمام نام‌های دسته/محصول
- بهبود CTR با متاتایتل/متادیسکریپشن بهینه
- رفع مشکلات فنی سئو (canonical، hreflang، sitemap، robots)
- افزودن اسکیما (Product, LocalBusiness/CafeOrCoffeeShop) و بهبود Core Web Vitals
- توسعه محتوای هدفمند و لینک‌سازی داخلی

---

## فاز کوتاه‌مدت (۱–۲ هفته)

1) الگوهای متاتایتل/متادیسکریپشن (خانه، دسته، محصول)
- هدف: افزایش CTR و پوشش کلمات کلیدی اصلی و بلند.
- تاثیر: بالا
- سختی: آسان
- فایل‌ها/قالب‌ها: `shop/templates/shop/base.html`, `shop/templates/shop/home.html`, `shop/templates/shop/category_detail.html`, `shop/templates/shop/product_detail.html`

2) ساختار تیترها (H1/H2/H3) و جایگاه‌های محتوایی
- هدف: بهبود درک موتور جستجو و آماده‌سازی برای محتوا.
- تاثیر: متوسط تا بالا
- سختی: آسان
- فایل‌ها/قالب‌ها: همان فایل‌های فوق + ایجاد طرح محتوایی در: `/seo/content-outlines/`

3) ایجاد لیست گسترده کلمات کلیدی فارسی (۶۰–۱۰۰ عبارت) + گروه‌بندی نیت
- هدف: تغذیه استراتژی محتوا و متاها.
- تاثیر: متوسط
- سختی: آسان
- فایل‌ها: `/seo/keywords-persian.csv`, `/seo/keywords-persian.md`

4) تنظیم canonical و hreflang سمت سرور با context processor
- هدف: جلوگیری از محتوای تکراری و سیگنال‌دهی زبان/منطقه.
- تاثیر: بالا
- سختی: متوسط
- فایل‌ها/قالب‌ها: `shop/context_processors.py` (جدید)، `coffe_shop/settings.py` (افزودن CP)، `shop/templates/shop/base.html` (تگ‌های `<link rel="canonical">` و `alternate`)

5) به‌روزرسانی robots.txt و تکمیل sitemap.xml
- هدف: خزش صحیح و ایندکس بهتر.
- تاثیر: بالا
- سختی: آسان
- فایل‌ها: `coffe_shop/urls.py` (robots.txt)، `shop/sitemaps.py` (تایید و بهبود)

6) اسکیما Product برای صفحه محصول + LocalBusiness/CafeOrCoffeeShop سراسری
- هدف: ریچ‌نتایج، ستاره‌ها و نمایش قیمت/موجودی.
- تاثیر: بالا
- سختی: متوسط
- فایل‌ها/قالب‌ها: `shop/templates/shop/product_detail.html` (JSON-LD Product)، `shop/templates/shop/base.html` (JSON-LD LocalBusiness/CafeOrCoffeeShop — با TODO اطلاعات کسب‌وکار)

7) Lazy-loading و srcset برای تصاویر کلیدی
- هدف: بهبود LCP و CLS و سرعت.
- تاثیر: متوسط تا بالا
- سختی: آسان تا متوسط
- فایل‌ها/قالب‌ها: `shop/templates/shop/home.html`, `shop/templates/shop/category_detail.html`, `shop/templates/shop/product_detail.html`, `shop/templates/shop/product_list.html`

8) ریدایرکت 301 از مسیرهای ID به مسیرهای slug (محصول/دسته)
- هدف: تثبیت آدرس canonical و حذف نسخه‌های تکراری.
- تاثیر: بالا
- سختی: متوسط
- فایل‌ها: `shop/views.py` (ریدایرکت دائمی)، (PR جدا با برچسب «requires manual review»)

---

## فاز میان‌مدت (۳–۶ هفته)

9) برنامه محتوایی و لینک‌سازی داخلی (۱۲ عنوان بلاگ + بریف)
- هدف: جذب ترافیک ارگانیک اطلاعاتی/تجاری و تقویت صفحات پول‌ساز.
- تاثیر: بالا
- سختی: متوسط
- فایل‌ها: `/seo/content-plan.md`, `/content/blog/` (۲ پیش‌نویس با front-matter)

10) بهبود Core Web Vitals و بهینه‌سازی امن سمت فرانت
- هدف: بهبود امتیاز PageSpeed و تجربه کاربری.
- تاثیر: متوسط تا بالا
- سختی: متوسط
- فایل‌ها: `/seo/performance.md`, اصلاحات سبک و اسکریپت در `shop/templates/shop/base.html` و صفحات سنگین (با احتیاط)

11) داشبورد مانیتورینگ SEO (GSC/GA4)
- هدف: پایش KPIها و کشف فرصت‌ها.
- تاثیر: متوسط
- سختی: آسان
- فایل‌ها: `/seo/monitoring.md`

---

## فاز بلندمدت (۷–۱۲ هفته)

12) توسعه اسکیما و سایتمپ‌های تخصصی (Image/News/FAQ)
- هدف: پوشش سناریوهای ریچ‌ریزلت و ایندکس بهتر تصاویر.
- تاثیر: متوسط
- سختی: متوسط تا سخت
- فایل‌ها: `shop/sitemaps.py` توسعه، الگوهای مرتبط

13) بین‌المللی‌سازی احتمالی و hreflang چندزبانه
- هدف: آمادگی برای نسخه‌های زبان/منطقه دیگر.
- تاثیر: وابسته به استراتژی
- سختی: متوسط
- فایل‌ها: context processor و الگوها

14) بهینه‌سازی معماری لینک داخلی در مقیاس
- هدف: انتقال PageRank داخلی به صفحات پول‌ساز.
- تاثیر: بالا
- سختی: متوسط
- فایل‌ها: الگوهای لیست و جزئیات محصول/دسته + صفحات محتوا

---

## نکات عملیاتی
- تمام تغییرات کد در شاخه‌های `seo/{short-task-name}` با کامیت‌های واضح انجام می‌شود.
- برای موارد با ریسک عملیاتی (ریدایرکت‌ها/تنظیمات سرور) PR جدا با برچسب «requires manual review» باز می‌شود.
- هر جا به مقادیر خصوصی/واقعی نیاز باشد (قیمت دقیق، SKU، آدرس، مختصات، ساعات کاری)، در کد `TODO` گذاشته می‌شود و در توضیح PR هم درج می‌گردد.

---

## نقشه فایل‌ها برای اجرا
- الگوها: `shop/templates/shop/base.html`, `home.html`, `category_detail.html`, `product_detail.html`, `product_list.html`
- ویوها: `shop/views.py`
- تنظیمات: `coffe_shop/settings.py`
- URLها: `coffe_shop/urls.py`, `shop/urls.py`
- سایت‌مپ: `shop/sitemaps.py`
- CP جدید: `shop/context_processors.py`
- مستندات/تحویل‌ها: `/seo/*.md`, `/seo/content-outlines/*`, `/content/blog/*`

