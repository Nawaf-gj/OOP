"""
غلاف بسيط حول واجهة أودو XML-RPC.

يعتمد على المكتبة القياسية فقط (xmlrpc.client) — لا تبعيات خارجية.
يقرأ الإعدادات من متغيرات البيئة أو من ملف .env.

الاستخدام:
    from odoo_ccd import connect
    odoo = connect()
    partners = odoo.search_read("res.partner", [], ["name", "email"], limit=10)
"""
from __future__ import annotations

import os
import ssl
import xmlrpc.client
from pathlib import Path

# مسار حزمة شهادات البروكسي في بيئة Claude (إن وُجد)
_CA_BUNDLE = "/root/.ccr/ca-bundle.crt"


def _load_dotenv(path: str = ".env") -> None:
    """تحميل متغيرات .env إلى os.environ دون الكتابة فوق المضبوط مسبقاً."""
    p = Path(path)
    if not p.is_file():
        # جرّب بجانب جذر المشروع
        p = Path(__file__).resolve().parent.parent / ".env"
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


def _ssl_context() -> ssl.SSLContext:
    """سياق TLS يثق بحزمة البروكسي إن وُجدت، وإلا الافتراضي."""
    if os.path.exists(_CA_BUNDLE):
        return ssl.create_default_context(cafile=_CA_BUNDLE)
    return ssl.create_default_context()


class OdooError(RuntimeError):
    """خطأ عام في الاتصال أو العمليات مع أودو."""


class OdooClient:
    """عميل أودو عبر XML-RPC مع دوال CRUD مبسّطة."""

    def __init__(self, url: str, db: str, user: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.user = user
        self._password = password
        self._ctx = _ssl_context()
        self.uid: int | None = None
        self._common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", context=self._ctx
        )
        self._models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", context=self._ctx
        )

    # ── الاتصال ──
    def version(self) -> dict:
        """معلومات إصدار السيرفر (لا تحتاج مصادقة)."""
        try:
            return self._common.version()
        except Exception as e:  # noqa: BLE001
            raise OdooError(f"تعذّر الوصول للسيرفر {self.url}: {e}") from e

    def connect(self) -> int:
        """مصادقة وإرجاع uid. يرفع OdooError عند الفشل."""
        try:
            uid = self._common.authenticate(self.db, self.user, self._password, {})
        except Exception as e:  # noqa: BLE001
            raise OdooError(f"فشل الاتصال بالسيرفر: {e}") from e
        if not uid:
            raise OdooError(
                "فشلت المصادقة: تحقّق من ODOO_USER/ODOO_API_KEY واسم قاعدة البيانات "
                f"({self.db}). ملاحظة: اسم الدخول حسّاس لحالة الأحرف."
            )
        self.uid = uid
        return uid

    def _ensure(self) -> int:
        if self.uid is None:
            return self.connect()
        return self.uid

    # ── عمليات عامة ──
    def execute(self, model: str, method: str, *args, **kwargs):
        """استدعاء أي دالة على أي نموذج (execute_kw)."""
        uid = self._ensure()
        try:
            return self._models.execute_kw(
                self.db, uid, self._password, model, method, list(args), kwargs
            )
        except xmlrpc.client.Fault as e:
            raise OdooError(f"خطأ أودو في {model}.{method}: {e.faultString}") from e

    def search(self, model: str, domain=None, **kw) -> list[int]:
        return self.execute(model, "search", domain or [], **kw)

    def search_count(self, model: str, domain=None) -> int:
        return self.execute(model, "search_count", domain or [])

    def search_read(self, model, domain=None, fields=None, **kw) -> list[dict]:
        if fields is not None:
            kw["fields"] = fields
        return self.execute(model, "search_read", domain or [], **kw)

    def read(self, model, ids, fields=None) -> list[dict]:
        kw = {"fields": fields} if fields else {}
        return self.execute(model, "read", ids if isinstance(ids, list) else [ids], **kw)

    def create(self, model: str, values: dict) -> int:
        return self.execute(model, "create", values)

    def write(self, model: str, ids, values: dict) -> bool:
        return self.execute(model, "write", ids if isinstance(ids, list) else [ids], values)

    def unlink(self, model: str, ids) -> bool:
        return self.execute(model, "unlink", ids if isinstance(ids, list) else [ids])

    def fields_get(self, model: str, attributes=None) -> dict:
        attrs = attributes or ["string", "type", "required", "relation"]
        return self.execute(model, "fields_get", [], attributes=attrs)


def connect(env_file: str = ".env") -> OdooClient:
    """إنشاء عميل من إعدادات البيئة/.env والمصادقة فوراً."""
    _load_dotenv(env_file)
    url = os.environ.get("ODOO_URL")
    db = os.environ.get("ODOO_DB")
    user = os.environ.get("ODOO_USER")
    pwd = os.environ.get("ODOO_API_KEY") or os.environ.get("ODOO_PASSWORD")
    missing = [k for k, v in {"ODOO_URL": url, "ODOO_DB": db,
                              "ODOO_USER": user, "ODOO_API_KEY": pwd}.items() if not v]
    if missing:
        raise OdooError(
            "إعدادات ناقصة: " + ", ".join(missing) +
            ". انسخ .env.example إلى .env واملأ القيم."
        )
    client = OdooClient(url, db, user, pwd)
    client.connect()
    return client
