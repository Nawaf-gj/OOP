"""أدوات الاتصال بسيرفر أودو CCD (erp.ccd.sa)."""
from .client import OdooClient, OdooError, connect

__all__ = ["OdooClient", "OdooError", "connect"]
