#!/usr/bin/env python3
"""فحص حالة سيرفر أودو CCD: الوصول، الإصدار، المصادقة، ونظرة على البيانات."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from odoo_ccd import connect, OdooError  # noqa: E402

MODELS = [
    ("res.partner", "جهات الاتصال"),
    ("res.users", "المستخدمون"),
    ("sale.order", "أوامر البيع"),
    ("purchase.order", "أوامر الشراء"),
    ("account.move", "القيود والفواتير"),
    ("product.template", "المنتجات"),
    ("stock.picking", "عمليات المخزون"),
    ("project.project", "المشاريع"),
    ("hr.employee", "الموظفون"),
]


def main() -> int:
    print("── فحص حالة سيرفر أودو CCD ──\n")
    t0 = time.time()
    try:
        odoo = connect()
    except OdooError as e:
        print(f"❌ فشل: {e}")
        return 1
    dt = (time.time() - t0) * 1000

    v = odoo.version()
    print(f"✅ الاتصال والمصادقة ناجحان  (زمن الاستجابة {dt:.0f}ms)")
    print(f"   السيرفر : {odoo.url}")
    print(f"   الإصدار : Odoo {v.get('server_version')}")
    print(f"   قاعدة البيانات: {odoo.db}")
    print(f"   المستخدم: uid={odoo.uid}\n")

    print("── عدد السجلات في النماذج الأساسية ──")
    for model, label in MODELS:
        try:
            n = odoo.search_count(model)
            print(f"   {label:20} ({model:20}): {n}")
        except OdooError:
            print(f"   {label:20} ({model:20}): غير مثبّت")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
