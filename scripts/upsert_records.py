#!/usr/bin/env python3
"""
إنشاء/تحديث سجلات أودو بشكل مجمّع من ملف CSV.

⚠️ يعمل بوضع المعاينة (--dry-run) افتراضياً: يعرض ما سيحدث دون أي كتابة.
   أضف --commit لتنفيذ التغييرات فعلياً على السيرفر.

CSV: صف العناوين = أسماء الحقول. لتحديث سجل موجود ضع عمود id.
     بدون عمود id (أو id فارغ) يُنشأ سجل جديد.

مثال:
    python scripts/upsert_records.py --model res.partner --file new.csv          # معاينة
    python scripts/upsert_records.py --model res.partner --file new.csv --commit  # تنفيذ
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from odoo_ccd import connect, OdooError  # noqa: E402


def coerce(val: str):
    """تحويل نص CSV إلى نوع مناسب: أرقام، منطقي، أو نص."""
    s = val.strip()
    if s == "":
        return False
    low = s.lower()
    if low in ("true", "صحيح"):
        return True
    if low in ("false", "خطأ"):
        return False
    # أرقام تبدأ بصفر (هواتف، أكواد) تبقى نصوصاً حتى لا يضيع الصفر البادئ
    if s.isdigit():
        return s if (len(s) > 1 and s[0] == "0") else int(s)
    try:
        return float(s)
    except ValueError:
        return s


def main() -> int:
    ap = argparse.ArgumentParser(description="إنشاء/تحديث سجلات أودو من CSV")
    ap.add_argument("--model", required=True)
    ap.add_argument("--file", required=True, help="ملف CSV المصدر")
    ap.add_argument("--commit", action="store_true",
                    help="تنفيذ فعلي (بدونه = معاينة فقط)")
    args = ap.parse_args()

    src = Path(args.file)
    if not src.is_file():
        print(f"❌ الملف غير موجود: {src}")
        return 1

    with src.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("الملف فارغ.")
        return 0

    try:
        odoo = connect()
    except OdooError as e:
        print(f"❌ {e}")
        return 1

    mode = "تنفيذ فعلي ⚠️" if args.commit else "معاينة (لا كتابة)"
    print(f"النموذج: {args.model} | عدد الصفوف: {len(rows)} | الوضع: {mode}\n")

    created = updated = failed = 0
    for i, raw in enumerate(rows, 1):
        vals = {k: coerce(v) for k, v in raw.items() if k and k != "id"}
        rec_id = raw.get("id", "").strip()
        try:
            if rec_id:  # تحديث
                if args.commit:
                    odoo.write(args.model, [int(rec_id)], vals)
                print(f"  [{i}] تحديث id={rec_id}: {vals}")
                updated += 1
            else:  # إنشاء
                if args.commit:
                    new_id = odoo.create(args.model, vals)
                    print(f"  [{i}] إنشاء -> id={new_id}: {vals}")
                else:
                    print(f"  [{i}] سيُنشأ: {vals}")
                created += 1
        except OdooError as e:
            print(f"  [{i}] ❌ فشل: {e}")
            failed += 1

    print(f"\nالنتيجة: إنشاء={created} تحديث={updated} فشل={failed}")
    if not args.commit:
        print("ℹ️  هذه معاينة فقط. أضف --commit للتنفيذ الفعلي.")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
