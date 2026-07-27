# أدوات سيرفر أودو CCD

أدوات للاتصال والعمل مع سيرفر أودو الخاص بـ **المطور المعتمد للمقاولات (CCD)** على `erp.ccd.sa` (Odoo 19).

## ما الذي يعمل من أين

| المهمة | الطريقة | تعمل من بيئة Claude؟ |
|---|---|---|
| قراءة/تصدير البيانات | XML-RPC عبر HTTPS | ✅ نعم |
| إنشاء/تحديث السجلات | XML-RPC عبر HTTPS | ✅ نعم |
| فحص حالة أودو (إصدار، بيانات) | XML-RPC عبر HTTPS | ✅ نعم |
| تطوير موديول مخصص | ملفات في `addons/` | ✅ يُبنى محلياً |
| نشر الموديول / سجلات النظام / systemctl | SSH | ❌ من جهازك فقط (SSH محجوب في بيئة Claude) |

## الإعداد

```bash
cp .env.example .env      # ثم املأ القيم
```

`.env` مستثنى من Git ولن يُرفع. **يُفضّل بشدة** استخدام API key بدل كلمة المرور:
داخل أودو → `Settings → Users → حسابك → Account Security → New API Key`، وضعه في `ODOO_API_KEY`.

## الاستخدام

```bash
# فحص الاتصال والحالة
python scripts/health_check.py

# تصدير نموذج إلى CSV
python scripts/export_data.py --model res.partner --limit 50
python scripts/export_data.py --model sale.order \
    --fields name,partner_id,amount_total,state \
    --domain '[["state","=","sale"]]' --out exports/sales.csv

# إنشاء/تحديث سجلات من CSV — معاينة أولاً (لا كتابة)
python scripts/upsert_records.py --model res.partner --file new.csv
# ثم التنفيذ الفعلي
python scripts/upsert_records.py --model res.partner --file new.csv --commit
```

### من كود Python

```python
from odoo_ccd import connect
odoo = connect()
partners = odoo.search_read("res.partner", [["is_company", "=", True]],
                            ["name", "phone", "email"], limit=20)
new_id = odoo.create("res.partner", {"name": "شركة جديدة"})
odoo.write("res.partner", new_id, {"phone": "0500000000"})
```

## مهام SSH (من جهازك المحلي)

```bash
bash scripts/ssh/service_status.sh          # حالة الخدمة والسجلات
bash scripts/ssh/deploy_module.sh ccd_custom # نشر وترقية الموديول
```

> عدّل المتغيرات داخل `deploy_module.sh` (مسار addons، اسم الخدمة) لتطابق سيرفرك.

## بنية المشروع

```
odoo_ccd/          مكتبة الاتصال (XML-RPC)
scripts/           أدوات: health_check, export_data, upsert_records
scripts/ssh/       سكربتات SSH (تُشغَّل من جهازك)
addons/ccd_custom/ هيكل الموديول المخصص (Odoo 19)
```

## ملاحظات أمنية

- لا تُحفظ بيانات الاعتماد في Git — تُقرأ من `.env` المستثنى.
- استخدم API key قابلاً للإلغاء بدل كلمة مرور الحساب الأساسي.
- بيانات SSH (root) للجهاز نفسه — احمِها بمفتاح SSH وعطّل الدخول بكلمة المرور.
