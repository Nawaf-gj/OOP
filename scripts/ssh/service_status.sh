#!/usr/bin/env bash
# فحص حالة خدمة أودو وقراءة سجلاتها عبر SSH.
#
# ⚠️ يُشغَّل من جهازك المحلي — لا يعمل من بيئة Claude السحابية (SSH محجوب هناك).
#
# الاستخدام:  bash scripts/ssh/service_status.sh
# اقرأ الإعدادات من .env (SSH_HOST, SSH_USER).

set -euo pipefail
cd "$(dirname "$0")/../.."
[ -f .env ] && set -a && . ./.env && set +a

SSH_HOST="${SSH_HOST:?ضع SSH_HOST في .env}"
SSH_USER="${SSH_USER:-root}"

echo "── الاتصال بـ ${SSH_USER}@${SSH_HOST} ──"
ssh "${SSH_USER}@${SSH_HOST}" bash -s <<'REMOTE'
  echo "── حالة خدمة أودو ──"
  systemctl status odoo --no-pager 2>/dev/null | head -15 \
    || systemctl status odoo19 --no-pager 2>/dev/null | head -15 \
    || echo "لم يُعثر على خدمة باسم odoo / odoo19 — جرّب: systemctl list-units | grep -i odoo"
  echo
  echo "── آخر 30 سطراً من سجل أودو ──"
  journalctl -u odoo --no-pager -n 30 2>/dev/null \
    || tail -n 30 /var/log/odoo/odoo-server.log 2>/dev/null \
    || echo "لم يُعثر على سجل — تحقّق من مسار log في odoo.conf"
  echo
  echo "── حالة PostgreSQL ──"
  systemctl is-active postgresql 2>/dev/null || echo "postgresql غير معروف"
REMOTE
