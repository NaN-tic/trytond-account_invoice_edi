# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta


class Company(metaclass=PoolMeta):
    __name__ = 'company.company'

    trade_register = fields.Char("Trade Register",
        help="This field is needed for EDI invoices. You have to write the "
        "information of the Trade Register (e.g.: RM Barcelona Tomo XXX, "
        "Folio XX, Hoja XX)")

    @classmethod
    def default_cancel_invoice_out(cls):
        return False
