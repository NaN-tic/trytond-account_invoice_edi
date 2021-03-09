# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.account_invoice_edi.tests.test_account_invoice_edi import suite
except ImportError:
    from .test_account_invoice_edi import suite

__all__ = ['suite']
