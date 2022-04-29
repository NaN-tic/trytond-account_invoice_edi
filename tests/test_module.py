
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase


class AccountInvoiceEdiTestCase(CompanyTestMixin, ModuleTestCase):
    'Test AccountInvoiceEdi module'
    module = 'account_invoice_edi'
    extras = ['sale', 'sale_edi_ediversa', 'sale_invoice_grouping_by_address']


del ModuleTestCase
