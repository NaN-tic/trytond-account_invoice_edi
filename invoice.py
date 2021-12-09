# -*- coding: utf-8 -*
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Not
from trytond.transaction import Transaction
from trytond.exceptions import UserError, UserWarning
from trytond.i18n import gettext

import os
from datetime import datetime
from decimal import Decimal
import codecs
from stdnum import ean
from jinja2 import Template

__all__ = ['InvoiceEdi', 'InvoiceEdiLine', 'SupplierEdi',
    'InvoiceEdiReference', 'InvoiceEdiMaturityDates', 'InvoiceEdiDiscount',
    'InvoiceEdiLineQty', 'InvoiceEdiTax', 'Cron']

DEFAULT_FILES_LOCATION = '/tmp/invoice'

# Tryton to EDI UOMS mapping
MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
KNOWN_EXTENSIONS = ['.txt', '.edi', '.pla']
DATE_FORMAT = '%Y%m%d'


def to_date(value):
    if value is None or value == '':
        return None
    return datetime.strptime(value, DATE_FORMAT)


def to_decimal(value, digits=2):
    if value is None or value == '':
        return None
    return Decimal(value).quantize(Decimal('10')**-digits)


class Cron(metaclass=PoolMeta):
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super(Cron, cls).__setup__()
        cls.method.selection.extend([
            ('invoice.edi|import_edi_files', 'Import Edi Invoices'),
        ])


SUPPLIER_TYPE = [('NADSCO', 'Legal Supplier'),
    ('NADBCO', 'Legal Purchaser'), ('NADSU', 'Supplier'),
    ('NADBY', 'Purchaser'), ('NADII', 'Invoice Issuer'),
    ('NADIV', 'Invoice Receiver'), ('NADDP', 'Stock Receiver'),
    ('NADPW', 'NADPW'), ('NADPE', 'NADPE'),
    ('NADPR', 'Payment Issuer'), ('NADDL', 'Endorser'),
    ('NAD', 'NAD'), ('NADMR', 'NADMR'),
    ('NADUC', 'Final Receiver'), ('NADSH', 'Sender'),
    ]


class SupplierEdiMixin(ModelSQL, ModelView):

    type_ = fields.Selection(SUPPLIER_TYPE, 'Type')

    edi_code = fields.Char('Edi Code')
    name = fields.Char('Name')
    commercial_register = fields.Char('Comercial Register')
    street = fields.Char('Street')
    city = fields.Char('City')
    zip = fields.Char('zip')
    vat = fields.Char('Vat')
    country_code = fields.Char('Country_code')
    account_bank = fields.Char('Account Bank')
    party = fields.Many2One('party.party', 'Party')

    def read_NADSCO(self, message):
        self.type_ = 'NADSCO'
        self.edi_code = message.pop(0) if message else ''
        self.name = message.pop(0) if message else ''
        if message:
            self.commercial_register = message.pop(0)
        if message:
            self.street = message.pop(0)
        if message:
            self.city = message.pop(0)
        if message:
            self.zip = message.pop(0)
        if message:
            self.vat = message.pop(0)
        if message:
            self.account_bank = message.pop(0)

    def read_NADBCO(self, message):
        self.type_ = 'NADBCO'
        self.edi_code = message.pop(0) if message else ''
        self.name = message.pop(0) if message else ''
        if message:
            self.street = message.pop(0)
        self.city = message.pop(0)
        if message:
            self.zip = message.pop(0)
        if message:
            self.vat = message.pop(0)
        if message:
            self.country_code = message.pop(0)

    def read_NADMR(self, message):
        self.type_ = 'NADMR'
        self.edi_code = message.pop(0) if message else ''
        self.name = message.pop(0) if message else ''
        if message:
            self.street = message.pop(0)
        if message:
            self.city = message.pop(0)
        if message:
            self.zip = message.pop(0)

    def read_NADDL(self, message):
        self.type_ = 'NADDL'
        self.edi_code = message.pop(0) if message else ''
        self.name = message.pop(0) if message else ''
        if message:
            self.street = message.pop(0)
        if message:
            self.city = message.pop(0)
        if message:
            self.zip = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NAD(self, message):
        self.type_ = 'NAD'
        self.edi_code = message.pop(0) if message else ''
        if message:
            self.vat = message.pop(0)

    def read_NADIV(self, message):
        self.type_ = 'NADIV'
        self.edi_code = message.pop(0) if message else ''
        if message:
            self.vat = message.pop(0)

    def read_NADPE(self, message):
        self.type_ = 'NADPE'
        self.edi_code = message.pop(0) if message else ''
        if message:
            self.vat = message.pop(0)

    def read_NADSU(self, message):
        self.type_ = 'NADSU'
        self.edi_code = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NADBY(self, message):
        self.type_ = 'NADBY'
        self.edi_code = message.pop(0) if message else ''
        if message:
            self.vat = message.pop(0)

    def read_NADBIV(self, message):
        self.type_ = 'NADBIV'
        self.edi_code = message.pop(0) if message else ''
        if message:
            self.vat = message.pop(0)

    def read_NADPR(self, message):
        self.type_ = 'NADPR'
        self.edi_code = message.pop(0) if message else ''

    def read_NADII(self, message):
        self.type_ = 'NADII'
        self.edi_code = message.pop(0) if message else ''

    def read_NADDP(self, message):
        self.type_ = 'NADDP'
        self.edi_code = message.pop(0) if message else ''

    def read_NADPW(self, message):
        self.type_ = 'NADPW'
        self.edi_code = message.pop(0) if message else ''

    def read_NADSH(self, message):
        self.type_ = 'NADSH'
        self.edi_code = message.pop(0) if message else ''

    def read_NADUC(self, message):
        self.type_ = 'NADUC'
        self.edi_code = message.pop(0) if message else ''

    def search_party(self):
        PartyId = Pool().get('party.identifier')
        domain = []
        if self.edi_code:
            domain += [('type', '=', 'edi'), ('code', '=', self.edi_code)]
        if domain == []:
            return
        identifier = PartyId.search(domain, limit=1)
        if identifier:
            self.party = identifier[0].party
            return
        if hasattr(self, 'vat'):
            domain = [('type', '=', 'vat'), ('code', '=', self.vat)]
            identifier = PartyId.search(domain, limit=1)
            if identifier:
                self.party = identifier[0].party


class SupplierEdi(SupplierEdiMixin, ModelSQL, ModelView):
    'Supplier Edi'
    __name__ = 'invoice.edi.supplier'

    edi_invoice = fields.Many2One('invoice.edi', 'Edi Invoice')


class InvoiceEdiReference(ModelSQL, ModelView):
    'Account Invoice Reference'
    __name__ = 'invoice.edi.reference'

    type_ = fields.Selection([('DQ', 'Shipment'), ('ON', 'Purchase'),
        ('CT', 'Contract'), ('IV', 'Invoice'), ('AAK', 'Expedition'),
        ('ALO', 'Confirmed Reception'), ('move', 'Move'),
        ('LI', 'Line Number'), ('SNR', 'Medical Record')], 'Reference Code')

    value = fields.Char('Reference')
    line_number = fields.Char('Line Number')
    origin = fields.Reference('Reference', selection='get_resource')
    edi_invoice = fields.Many2One('invoice.edi', 'Edi Invoice',
        ondelete='CASCADE')
    edi_invoice_line = fields.Many2One('invoice.edi.line',
        'Edi Invoice Line', ondelete='CASCADE')

    @classmethod
    def get_resource(cls):
        'Return list of Model names for resource Reference'
        return [(None, ''), ('stock.shipment.in', 'Shipment'),
            ('purchase.purchase', 'Purchase'), ('account.invoice', 'Invoice'),
            ('stock.move', 'Move')]

    def read_message(self, message):
        if message:
            message.pop(0)
        type_ = message.pop(0) if message else ''
        value = message.pop(0) if message else ''
        self.type_ = type_
        self.value = value

    def search_reference(self):
        model = None
        if self.type_ == 'DQ':
            model = 'stock.shipment.in'
        elif self.type_ == 'ON':
            model = 'purchase.purchase'
        elif self.type_ == 'IV':
            model = 'account.invoice'
        if self.type_ == 'move':
            model = 'stock.move'

        if not model:
            return

        Model = Pool().get(model)
        res = Model.search([('number', '=', self.value)], limit=1)
        self.origin = None
        if res != []:
            self.origin = res[0]


class InvoiceEdiMaturityDates(ModelSQL, ModelView):
    'Edi Maturity Dates'
    __name__ = 'invoice.edi.maturity_date'

    type_ = fields.Selection([('35', 'Unique Payment'),
        ('21', 'Various Payments')], 'Type')
    maturity_date = fields.Date('Maturity Date')
    amount = fields.Numeric('Amount', digits=(16, 2))
    invoice_edi = fields.Many2One('invoice.edi', 'Edi Invoice',
        ondelete='CASCADE')


class InvoiceEdiDiscount(ModelSQL, ModelView):
    'Edi discount'
    __name__ = 'invoice.edi.discount'

    type_ = fields.Selection([('A', 'Discount'), ('C', 'Charge')], 'Type')
    sequence = fields.Integer('sequence')
    discount = fields.Selection([(None, ''), ('EAB', 'Prompt Payment'),
        ('ABH', 'Volume or Abseling'), ('TD', 'Commercial'), ('FC', 'Freight'),
        ('PC', 'Packaging'), ('SH', 'Mounting'), ('IN', 'INSURANCE'),
        ('CW', 'Container'), ('RAD', 'Charge Container'), ('FI', 'Finance'),
        ('VEJ', 'Grren Dot'), ('X40', 'Royal decree')], 'Discount Type')
    percent = fields.Numeric('Percent', digits=(16, 2))
    amount = fields.Numeric('Amount', digits=(16, 2))
    invoice_edi = fields.Many2One('invoice.edi', 'Edi Invoice',
        ondelete='CASCADE')
    invoice_edi_line = fields.Many2One('invoice.edi.line',
        'Edi Invoice Line', ondelete='CASCADE')


class InvoiceEdi(ModelSQL, ModelView):
    'Account Invoice Edi Reception Header'
    __name__ = 'invoice.edi'

    company = fields.Many2One('company.company', 'Company', readonly=True)
    number = fields.Char('Number', readonly=True)
    invoice = fields.Many2One('account.invoice', 'Invoice')
    type_ = fields.Selection([
            ('380', 'Invoice'),
            ('381', 'Credit'),
            ('383', 'Charge Note')],
        'Document Type', readonly=True)
    function_ = fields.Selection([
            (None, ''),
            ('9', 'Original'),
            ('31', 'Copy')],
        'Message Function', readonly=True)
    invoice_date = fields.Date('Invoice Date', readonly=True)
    service_date = fields.Date('Service Date', readonly=True)
    start_period_date = fields.Date('Start Period', readonly=True)
    end_period_date = fields.Date('End Period', readonly=True)
    payment_type_value = fields.Selection([
            (None, ''),
            ('42', 'Account Bank'),
            ('10', 'cash'),
            ('20', 'check'),
            ('60', 'Bank Note'),
            ('14E', 'Bank Draft'),
            ('30', 'Credit Transfer')],
        'Payment Type Value', readonly=True)
    payment_type = fields.Many2One('account.payment.type', 'Payment Type',
        readonly=True)
    factoring = fields.Boolean('Factoring', readonly=True)
    currency_code = fields.Char('Currency Code', readonly=True)
    currency = fields.Many2One('currency.currency', 'Currency', readonly=True)
    maturity_dates = fields.One2Many('invoice.edi.maturity_date',
        'invoice_edi', 'Maturity Dates', readonly=True)
    discounts = fields.One2Many('invoice.edi.discount',
            'invoice_edi', 'Discounts', readonly=True)
    net_amount = fields.Numeric('Net Amount', digits=(16, 2), readonly=True)
    gross_amount = fields.Numeric('Gross Amount', digits=(16, 2),
        readonly=True)
    base_amount = fields.Numeric('Base Amount', digits=(16, 2), readonly=True)
    total_amount = fields.Numeric('Total Amount', digits=(16, 2),
        readonly=True)
    tax_amount = fields.Numeric('Tax Amount', digits=(16, 2), readonly=True)
    discount_amount = fields.Numeric('Discount Amount', digits=(16, 2),
        readonly=True)
    charge_amount = fields.Numeric('Charge Amount', digits=(16, 2),
        readonly=True)
    taxes = fields.One2Many('invoice.edi.tax', 'edi_invoice', 'Taxes',
        readonly=True)
    lines = fields.One2Many('invoice.edi.line', 'edi_invoice', 'Lines')
    suppliers = fields.One2Many('invoice.edi.supplier', 'edi_invoice',
        'Supplier', readonly=True)
    references = fields.One2Many('invoice.edi.reference',
        'edi_invoice', 'References', readonly=True)
    state = fields.Function(fields.Selection([('draft', 'Draft'),
        ('confirmed', 'Confirmed')], 'State'), 'get_state',
        searcher='search_state')
    differences_state = fields.Function(fields.Selection([
        (None, ''), ('ok', 'Ok'), ('difference', 'Difference')],
        'Difference State'), 'get_differences_state')
    difference_amount = fields.Function(fields.Numeric('Differences',
        digits=(16, 2)), 'get_difference_amount')
    party = fields.Function(fields.Many2One('party.party', 'Invoice Party'),
        'get_party', searcher='search_party')
    manual_party = fields.Many2One('party.party', 'Manual Party')
    comment = fields.Text('Comment')

    @classmethod
    def __setup__(cls):
        super(InvoiceEdi, cls).__setup__()
        cls._order = [
            ('invoice_date', 'DESC'),
            ('id', 'DESC'),
            ]
        cls._buttons.update({
            'create_invoices': {},
            'search_references': {}
        })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_state(self, name):
        if self.invoice:
            return 'confirmed'
        return 'draft'

    @classmethod
    def search_state(cls, name, clause):
        if clause[-1] == 'draft':
            return [('invoice', clause[1], None)]
        return [('invoice', '!=', None)]

    def get_differences_state(self, name):
        if not self.invoice:
            return
        if self.invoice.total_amount != self.total_amount:
            return 'difference'
        return 'ok'

    def get_difference_amount(self, name):
        if not self.invoice:
            return
        return self.total_amount - self.invoice.total_amount

    @classmethod
    def search_party(cls, name, clause):
        return ['OR', ('manual_party', ) + tuple(clause[1:]),
                [('suppliers.type_', '=', 'NADSU'),
                    ('suppliers.party', ) + tuple(clause[1:])]]

    def get_party(self, name):
        if self.manual_party:
            return self.manual_party.id
        for s in self.suppliers:
            if s.type_ == 'NADSU':
                return s.party and s.party.id

    def read_INV(self, message):
        self.number = message.pop(0) if message else ''
        self.type_ = message.pop(0) if message else ''
        self.function_ = '9'
        if message:
            self.function_ = message.pop(0)

    def read_TXT(self, message):
        self.comment = message.pop(0) if message else ''

    def read_DTM(self, message):
        self.invoice_date = to_date(message.pop(0)[0:8]) if message else None
        if message:
            self.service_date = to_date(message.pop(0)[0:8])
        if message:
            period = message.pop(0)
            self.start_period_date = to_date(period[0:8])
            self.end_period_date = to_date(period[8:])

    def read_PAI(self, message):
        payment_type = message.pop(0) if message else ''
        self.payment_type_value = payment_type
        factoring = False
        if message:
            factoring = message.pop(0)

        self.factoring = factoring

    def read_RFF(self, message):
        REF = Pool().get('invoice.edi.reference')
        ref = REF()
        ref.type_ = message.pop(0) if message else ''
        ref.value = message.pop(0) if message else ''
        if message:
            ref.line_number = message.pop(0)
        ref.search_reference()
        if not getattr(self, 'references', False):
            self.references = []
        self.references += (ref,)

    def read_CUX(self, message):
        message.pop(0)
        self.currency_code = message.pop(0) if message else ''

    def read_PAT(self, message):
        MaturityDate = Pool().get('invoice.edi.maturity_date')
        line = MaturityDate()
        line.type_ = message.pop(0) if message else ''
        line.maturity_date = to_date(message.pop(0)) if message else None
        if message:
            line.amount = to_decimal(message.pop(0))
        if not getattr(self, 'maturity_dates', False):
            self.maturity_dates = []
        self.maturity_dates += (line,)

    def read_ALC(self, message):
        Discount = Pool().get('invoice.edi.discount')
        discount = Discount()
        discount.type_ = message.pop(0) if message else ''
        sequence = message.pop(0) if message else ''
        discount.sequence = int(sequence) or None
        discount.discount = message.pop(0) if message else ''
        discount.percent = to_decimal(message.pop(0)
            ) if message else Decimal(0)
        discount.amount = to_decimal(message.pop(0)
            ) if message else Decimal(0)
        if not getattr(self, 'discounts', False):
            self.discounts = []
        self.discounts += (discount,)

    def read_MOARES(self, message):
        self.net_amount = to_decimal(message.pop(0)) if message else Decimal(0)
        self.gross_amount = to_decimal(message.pop(0)
            ) if message else Decimal(0)
        self.base_amount = to_decimal(message.pop(0)
            ) if message else Decimal(0)
        self.total_amount = to_decimal(message.pop(0)
            ) if message else Decimal(0)
        self.tax_amount = to_decimal(message.pop(0)) if message else Decimal(0)
        if message:
            self.discount_amount = to_decimal(message.pop(0))
        if message:
            self.charge_amount = to_decimal(message.pop(0))

    def read_TAXRES(self, message):
        Tax = Pool().get('invoice.edi.tax')
        tax = Tax()
        tax.type_ = message.pop(0)
        tax.percent = to_decimal(message.pop(0)) if message else Decimal(0)
        tax.tax_amount = to_decimal(message.pop(0)) if message else Decimal(0)
        print(message)
        if message:
            tax.base_amount = to_decimal(message.pop(0))
        tax.search_tax()
        if not getattr(self, 'taxes', False):
            self.taxes = []
        self.taxes += (tax,)

    def read_CNTRES(self, message):
        pass

    @classmethod
    def import_edi_file(cls, data):
        pool = Pool()
        Invoice = pool.get('invoice.edi')
        InvoiceLine = pool.get('invoice.edi.line')
        SupplierEdi = pool.get('invoice.edi.supplier')
        Configuration = pool.get('invoice.edi.configuration')

        config = Configuration(1)
        separator = config.separator

        invoice = None
        invoice_line = None
        document_type = data.pop(0)
        if document_type == 'INVOIC_D_93A_UN_EAN007':
            return
        for line in data:
            line = line.replace('\n', '').replace('\r', '')
            line = line.split(separator)
            msg_id = line.pop(0)
            if msg_id == 'INV':
                invoice = Invoice()
                invoice.read_INV(line)
            elif msg_id == 'LIN':
                # if invoice_line:
                #     invoice_line.search_related(invoice)
                invoice_line = InvoiceLine()
                invoice_line.read_LIN(line)
                if not getattr(invoice, 'lines', False):
                    invoice.lines = []
                invoice.lines += (invoice_line,)
            elif 'LIN' in msg_id:
                if hasattr(invoice_line, 'read_%s' % msg_id):
                    getattr(invoice_line, 'read_%s' % msg_id)(line)
            elif msg_id in [x[0] for x in SUPPLIER_TYPE]:
                supplier = SupplierEdi()
                if hasattr(supplier, 'read_%s' % msg_id):
                    getattr(supplier, 'read_%s' % msg_id)(line)
                supplier.search_party()
                if not getattr(invoice, 'suppliers', False):
                    invoice.suppliers = []
                invoice.suppliers += (supplier,)
            elif 'NAD' in msg_id:
                continue
            else:
                if hasattr(invoice, 'read_%s' % msg_id):
                    getattr(invoice, 'read_%s' % msg_id)(line)

        # invoice_line.search_related(invoice)
        return invoice

    def add_attachment(self, attachment, filename=None):
        pool = Pool()
        Attachment = pool.get('ir.attachment')
        if not filename:
            filename = datetime.now().strftime("%y/%m/%d %H:%M:%S")
        attach = Attachment(
            name=filename,
            type='data',
            data=attachment.encode('utf8'),
            resource=self)
        attach.save()

    @classmethod
    def import_edi_files(cls, invoices=None):
        pool = Pool()
        Configuration = pool.get('invoice.edi.configuration')
        configuration = Configuration(1)
        source_path = os.path.abspath(configuration.edi_files_path or
             DEFAULT_FILES_LOCATION)
        files = [os.path.join(source_path, fp) for fp in
                 os.listdir(source_path) if os.path.isfile(os.path.join(
                     source_path, fp))]
        files_to_delete = []
        to_save = []
        attachments = dict()
        for fname in files:
            if fname[-4:].lower() not in KNOWN_EXTENSIONS:
                continue
            with codecs.open(fname, 'rb', 'latin-1') as fp:
                data = fp.readlines()
                invoice = cls.import_edi_file(data)

            basename = os.path.basename(fname)
            if invoice:
                attachments[invoice] = ("\n".join(data), basename)
                to_save.append(invoice)
                files_to_delete.append(fname)

        if to_save:
            cls.save(to_save)

        with Transaction().set_user(0, set_context=True):
            for invoice, (data, basename) in attachments.items():
                invoice.add_attachment(data, basename)

        if files_to_delete:
            for file in files_to_delete:
                os.remove(file)

        cls.search_references(to_save)

    def get_invoice(self):
        pool = Pool()
        Invoice = pool.get('account.invoice')

        invoice = Invoice()
        invoice.currency = Invoice.default_currency()
        invoice.company = self.company
        invoice.party = self.party
        invoice.on_change_party()
        invoice.reference = self.number
        invoice.invoice_date = self.invoice_date
        invoice.type = 'in'
        invoice.on_change_type()
        invoice.account = invoice.on_change_with_account()
        invoice.state = 'draft'
        return invoice

    def get_discount_invoice_line(self, description, amount, taxes=None):
        Config = Pool().get('account.configuration')
        config = Config(1)
        Line = Pool().get('account.invoice.line')
        line = Line()
        line.invoice_type = 'in'
        line.party = self.party
        line.type = 'line'
        line.description = description
        line.quantity = 1
        line.unit_price = amount
        line.gross_unit_price = amount
        line.account = config.default_product_account_expense
        line.taxes = taxes
        return line

    @classmethod
    @ModelView.button
    def search_references(cls, edi_invoices):
        for edi_invoice in edi_invoices:
            if edi_invoice.invoice:
                continue
            invoice = edi_invoice.get_invoice()
            invoice.lines = []
            for eline in edi_invoice.lines:
                eline.search_related(edi_invoice)
                eline.save()

    @classmethod
    @ModelView.button
    def create_invoices(cls, edi_invoices):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        invoices = []
        to_save = []
        for edi_invoice in edi_invoices:
            if edi_invoice.invoice:
                continue
            invoice = edi_invoice.get_invoice()
            invoice.lines = []
            for eline in edi_invoice.lines:
                line = eline.get_line()
                invoice.lines += (line,)
            invoice.on_change_lines()
            invoice.on_change_lines()
            invoice.on_change_type()
            invoice.is_edi = True
            edi_invoice.invoice = invoice
            invoices.append(invoice)
            to_save.append(edi_invoice)

        Invoice.save(invoices)
        Invoice.validate(invoices)
        Invoice.draft(invoices)
        cls.save(to_save)


class InvoiceEdiLineQty(ModelSQL, ModelView):
    'Invoice Edi Line Qty'
    __name__ = 'invoice.edi.line.quantity'

    type_ = fields.Selection([('47', 'Invoiced'), ('46', 'Delivered'),
        ('61', 'Returned'), ('15E', 'Without Charge')], 'Type')
    quantity = fields.Numeric('Quantity', digits=(16, 4))
    uom_char = fields.Char('Uom')
    line = fields.Many2One('invoice.edi.line', 'Line', ondelete='CASCADE')

    def search_uom(self):
        # TODO: Not implemented, now use product uom.
        pass


class InvoiceEdiTax(ModelSQL, ModelView):
    'Invoice Edi Line Qty'
    __name__ = 'invoice.edi.tax'

    type_ = fields.Selection([('VAT', 'VAT'), ('EXT', 'Exempt'),
        ('RET', 'IRPF'), ('RE', 'Equivalence Surcharge'),
        ('ACT', 'Alcohol Tax'), ('ENV', 'Gree Dot'), ('IGIC', 'IGIC')], 'Type')
    percent = fields.Numeric('Percent', digits=(16, 2))
    tax_amount = fields.Numeric('Tax Amount', digits=(16, 2))
    base_amount = fields.Numeric('Base Amount', digits=(16, 2))
    line = fields.Many2One('invoice.edi.line', 'Line', ondelete='CASCADE')
    edi_invoice = fields.Many2One('invoice.edi', 'Invoice', ondelete='CASCADE')
    comment = fields.Text('Comment')

    def search_tax(self):
        # TODO: Not implementd, now use product tax
        pass


class InvoiceEdiLine(ModelSQL, ModelView):
    'Invoice Edi Line'
    __name__ = 'invoice.edi.line'

    edi_invoice = fields.Many2One('invoice.edi', 'Invoice', ondelete='CASCADE')
    code = fields.Char('Code')
    code_type = fields.Selection([
            (None, ''),
            ('EAN', 'EAN'),
            ('EAN8', 'EAN8'),
            ('EAN12', 'UPC (EAN12)'),
            ('EAN13', 'EAN13'),
            ('EAN14', 'GTIN (EAN14)'),
            ('DUN14', 'DUN14'),
        ], 'Code Type')
    sequence = fields.Integer('Sequence')
    supplier_code = fields.Char('Supplier Code')
    purchaser_code = fields.Char('Purchaser Code')
    lot_number = fields.Char('Lot Number')
    serial_number = fields.Char('Serial Number')
    customer_code = fields.Char('Customer Code')
    producer_code = fields.Char('Producer Code')
    national_code = fields.Char('National Code')
    hibc_code = fields.Char('Healh Industry Bar Code')
    description = fields.Char('Description')
    characteristic = fields.Selection([(None, ''), ('M', 'Goods'),
        ('C', 'C')], 'Characteristic')
    qualifier = fields.Selection([(None, ''), ('F', 'Free Description')],
        'Qualifier  ')
    quantities = fields.One2Many('invoice.edi.line.quantity', 'line',
        'Quantities')
    delivery_date = fields.Char('Delivery Date')
    base_amount = fields.Numeric('Base Amount', digits=(16, 2))
    total_amount = fields.Numeric('Total Amount', digits=(16, 2))
    unit_price = fields.Numeric('Unit Price', digits=(16, 4))
    gross_price = fields.Numeric('Gross Price', digits=(16, 4))
    references = fields.One2Many('invoice.edi.reference',
        'edi_invoice_line', 'References')
    taxes = fields.One2Many('invoice.edi.tax', 'line', 'Taxes')
    discounts = fields.One2Many('invoice.edi.discount',
        'invoice_edi_line', 'Discounts')
    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Function(fields.Numeric('Quantity', digits=(16, 4)),
        'invoiced_quantity')
    invoice_line = fields.Many2One('account.invoice.line', 'Invoice Line')
    note = fields.Text('Note')

    @classmethod
    def __setup__(cls):
        super(InvoiceEdiLine, cls).__setup__()

    def search_related(self, edi_invoice):
        pool = Pool()
        ProductIdentifier = pool.get('product.identifier')
        REF = Pool().get('invoice.edi.reference')
        domain = [('code', '=', self.code)]
        codes = ProductIdentifier.search(domain, limit=1)
        if not codes:
            return
        product = codes[0].product
        self.product = product

        purchases = [x.origin for x in edi_invoice.references if
            x.type_ == 'ON' and x.origin]
        self.references = []
        for purchase in purchases:
            for move in purchase.moves:
                if move.state != 'done':
                    continue
                if move.product == product:  # TODO: check for quantity?
                    ref = REF()
                    ref.type_ = 'move'
                    ref.origin = 'stock.move,%s' % move.id
                    self.references += (ref,)

    def get_line(self):
        if self.edi_invoice.type_ == '381':  # CREDIT:
            return self.get_line_credit()
        if self.references is None or len(self.references) != 1:
            raise UserError(gettext(
                'account_invoice_edi.confirm_invoice_with_reference',
                line=self.description))

        move, = self.references
        invoice_lines = [x for x in move.origin.invoice_lines if not x.invoice]
        if not invoice_lines or len(invoice_lines) != 1:
            raise UserError(gettext(
                'account_invoice_edi.confirm_invoice_with_invoice',
                line=self.description))

        invoice_line, = invoice_lines

        # JUst invoice wat system expect to see differences.
        # invoice_line.gross_unit_price = self.gross_price or self.unit_price
        # invoice_line.unit_price = self.unit_price
        # if self.unit_price and self.gross_price:
        #     invoice_line.discount = Decimal(1 -
        #         self.unit_price/self.gross_price).quantize(Decimal('.01'))
        # else:
        #     invoice_line.unit_price = Decimal(
        #         self.base_amount / self.quantity).quantize(Decimal('0.0001'))

        self.invoice_line = invoice_line
        return invoice_line

    def get_line_credit(self):
        move = self.references and self.references[0]
        invoice_lines = [x for x in move and move.origin.invoice_lines or []
            if not x.invoice]
        invoice_line = invoice_lines and invoice_lines[0]

        Line = Pool().get('account.invoice.line')
        line = Line()
        line.product = self.product
        line.invoice_type = 'in'
        line.quantity = self.quantity
        if self.base_amount < 0:
            line.quantity = -self.quantity
        line.party = self.edi_invoice.party
        line.type = 'line'
        line.on_change_product()
        line.on_change_account()
        line.gross_unit_price = self.gross_price or self.unit_price
        line.unit_price = self.unit_price
        if self.unit_price and self.gross_price:
            line.discount = Decimal(1 -
                self.unit_price / self.gross_price).quantize(Decimal('.01'))
        else:
            line.unit_price = Decimal(
                self.base_amount / self.quantity).quantize(Decimal('0.0001'))
        if invoice_line:
            line.origin = invoice_line
        self.invoice_line = line
        return line

    def invoiced_quantity(self, name):
        for q in self.quantities:
            if q.type_ == '47':
                return q.quantity
        return Decimal('0')

    def read_LIN(self, message):
        def _get_code_type(code):
            # stdnum.ean only handles numbers EAN-13, EAN-8, UPC (12-digit)
            # and GTIN (EAN-14) format
            if ean.is_valid(code):
                return 'EAN%s' % str(len(code))
            # TODO DUN14
            return 'EAN'

        self.code = message.pop(0) if message else ''
        self.code_type = None
        code_type = message.pop(0) if message else ''
        if code_type == 'EN':
            self.code_type = _get_code_type(self.code)
        # Some times the provider send the EAN13 without left zeros
        # and the EAN is an EAN13 but the check fail becasue it have
        # less digits.
        if self.code_type == 'EAN' and len(self.code) < 13:
            code = self.code.zfill(13)
            if ean.is_valid(code):
                self.code = code
                self.code_type = 'EAN13'
        if message:
            self.sequence = int(message.pop(0))

    def read_PIALIN(self, message):
        self.supplier_code = message.pop(0) if message else ''
        if message:
            self.purchaser_code = message.pop(0)
        if message:
            self.lot_number = message.pop(0)
        if message:
            self.serial_number = message.pop(0)
        if message:
            self.customer_code = message.pop(0)
        if message:
            self.producer_code = message.pop(0)
        if message:
            self.national_code = message.pop(0)
        if message:
            self.hibc_code = message.pop(0)

    def read_IMDLIN(self, message):
        self.description = message.pop(0) if message else ''
        self.characteristic = message.pop(0) if message else ''
        self.qualifier = message.pop(0) if message else ''

    def read_QTYLIN(self, message):
        QTY = Pool().get('invoice.edi.line.quantity')
        qty = QTY()
        qty.type_ = message.pop(0) if message else ''
        qty.quantity = to_decimal(message.pop(0), 4) if message else Decimal(0)
        if qty.type_ == '47':
            self.quantity = qty.quantity
        if message:
            qty.uom_char = message.pop(0)
        if not getattr(self, 'quantities', False):
            self.quantities = []
        self.quantities += (qty,)

    def read_DTMLINE(self, message):
        self.delivery_date = to_date(message.pop(0)) if message else None

    def read_MOALIN(self, message):
        self.base_amount = to_decimal(message.pop(0)
            ) if message else Decimal(0)
        if message:
            self.total_amount = to_decimal(message.pop(0))

    def read_PRILIN(self, message):
        type_ = message.pop(0)
        if type_ == 'AAA':
            self.unit_price = to_decimal(message.pop(0), 4
                ) if message else Decimal(0)
        elif type_ == 'AAB':
            self.gross_price = to_decimal(message.pop(0), 4
                ) if message else Decimal(0)

    def read_RFFLIN(self, message):
        REF = Pool().get('invoice.edi.reference')
        ref = REF()
        ref.type_ = message.pop(0) if message else ''
        ref.value = message.pop(0) if message else ''
        ref.search_reference()
        if message:
            ref.line_number = message.pop(0) if message else ''
        if not getattr(self, 'references', False):
            self.references = []
        self.references += (ref,)

    def read_TAXLIN(self, message):
        Tax = Pool().get('invoice.edi.tax')
        tax = Tax()
        tax.type_ = message.pop(0) if message else ''
        tax.percent = to_decimal(message.pop(0)) if message else Decimal(0)
        if message:
            tax.tax_amount = to_decimal(message.pop(0))
        if not getattr(self, 'taxes', False):
            self.taxes = []
        self.taxes += (tax,)

    def read_TXTLIN(self, message):
        self.note = message.pop(0) if message else ''

    def read_ALCLIN(self, message):
        Discount = Pool().get('invoice.edi.discount')
        discount = Discount()
        discount.type_ = message.pop(0) if message else ''
        discount.sequence = int(message.pop(0) or 0) if message else 0
        discount.discount = message.pop(0) if message else ''
        discount.percent = to_decimal(message.pop(0)
            ) if message else Decimal(0)
        discount.amount = to_decimal(message.pop(0)) if message else Decimal(0)
        if not getattr(self, 'discounts', False):
            self.discounts = []
        self.discounts += (discount,)


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    is_edi = fields.Boolean('Is EDI',
        help='Use EDI protocol for this invoice')
    edi_invoices = fields.One2Many('invoice.edi', 'invoice',
        'Edi Invoices')
    edi_document_type = fields.Function(fields.Selection([
            ('', 'Nothing'),
            ('380', 'Invoice'),
            ('381', 'Credit Invoice'),
            ('325', 'Pro-forma'),
            ], 'EDI Document Type'), 'get_edi_document_type')

    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()
        cls._check_modify_exclude.add('is_edi')
        cls._buttons.update({
                'generate_edi_file': {'invisible': (
                        Not(Eval('is_edi')) |
                        (Eval('type') != 'out') |
                        (Eval('state').in_(['draft', 'cancel']))
                        )},
                })

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)

        # Field name change:
        if table.column_exist('use_edi'):
            table.column_rename('use_edi', 'is_edi')

        super().__register__(module_name)

    def get_edi_document_type(self, name):
        if self.state in ('draft', 'cancel'):
            return ''
        if self.total_amount < 0:
            # Credit Invoice
            return '381'
        elif self.state == 'validated':
            # Pro-forma
            return '325'
        # Invoice
        return '380'

    @classmethod
    @ModelView.button
    def generate_edi_file(cls, invoices):
        pool = Pool()
        Configuration = pool.get('invoice.edi.configuration')
        Warning = pool.get('res.user.warning')

        post_edi_invoice = Transaction().context.get('post_edi_invoice', False)
        if post_edi_invoice:
            configuration = Configuration(1)
            if not configuration.automatic_edi_invoice_out:
                return

        for invoice in invoices:
            if invoice.type == 'out' and invoice.is_edi:
                if post_edi_invoice:
                    warning_name = '%s.send_edi_invoice' % invoice
                    if Warning.check(warning_name):
                        raise UserWarning(warning_name, gettext(
                                'account_invoice_edi.msg_send_edi_invoice',
                                invoice=invoice.number))
                invoice.generate_edi()

    def generate_edi(self):
        pool = Pool()
        InvoiceConfiguration = pool.get('invoice.edi.configuration')
        config = InvoiceConfiguration(1)

        template_name = 'invoice_out_edi_template.jinja2'
        result_name = 'invoice_{}.PLA'.format(self.number or self.id)
        template_path = os.path.join(MODULE_PATH, template_name)
        try:
            result_path = os.path.join(config.outbox_path_edi, result_name)
        except Exception:
            raise UserError(gettext('account_invoice_edi.msg_path_not_found'))
        if self.type == 'out' and self.is_edi:
            with open(template_path) as file_:
                template = Template(file_.read())
            edi_file = template.render({'invoice': self})
            if not os.path.exists(result_path):
                with open(result_path, 'w') as f:
                    f.write(edi_file)

    @classmethod
    def post(cls, invoices):
        pool = Pool()
        Warning = pool.get('res.user.warning')

        super(Invoice, cls).post(invoices)

        differences = []
        for invoice in invoices:
            if invoice.type == 'out' or not invoice.is_edi:
                continue
            if not invoice.edi_invoices:
                continue
            edi_invoice = invoice.edi_invoices[-1]
            if edi_invoice.differences_state == 'difference':
                differences.append(invoice)

        if differences:
            key = 'confirm_invoice_with_difference_%s' % (
                    "_".join([str(x.id) for x in differences]))
            if Warning.check(key):
                raise UserWarning(key, gettext(
                        'account_invoice_edi.confirm_invoice_with_difference',
                        invoices=",".join([x.reference for x in differences])))
        with Transaction().set_context(post_edi_invoice=True):
            cls.generate_edi_file(invoices)


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    shipment_reference = fields.Function(fields.Char('Shipment Number'),
        'get_shipment_reference')
    code_ean13 = fields.Function(fields.Char("Code EAN13"), 'get_code_ean13')

    def get_code_ean13(self, name):
        if self.product:
            for identifier in self.product.identifiers:
                if identifier.type == 'ean' and len(identifier.code) == 13:
                    return identifier.code
        return None

    def get_shipment_reference(self, name):
        name = name[9:]
        values = []
        for move in self.stock_moves:
            value = getattr(move.shipment, name, None)
            if value:
                values.append(value)
        if values:
            return " / ".join(values)
        return ""
