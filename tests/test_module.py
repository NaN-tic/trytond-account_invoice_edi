# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.account.tests import create_chart
from trytond.modules.company.tests import (
    CompanyTestMixin, create_company, set_company)
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class AccountInvoiceEdiTestCase(CompanyTestMixin, ModuleTestCase):
    'Test AccountInvoiceEdi module'
    module = 'account_invoice_edi'
    extras = ['sale', 'sale_edi_ediversa', 'sale_invoice_grouping_by_address']

    @with_transaction()
    def test_on_change_party_forces_edi(self):
        "Test on_change_party forces EDI for flagged parties"
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Party = pool.get('party.party')

        company = create_company()
        with set_company(company):
            create_chart(company, tax=True)
            party = Party(name='EDI Customer', force_edi_invoice=True)
            party.save()

            invoice = Invoice(company=company, type='out', party=party)
            invoice.on_change_party()

            self.assertTrue(invoice.is_edi)

    @with_transaction()
    def test_set_edi_defaults_from_party_uses_sale_reference(self):
        "Test flagged parties copy sale reference into invoice"
        pool = Pool()
        Invoice = pool.get('account.invoice')
        InvoiceLine = pool.get('account.invoice.line')
        Party = pool.get('party.party')
        Sale = pool.get('sale.sale')
        SaleLine = pool.get('sale.line')

        party = Party(name='EDI Customer', force_edi_invoice=True)
        sale = Sale(reference='SALE-REF')
        sale_line = SaleLine(sale=sale)
        invoice_line = InvoiceLine(origin=sale_line)
        invoice = Invoice(
            type='out',
            party=party,
            lines=[invoice_line],
            reference=None)

        invoice.set_edi_defaults_from_party()

        self.assertTrue(invoice.is_edi)
        self.assertEqual(invoice.reference, 'SALE-REF')


del ModuleTestCase
