#!/usr/bin/env python3
"""
إصلاح خطأ أودو 19: "Missing 'card' template" في عروض kanban قديمة.

السبب: أودو 18/19 يتطلب أن يُسمّى قالب الـ kanban بـ 'card' بدل الأسماء
القديمة 'kanban-box' / 'kanban-card'. الموديولات غير المُرقّاة تُبقي الاسم
القديم فيفشل عرض الـ kanban.

هذا السكربت يعدّل arch_db مباشرة عبر XML-RPC (يعمل فوراً دون SSH).
⚠️ يعمل بوضع المعاينة افتراضياً — أضف --commit للتطبيق الفعلي.
   --restore يعيد النسخ الأصلية من مجلد backup.

الاستخدام:
    python scripts/fix_kanban_card.py            # معاينة
    python scripts/fix_kanban_card.py --commit   # تطبيق
    python scripts/fix_kanban_card.py --restore --commit  # تراجع
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from odoo_ccd import connect, OdooError  # noqa: E402

BACKUP = Path(__file__).resolve().parent.parent / "migrations/kanban_card_fix/backup"

# العروض المتأثّرة (id ثابت في هذه القاعدة)
VIEW_IDS = [3238, 3243, 3256, 3981]

# إصلاح ثانوي: res.users.image_small محذوف منذ أودو 13 — استبدله بالودجت الحديث
IMG_OLD = re.compile(
    r'<img[^>]*kanban_image\(\s*[\'"]res\.users[\'"][^>]*/>', re.DOTALL
)
IMG_NEW = '<field name="user_id" widget="many2one_avatar_user"/>'


def migrate(arch: str) -> str:
    """تحويل arch إلى صيغة أودو 19: تسمية القالب card + إصلاحات معروفة."""
    new = arch.replace('t-name="kanban-box"', 't-name="card"')
    new = new.replace('t-name="kanban-card"', 't-name="card"')
    new = new.replace("t-name='kanban-box'", "t-name='card'")
    new = new.replace("t-name='kanban-card'", "t-name='card'")
    new = IMG_OLD.sub(IMG_NEW, new)
    return new


def restore(odoo, commit: bool) -> int:
    idx = BACKUP / "_index.json"
    if not idx.is_file():
        print("❌ لا توجد نسخ احتياطية في", BACKUP)
        return 1
    import json
    for meta in json.loads(idx.read_text(encoding="utf-8")):
        vid = meta["id"]
        f = BACKUP / f"{vid}_{meta['model'].replace('.', '_')}.xml"
        arch = f.read_text(encoding="utf-8")
        print(f"استعادة id={vid} ({meta['model']}) من {f.name}")
        if commit:
            odoo.write("ir.ui.view", vid, {"arch_db": arch})
    print("✅ تمّت الاستعادة." if commit else "ℹ️ معاينة — أضف --commit.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="إصلاح Missing 'card' template")
    ap.add_argument("--commit", action="store_true", help="تطبيق فعلي")
    ap.add_argument("--restore", action="store_true", help="استعادة النسخ الأصلية")
    args = ap.parse_args()

    try:
        odoo = connect()
    except OdooError as e:
        print(f"❌ {e}")
        return 1

    if args.restore:
        return restore(odoo, args.commit)

    rows = odoo.read("ir.ui.view", VIEW_IDS, ["id", "model", "xml_id", "arch_db"])
    changed = 0
    for r in rows:
        old = r["arch_db"]
        new = migrate(old)
        if new == old:
            print(f"  id={r['id']} ({r['model']}): لا تغيير مطلوب")
            continue
        changed += 1
        has_card = 't-name="card"' in new
        print(f"  id={r['id']} ({r['model']}): سيُصلَح  "
              f"[card={'✓' if has_card else '✗'}]")
        if args.commit:
            try:
                odoo.write("ir.ui.view", r["id"], {"arch_db": new})
                print(f"     ✅ طُبّق على id={r['id']}")
            except OdooError as e:
                print(f"     ❌ فشل id={r['id']}: {e}")

    print(f"\nالمجموع: {changed} عرض بحاجة إصلاح.")
    if not args.commit:
        print("ℹ️ هذه معاينة. أضف --commit للتطبيق الفعلي على السيرفر.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
