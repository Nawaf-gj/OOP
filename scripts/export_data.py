#!/usr/bin/env python3
"""
تصدير أي نموذج من أودو إلى CSV.

أمثلة:
    python scripts/export_data.py --model res.partner --limit 50
    python scripts/export_data.py --model sale.order \
        --fields name,partner_id,am_total,state \
        --domain '[["state","=","sale"]]' --out exports/sales.csv
"""
import argparse
import ast
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from odoo_ccd import connect, OdooError  # noqa: E402


def flatten(value):
    """تحويل قيمة أودو إلى نص مناسب لـ CSV (many2one تصبح الاسم)."""
    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], int):
        return value[1]  # many2one -> [id, name]
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    if value is False:
        return ""
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description="تصدير نموذج أودو إلى CSV")
    ap.add_argument("--model", required=True, help="اسم النموذج، مثل res.partner")
    ap.add_argument("--fields", help="حقول مفصولة بفواصل (افتراضياً كل الحقول المعروضة)")
    ap.add_argument("--domain", default="[]", help='فلتر أودو بصيغة JSON، مثل [["state","=","sale"]]')
    ap.add_argument("--limit", type=int, default=0, help="حد أقصى للسجلات (0 = بلا حد)")
    ap.add_argument("--out", help="ملف الإخراج (افتراضياً exports/<model>.csv)")
    args = ap.parse_args()

    try:
        domain = ast.literal_eval(args.domain)
    except (ValueError, SyntaxError) as e:
        print(f"❌ صيغة --domain غير صحيحة: {e}")
        return 1

    try:
        odoo = connect()
    except OdooError as e:
        print(f"❌ {e}")
        return 1

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else None
    kw = {}
    if fields:
        kw["fields"] = fields
    if args.limit:
        kw["limit"] = args.limit

    try:
        rows = odoo.search_read(args.model, domain, **kw)
    except OdooError as e:
        print(f"❌ {e}")
        return 1

    if not rows:
        print("لا توجد سجلات مطابقة.")
        return 0

    cols = fields or sorted({k for r in rows for k in r})
    out = Path(args.out or f"exports/{args.model.replace('.', '_')}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: flatten(r.get(c)) for c in cols})

    print(f"✅ صُدّر {len(rows)} سجل إلى {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
