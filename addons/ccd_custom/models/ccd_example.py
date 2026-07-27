from odoo import fields, models


class CcdExample(models.Model):
    """نموذج تجريبي — استبدله/عدّله حسب متطلبات الموديول."""

    _name = "ccd.example"
    _description = "CCD Example"

    name = fields.Char(string="الاسم", required=True)
    note = fields.Text(string="ملاحظات")
    active = fields.Boolean(string="نشط", default=True)
