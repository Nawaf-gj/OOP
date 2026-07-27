#!/usr/bin/env bash
# نشر موديول أودو مخصص إلى السيرفر وترقيته.
#
# ⚠️ يُشغَّل من جهازك المحلي — لا يعمل من بيئة Claude السحابية (SSH محجوب هناك).
# ⚠️ عدّل المتغيرات أدناه لتطابق إعداد سيرفرك (مسار addons، اسم الخدمة، قاعدة البيانات).
#
# الاستخدام:  bash scripts/ssh/deploy_module.sh ccd_custom

set -euo pipefail
cd "$(dirname "$0")/../.."
[ -f .env ] && set -a && . ./.env && set +a

MODULE="${1:-ccd_custom}"
SSH_HOST="${SSH_HOST:?ضع SSH_HOST في .env}"
SSH_USER="${SSH_USER:-root}"

# ── عدّل هذه لتطابق سيرفرك ──
REMOTE_ADDONS="/mnt/extra-addons"   # مسار مجلد addons على السيرفر
ODOO_SERVICE="odoo"                 # اسم خدمة systemd
ODOO_DB="${ODOO_DB:-ccd_erp}"

LOCAL_MODULE="addons/${MODULE}"
[ -d "$LOCAL_MODULE" ] || { echo "❌ الموديول غير موجود محلياً: $LOCAL_MODULE"; exit 1; }

echo "── نسخ ${MODULE} إلى ${SSH_USER}@${SSH_HOST}:${REMOTE_ADDONS} ──"
rsync -avz --delete "${LOCAL_MODULE}/" \
  "${SSH_USER}@${SSH_HOST}:${REMOTE_ADDONS}/${MODULE}/"

echo "── ترقية الموديول وإعادة تشغيل الخدمة ──"
ssh "${SSH_USER}@${SSH_HOST}" bash -s <<REMOTE
  set -e
  systemctl stop ${ODOO_SERVICE}
  su - odoo -c "odoo -d ${ODOO_DB} -u ${MODULE} --stop-after-init" 2>/dev/null \
    || odoo -d ${ODOO_DB} -u ${MODULE} --stop-after-init 2>/dev/null \
    || echo "⚠️ تعذّرت الترقية بالأمر المباشر — رقّ الموديول من واجهة أودو (Apps → Update Apps List)."
  systemctl start ${ODOO_SERVICE}
  systemctl is-active ${ODOO_SERVICE}
REMOTE
echo "✅ تم النشر."
