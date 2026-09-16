# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Template

from trytond.exceptions import UserError
from trytond.modules.account.tests import create_chart
from trytond.modules.company.tests import (
    CompanyTestMixin, create_company, set_company)
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


MODULE_PATH = Path(__file__).parent.parent


class AccountInvoiceEdiTestCase(CompanyTestMixin, ModuleTestCase):
    'Test AccountInvoiceEdi module'
    module = 'account_invoice_edi'
    extras = ['sale', 'sale_edi_ediversa', 'sale_invoice_grouping_by_address']

    @staticmethod
    def _create_product(name, ean=None):
        pool = Pool()
        Identifier = pool.get('product.identifier')
        Product = pool.get('product.product')
        Template = pool.get('product.template')
        Uom = pool.get('product.uom')

        unit, = Uom.search([('name', '=', 'Unit')])
        template = Template(
            name=name, default_uom=unit, type='service',
            list_price=Decimal(0))
        template.save()
        product = Product(template=template)
        product.save()
        if ean:
            Identifier(product=product, type='ean', code=ean).save()
        return Product(product.id), unit

    @staticmethod
    def _create_invoice_line(invoice, product, unit, quantity, unit_price,
            tax=None):
        InvoiceLine = Pool().get('account.invoice.line')
        line = InvoiceLine(
            invoice=invoice,
            type='line',
            company=invoice.company,
            currency=invoice.currency,
            product=product,
            unit=unit,
            quantity=Decimal(quantity),
            unit_price=Decimal(unit_price),
            taxes=[tax] if tax else [])
        line.amount = line.on_change_with_amount()
        line.code_ean13 = line.get_code_ean13(None)
        line.is_edi = False
        line.stock_moves = []
        return line

    @staticmethod
    def _render_template(name, invoice):
        with (MODULE_PATH / name).open() as template_file:
            return Template(template_file.read()).render({'invoice': invoice})

    @staticmethod
    def _template_invoice():
        discount_line = SimpleNamespace(
            product=SimpleNamespace(name='Fixed discount'))
        line = SimpleNamespace(
            code_ean13='4006381333931',
            product=SimpleNamespace(code='MAIN', name='Main product'),
            quantity=Decimal('2'),
            unit_price=Decimal('50.00'),
            base_price=None,
            origin=None,
            shipments_reference=[],
            discount_rate=None,
            discount_amount=None,
            edi_aldi_supplier_code='MAIN',
            edi_aldi_purchaser_code='BUYER-MAIN',
            edi_aldi_consumer_quantity=None,
            edi_aldi_order_line_number='1',
            edi_uom_code='PCE')
        line_tax = {
            'rate': Decimal('0.20'),
            'base': Decimal('100.00'),
            'amount': Decimal('20.00'),
            'discount_amount': Decimal('0.00'),
            'absolute_discount_amount': Decimal('0.00'),
            }
        summary_tax = {
            'rate': Decimal('0.20'),
            'base': Decimal('90.00'),
            'amount': Decimal('18.00'),
            'discount_amount': Decimal('-10.00'),
            'absolute_discount_amount': Decimal('10.00'),
            }
        edi_line = {
            'line': line,
            'amount': Decimal('100.00'),
            'taxes': [line_tax],
            }
        discount = {
            'line': discount_line,
            'amount': Decimal('-10.00'),
            'absolute_amount': Decimal('10.00'),
            }
        edi_data = {
            'lines': [edi_line],
            'global_discounts': [discount],
            'line_count': 1,
            'shipments_reference': [],
            'untaxed_amount': Decimal('90.00'),
            'base_amount': Decimal('90.00'),
            'discount_amount': Decimal('-10.00'),
            'absolute_discount_amount': Decimal('10.00'),
            'tax_amount': Decimal('18.00'),
            'total_amount': Decimal('108.00'),
            'taxes': [summary_tax],
            }
        return SimpleNamespace(
            number='INV-1', id=1, edi_document_type='380',
            invoice_date='2026-09-15', edi_delivery_date='2026-09-15',
            edi_due_date=None, edi_data=edi_data, sales=[], shipments=[],
            reference='', edi_nadsco='', edi_nadbco='', edi_nadsu='',
            edi_nadby='', edi_nadii='', edi_nadiv='', edi_naddp='',
            edi_nadpr='', edi_nadpe='', edi_aldi_nadsu='', edi_aldi_nadby='',
            edi_aldi_nadiv='', edi_aldi_naddp='', edi_fii_su_account='')

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

            invoice = Invoice(
                company=company, type='out', party=party, reference=None)
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

    @with_transaction()
    def test_edi_data_groups_discount_and_excludes_no_edi_product(self):
        "Test EDI data handles global discounts and excluded products"
        pool = Pool()
        Configuration = pool.get('invoice.edi.configuration')
        Invoice = pool.get('account.invoice')
        Tax = pool.get('account.tax')

        company = create_company()
        with set_company(company):
            create_chart(company, tax=True)
            tax, = Tax.search([
                    ('name', '=', '20% VAT'),
                    ('company', '=', company.id),
                    ])
            main_product, unit = self._create_product(
                'Main product', '4006381333931')
            discount_product, _ = self._create_product('Fixed discount')
            no_edi_product, _ = self._create_product(
                'No EDI product', '5901234123457')

            configuration = Configuration(1)
            configuration.discount_products = [discount_product]
            configuration.no_edi_products = [
                discount_product, no_edi_product]
            configuration.save()

            invoice = Invoice(
                type='out', company=company, currency=company.currency,
                is_edi=True, total_amount=Decimal('102.00'))
            discount_line = self._create_invoice_line(
                invoice, discount_product, unit, '1', '-10.00', tax)
            main_line = self._create_invoice_line(
                invoice, main_product, unit, '2', '50.00', tax)
            trailing_discount_line = self._create_invoice_line(
                invoice, discount_product, unit, '1', '-5.00', tax)
            no_edi_line = self._create_invoice_line(
                invoice, no_edi_product, unit, '1', '25.00', tax)
            invoice.lines = [
                discount_line, main_line, trailing_discount_line,
                no_edi_line]

            edi = invoice.edi_data

            self.assertEqual(len(edi['lines']), 1)
            self.assertEqual(edi['lines'][0]['line'], main_line)
            self.assertEqual(
                edi['global_discounts'][0]['line'], discount_line)
            self.assertEqual(
                edi['global_discounts'][1]['line'],
                trailing_discount_line)
            self.assertEqual(edi['lines'][0]['amount'], Decimal('100.00'))
            self.assertEqual(edi['untaxed_amount'], Decimal('85.00'))
            self.assertEqual(edi['tax_amount'], Decimal('17.00'))
            self.assertEqual(edi['total_amount'], Decimal('102.00'))
            self.assertEqual(edi['taxes'][0]['base'], Decimal('85.00'))
            self.assertEqual(
                edi['taxes'][0]['discount_amount'], Decimal('-15.00'))

    @with_transaction()
    def test_edi_discount_validation_and_origin(self):
        "Test discount validation, orphan handling and EDI sale precedence"
        pool = Pool()
        Configuration = pool.get('invoice.edi.configuration')
        EdiSale = pool.get('edi.sale')
        Invoice = pool.get('account.invoice')
        Sale = pool.get('sale.sale')
        SaleLine = pool.get('sale.line')

        company = create_company()
        with set_company(company):
            create_chart(company)
            product, unit = self._create_product('Discount product')
            configuration = Configuration(1)
            configuration.discount_products = [product]
            configuration.no_edi_products = [product]
            configuration.save()

            invoice = Invoice(
                type='out', company=company, currency=company.currency,
                is_edi=True, total_amount=Decimal('10.00'))
            line = self._create_invoice_line(
                invoice, product, unit, '1', '10.00')
            invoice.lines = [line]
            with self.assertRaises(UserError):
                invoice.edi_data

            line.unit_price = Decimal('0.00')
            with self.assertRaises(UserError):
                invoice.edi_data

            line.unit_price = Decimal('-10.00')
            line.amount = line.on_change_with_amount()
            edi = invoice.edi_data
            self.assertEqual(edi['lines'], [])
            self.assertEqual(
                edi['global_discounts'][0]['amount'], Decimal('-10.00'))

            main_product, _ = self._create_product(
                'Main credit product', '4006381333931')
            main_line = self._create_invoice_line(
                invoice, main_product, unit, '-1', '100.00')
            line.unit_price = Decimal('10.00')
            line.amount = line.on_change_with_amount()
            invoice.total_amount = Decimal('-90.00')
            invoice.lines = [main_line, line]
            edi = invoice.edi_data
            self.assertEqual(edi['lines'][0]['amount'], Decimal('-100.00'))
            self.assertEqual(
                edi['global_discounts'][0]['amount'], Decimal('10.00'))
            self.assertEqual(edi['untaxed_amount'], Decimal('-90.00'))

            line.unit_price = Decimal('10.00')
            line.origin = SaleLine(sale=Sale(origin=EdiSale()))
            invoice.lines = [line]
            edi = invoice.edi_data
            self.assertTrue(line.has_edi_sale_origin)
            self.assertEqual(len(edi['lines']), 1)
            self.assertEqual(edi['global_discounts'], [])

    def test_d93a_global_discount_segments(self):
        "Test D93A global discount and summary segment positions"
        result = self._render_template(
            'invoice_out_edi_template.jinja2', self._template_invoice())
        records = result.splitlines()

        lin_index = next(i for i, value in enumerate(records)
            if value.startswith('LIN|'))
        alc_index = next(i for i, value in enumerate(records)
            if value.startswith('ALC|'))
        self.assertLess(alc_index, lin_index)
        self.assertEqual(
            records[alc_index].split('|'),
            ['ALC', 'A', '1', 'TD', '', '10.00'])
        self.assertFalse(any(value.startswith('ALCLIN|') for value in records))
        self.assertIn('MOALIN|100.00', records)
        self.assertIn('CNTRES|2|1', records)
        self.assertIn('MOARES|90.00||90.00|108.00|18.00|10.00', records)
        self.assertIn('TAXRES|VAT|20.00|18.00|90.00', records)

    def test_aldi_global_discount_segments(self):
        "Test ALDI global discount and summary segment positions"
        result = self._render_template(
            'invoice_out_edi_template_aldi.jinja2',
            self._template_invoice())
        records = result.splitlines()

        alc = next(value for value in records
            if value.startswith('ALC|'))
        fields = alc.split('|')
        self.assertEqual(len(fields), 8)
        self.assertEqual(fields[1:4], ['A', '1', 'TD'])
        self.assertEqual(fields[6], '10.00')
        self.assertEqual(fields[7], 'Fixed discount')
        self.assertFalse(any(value.startswith('ALCLIN|') for value in records))

        moalin = next(value for value in records
            if value.startswith('MOALIN|')).split('|')
        self.assertEqual(moalin, ['MOALIN', '', '', '100.00'])

        moares = next(value for value in records
            if value.startswith('MOARES|')).split('|')
        self.assertEqual(moares[1], '90.00')
        self.assertEqual(moares[4], '10.00')
        self.assertEqual(moares[5], '90.00')
        self.assertEqual(moares[6], '18.00')
        self.assertEqual(moares[10], '108.00')

        taxres = next(value for value in records
            if value.startswith('TAXRES|')).split('|')
        self.assertEqual(len(taxres), 21)
        self.assertEqual(taxres[4], '90.00')
        self.assertEqual(taxres[5], '18.00')
        self.assertEqual(taxres[20], '-10.00')
        self.assertIn('CNTRES|2|1', records)


del ModuleTestCase
