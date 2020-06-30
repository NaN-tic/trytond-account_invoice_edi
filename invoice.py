# -*- coding: utf-8 -*
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Bool, Or
from trytond.transaction import Transaction
import os
from glob import glob
from unidecode import unidecode
from datetime import datetime
from trytond import backend
from decimal import Decimal
import codecs

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


class InvoiceEdiConfiguration(ModelSingleton, ModelSQL, ModelView):
    'Invoice Edi Configuration'
    __name__ = 'invoice.edi.configuration'

    edi_files_path = fields.Char('Invoice File Path')
    separator = fields.Char('Separator')

    @classmethod
    def default_separator(cls):
        return '|'


class SupplierEdi(ModelSQL, ModelView):
    'Supplier Edi'
    __name__ = 'invoice.edi.supplier'

    type_ = fields.Selection([('NADSCO','Legal Supplier'),
        ('NADBCO', 'Legal Purchaser'), ('NADSU', 'Supplier'),
        ('NADBY', 'Purchaser'), ('NADII', 'Invoice Issuer'),
        ('NADIV', 'Invoice Receiver'), ('NADDP', 'Stock Receiver'),
        ('NADPW', 'NADPW'),('NADPE', 'NADPE'),
        ('NADPR', 'Payment Issuer'), ('NADDL', 'Endorser'),
        ('NAD', 'NAD'),('NADMR', 'NADMR')], 'Type')

    edi_code = fields.Char('Edi Code')
    name = fields.Char('Name')
    commercial_register = fields.Char('Comercial Register')
    street = fields.Char('Street')
    city = fields.Char('City')
    zip = fields.Char('zip')
    vat = fields.Char('Vat')
    country_code = fields.Char('Country_code')
    account_bank = fields.Char('Account Bank')
    edi_invoice = fields.Many2One('invoice.edi', 'Edi Invoice')
    party = fields.Many2One('party.party', 'Party')

    def read_NADSCO(self, message):
        self.type_ = 'NADSCO'
        self.edi_code = message.pop(0)
        self.name = message.pop(0)
        self.commercial_register = message.pop(0)
        self.street = message.pop(0)
        self.city = message.pop(0)
        self.zip = message.pop(0)
        self.vat = message.pop(0)
        if message:
            self.account_bank = message.pop(0)

    def read_NADBCO(self, message):
        self.type_ = 'NADBCO'
        self.edi_code = message.pop(0)
        self.name = message.pop(0)
        self.street = message.pop(0)
        self.city = message.pop(0)
        self.zip = message.pop(0)
        self.vat = message.pop(0)
        if message:
            self.country_code = message.pop(0)

    def read_NADMR(self, message):
        self.type_ = 'NADMR'
        self.edi_code = message.pop(0)
        self.name = message.pop(0)
        self.street = message.pop(0)
        self.city = message.pop(0)
        self.zip = message.pop(0)

    def read_NADDL(self, message):
        self.type_ = 'NADDL'
        self.edi_code = message.pop(0)
        self.name = message.pop(0)
        self.street = message.pop(0)
        self.city = message.pop(0)
        self.zip = message.pop(0)
        self.vat = message.pop(0)

    def read_NAD(self, message):
        self.type_ = 'NAD'
        self.edi_code = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NADIV(self, message):
        self.type_ = 'NADIV'
        self.edi_code = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NADPE(self, message):
        self.type_ = 'NADPE'
        self.edi_code = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NADSU(self, message):
        self.type_ = 'NADSU'
        self.edi_code = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NADBY(self, message):
        self.type_ = 'NADBY'
        self.edi_code = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NADBIV(self, message):
        self.type_ = 'NADBIV'
        self.edi_code = message.pop(0)
        if message:
            self.vat = message.pop(0)

    def read_NADPR(self, message):
        self.type_ = 'NADPR'
        self.edi_code = message.pop(0)

    def read_NADII(self, message):
        self.type_ = 'NADII'
        self.edi_code = message.pop(0)

    def read_NADDP(self, message):
        self.type_ = 'NADDP'
        self.edi_code = message.pop(0)

    def read_NADPW(self, message):
        self.type_ = 'NADPW'
        self.edi_code = message.pop(0)

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



class InvoiceEdiReference(ModelSQL, ModelView):
    'Account Invoice Reference'
    __name__ = 'invoice.edi.reference'

    type_ = fields.Selection([('DQ', 'Shipment'), ('ON', 'Purchase'),
        ('CT', 'Contract'), ('IV', 'Invoice'), ('AAK', 'Expedition'),
        ('ALO', 'Confirmed Reception'),('move', 'Move'),
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
        messsage_id = message.pop(0)
        type_ = message.pop(0)
        value = message.pop(0)
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
            self.origin = str(res[0])

class InvoiceEdiMaturityDates(ModelSQL, ModelView):
    'Edi Maturity Dates'
    __name__ = 'invoice.edi.maturity_date'

    type_ = fields.Selection([('35', 'Unique Payment'),
        ('21', 'Various Payments')], 'Type')
    maturity_date = fields.Date('Maturity Date')
    amount = fields.Numeric('Amount', digits=(16,2))
    invoice_edi = fields.Many2One('invoice.edi', 'Edi Invoice',
        ondelete='CASCADE')


class InvoiceEdiDiscount(ModelSQL, ModelView):
    'Edi discount'
    __name__ = 'invoice.edi.discount'

    type_ = fields.Selection([('A', 'Discount'),('C', 'Charge')], 'Type')
    sequence = fields.Integer('sequence')
    discount = fields.Selection([(None, ''),('EAB', 'Prompt Payment'),
        ('ABH', 'Volume or Abseling'), ('TD', 'Commercial'), ('FC', 'Freight'),
        ('PC', 'Packaging'), ('SH', 'Mounting'), ('IN', 'INSURANCE'),
        ('CW', 'Container'), ('RAD', 'Charge Container'), ('FI', 'Finance'),
        ('VEJ', 'Grren Dot'), ('X40','Royal decree')], 'Discount Type')
    percent = fields.Numeric('Percent', digits=(16,2))
    amount = fields.Numeric('Amount', digits=(16,2))
    invoice_edi = fields.Many2One('invoice.edi', 'Edi Invoice',
        ondelete='CASCADE')
    invoice_edi_line = fields.Many2One('invoice.edi.line',
        'Edi Invoice Line', ondelete='CASCADE')


class InvoiceEdi(ModelSQL, ModelView):
    'Account Invoice Edi Reception Header'
    __name__ = 'invoice.edi'

    company = fields.Many2One('company.company', 'Company', readonly=True)
    number = fields.Char('Number', readonly=True)
    invoice = fields.Many2One('account.invoice', 'Invoice', readonly=True)
    type_ = fields.Selection([('380', 'Invoice'),('381', 'Credit'),
        ('383', 'Charge Note'),], 'Document Type', readonly=True)
    function_ = fields.Selection([(None, ''),('9', 'Original'), ('31', 'Copy')],
        'Message Function', readonly=True)
    invoice_date = fields.Date('Invoice Date', readonly=True)
    service_date = fields.Date('Service Date', readonly=True)
    start_period_date = fields.Date('Start Period', readonly=True)
    end_period_date = fields.Date('End Period', readonly=True)
    payment_type_value = fields.Selection([(None, ''), ('42', 'Account Bank'),
        ('10', 'cash'), ('20', 'check'), ('60', 'Bank Note'),
        ('14E', 'Bank Draft')], 'Payment Type Value', readonly=True)
    payment_type = fields.Many2One('account.payment.type', 'Payment Type',
        readonly=True)
    factoring = fields.Boolean('Factoring', readonly=True)
    currency_code = fields.Char('Currency Code', readonly=True)
    currency = fields.Many2One('currency.currency', 'Currency', readonly=True)
    maturity_dates = fields.One2Many('invoice.edi.maturity_date',
        'invoice_edi', 'Maturity Dates', readonly=True)
    discounts = fields.One2Many('invoice.edi.discount',
            'invoice_edi', 'Discounts', readonly=True)
    net_amount = fields.Numeric('Net Amount', digits=(16,2), readonly=True)
    gross_amount = fields.Numeric('Gross Amount', digits=(16,2),readonly=True)
    base_amount = fields.Numeric('Base Amount', digits=(16,2), readonly=True)
    total_amount = fields.Numeric('Total Amount', digits=(16,2), readonly=True)
    tax_amount = fields.Numeric('Tax Amount', digits=(16,2), readonly=True)
    discount_amount = fields.Numeric('Discount Amount', digits=(16,2),
        readonly=True)
    charge_amount = fields.Numeric('Charge Amount', digits=(16,2),
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
    difference_amount =fields.Function(fields.Numeric('Differences',
        digits=(16,2)), 'get_difference_amount')
    party = fields.Function(fields.Many2One('party.party', 'Invoice Party'),
        'get_party', searcher='search_party')
    manual_party = fields.Many2One('party.party', 'Manual Party')

    @classmethod
    def __setup__(cls):
        super(InvoiceEdi, cls).__setup__()
        cls._buttons.update({
            'create_invoices': {}
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
        return [('invoice', clause[1], None)]

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
                [('suppliers.type_', '=', 'NADSU'), ('suppliers.party', ) + tuple(clause[1:])]]

    def get_party(self, name):
        if self.manual_party:
            return self.manual_party.id
        for s in self.suppliers:
            if s.type_ == 'NADSU':
                return s.party and s.party.id

    def read_INV(self, message):
        self.number = message.pop(0)
        self.type_ = message.pop(0)
        self.function_ = '9'
        if message:
            self.function_ = message.pop(0)

    def read_TXT(self, message):
        self.comment = message.pop(0)

    def read_DTM(self, message):
        print(message)
        self.invoice_date = to_date(message.pop(0)[0:8])
        if message:
            self.service_date = to_date(message.pop(0)[0:8])
        if message:
            period = message.pop(0)
            self.start_period_date = to_date(period[0:8])
            self.end_period_date = to_date(priod[8:])


    def read_PAI(self, message):
        payment_type = message.pop(0)
        self.payment_type_value = payment_type
        factoring = False
        if message:
            factoring = message.pop(0)

        self.factoring = factoring

    def read_RFF(self, message):
        REF = Pool().get('invoice.edi.reference')
        ref = REF()
        ref.type_ = message.pop(0)
        ref.value = message.pop(0)
        if message:
            ref.line_number = message.pop(0)
        ref.search_reference()
        if not getattr(self, 'references', False):
            self.references = []
        self.references += (ref,)

    def read_CUX(self, message):
        message_id = message.pop(0)
        self.currency_code = message.pop(0)

    def read_PAT(self, message):
        MaturityDate = Pool().get('invoice.edi.maturity_date')
        line = MaturityDate()
        line.type_ = message.pop(0)
        line.maturity_date = to_date(message.pop(0))
        if message:
            line.amount = to_decimal(message.pop(0))
        if not getattr(self, 'maturity_dates', False):
            self.maturity_dates = []
        self.maturity_dates += (line,)

    def read_ALC(self, message):
        Discount =  Pool().get('invoice.edi.discount')
        discount = Discount()
        discount.type_ = message.pop(0)
        sequence = message.pop(0)
        discount.sequence = int(sequence) or None
        discount.discount = message.pop(0)
        discount.percent = to_decimal(message.pop(0))
        discount.amount = to_decimal(message.pop(0))
        if not getattr(self, 'discounts', False):
            self.discounts = []
        self.discounts += (discount,)

    def read_MOARES(self, message):
        self.net_amount = to_decimal(message.pop(0))
        self.gross_amount = to_decimal(message.pop(0))
        self.base_amount = to_decimal(message.pop(0))
        self.total_amount = to_decimal(message.pop(0))
        self.tax_amount = to_decimal(message.pop(0))
        if message:
            self.discount_amount = to_decimal(message.pop(0))
        if message:
            self.charge_amount = to_decimal(message.pop(0))

    def read_TAXRES(self, message):
        Tax = Pool().get('invoice.edi.tax')
        tax = Tax()
        tax.type_ = message.pop(0)
        tax.percent = to_decimal(message.pop(0))
        tax.tax_amount = to_decimal(message.pop(0))
        if message:
            tax.base_amount = to_decimal(message.pop(0))
        tax.search_tax()
        if not getattr(self, 'taxes', False):
            self.taxes = []
        self.taxes += (tax,)

    def read_CNTRES(self, message):
        pass


    @classmethod
    def import_edi_file(self, data):
        pool = Pool()
        Invoice = pool.get('invoice.edi')
        InvoiceLine = pool.get('invoice.edi.line')
        SupplierEdi = pool.get('invoice.edi.supplier')
        Configuration = pool.get('invoice.edi.configuration')

        config = Configuration(1)
        separator = str(config.separator)

        invoice = None
        invoice_line = None
        document_type = data.pop(0)
        if document_type == 'INVOIC_D_93A_UN_EAN007':
            return
        print document_type
        for line in data:
            line = line.replace('\n','').replace('\r','')
            line = line.split(separator)
            msg_id = line.pop(0)
            if msg_id == 'INV':
                invoice = Invoice()
                invoice.read_INV(line)
            elif msg_id == 'LIN':
                if invoice_line:
                    invoice_line.search_related(invoice)
                invoice_line = InvoiceLine()
                invoice_line.read_LIN(line)
                if not getattr(invoice, 'lines', False):
                    invoice.lines = []
                invoice.lines += (invoice_line,)
            elif 'LIN' in msg_id:
                getattr(invoice_line, 'read_%s' %msg_id)(line)
            elif msg_id in ('NADSCO', 'NADBCO','NADSU', 'NADBY', 'NADII',
                    'NADIV', 'NADDP', 'NADPR', 'NADDL', 'NAD', 'NADPE', 'NADPW',
                    'NADMR'):
                supplier = SupplierEdi()
                getattr(supplier, 'read_%s' %msg_id)(line)
                supplier.search_party()
                if not getattr(invoice, 'suppliers', False):
                    invoice.suppliers = []
                invoice.suppliers += (supplier,)
            elif 'NAD' in msg_id:
                continue
            else:
                getattr(invoice, 'read_%s' %msg_id)(line)

        invoice_line.search_related(invoice)
        return invoice

    def add_attachment(self, attachment, filename=None):
        return
        pool = Pool()
        Attachment = pool.get('ir.attachment')
        if not filename:
            filename = datetime.now().strftime("%y/%m/%d %H:%M:%S")
        attach = Attachment(
            name=filename,
            type='data',
            data=attachment.decode('latin-1').encode('utf8'),
            resource=str(self))
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


    def get_invoice(self):
        pool = Pool()
        Invoice = pool.get('account.invoice')

        invoice = Invoice()
        invoice.currency = Invoice.default_currency()
        invoice.company = self.company
        invoice.party = self.party
        invoice.reference = self.number
        invoice.invoice_date = self.invoice_date
        invoice.type = 'in'
        invoice.party = self.party
        invoice.state = 'draft'
        invoice.on_change_type()
        invoice.on_change_party()
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
    def create_invoices(cls, edi_invoices):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Line = pool.get('account.invoice.line')
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
            for discount in edi_invoice.discounts:
                if discount.percent:
                    continue
                line = edi_invoice.get_discount_invoice_line(discount.discount,
                    discount.amount)
                invoice.lines += (line,)

            invoice.on_change_lines()

            discounts = set((x.type_, x.discount, x.percent) for x in edi_invoice.discounts
                if x.percent)
            for type_, discount, percent in discounts:
                for tax in invoice.taxes:
                    amount = (tax.base*percent*Decimal('0.01')).quantize(Decimal('.01'))
                    if type_ == 'A':
                        amount = amount*-1
                    line = edi_invoice.get_discount_invoice_line(discount, amount,
                        [tax.tax])
                    invoice.lines += (line,)

            invoice.on_change_lines()
            invoice.on_change_type()
            invoice.use_edi = True
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
    quantity = fields.Numeric('Quantity', digits=(16,2))
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
    percent = fields.Numeric('Percent', digits=(16,2))
    tax_amount = fields.Numeric('Tax Amount', digits=(16,2))
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
    code  = fields.Char('Code')
    code_type = fields.Selection([('EAN8', 'EAN8'), ('EAN13', 'EAN13'),
        ('EAN14', 'EAN14'), ('DUN14', 'DUN14')], 'Code Type')
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
    qualifier = fields.Selection([(None, ''), ('F','Free Description')],
        'Qualifier  ')
    quantities = fields.One2Many('invoice.edi.line.quantity', 'line',
        'Quantities')
    delivery_date = fields.Char('Delivery Date')
    base_amount = fields.Numeric('Base Amount', digits=(16,2))
    total_amount = fields.Numeric('Total Amount', digits=(16,2))
    unit_price = fields.Numeric('Unit Price', digits=(16,4))
    gross_price = fields.Numeric('Gross Price', digits=(16,4))
    references = fields.One2Many('invoice.edi.reference',
        'edi_invoice_line', 'References')
    taxes = fields.One2Many('invoice.edi.tax', 'line', 'Taxes')
    discounts = fields.One2Many('invoice.edi.discount',
        'invoice_edi_line', 'Discounts')
    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Function(fields.Numeric('Quantity', digits=(16,4)),
        'invoiced_quantity')

    def search_related(self, edi_invoice):
        pool = Pool()
        Barcode = pool.get('product.code')
        Move = pool.get('stock.move')
        REF = Pool().get('invoice.edi.reference')
        # ('barcode', '=', self.code_type) Remove this from domain after some
        # received
        domain = [('number', '=', self.code)]
        barcode = Barcode.search(domain, limit=1)
        if not barcode:
            return
        product = barcode[0].product
        self.product = product

        purchases = [x.origin for x in edi_invoice.references if
            x.type_ == 'ON' and x.origin]
        self.references = []
        for purchase in purchases:
            for move in purchase.moves:
                if move.state != 'done':
                    continue
                if move.product == product: #TODO: check for quantity?
                    ref = REF()
                    ref.type_ = 'move'
                    ref.origin = 'stock.move,%s'%str(move.id)
                    self.references += (ref,)


    def get_line(self):
        Line = Pool().get('account.invoice.line')
        line = Line()
        line.product = self.product
        line.invoice_type = 'in'
        line.quantity = self.quantity
        line.party = self.edi_invoice.party
        line.type = 'line'
        line.on_change_product()
        line.on_change_account()
        line.gross_unit_price = self.gross_price or self.unit_price
        line.unit_price = self.unit_price
        if self.unit_price and self.gross_price:
            line.discount = Decimal(str(1 -
                self.unit_price/self.gross_price)).quantize(Decimal('.01'))
        else:
            line.unit_price = Decimal(self.base_amount / self.quantity).quantize(
                Decimal('0.0001'))

        line.stock_moves = [x.origin.id for x in self.references if x.origin
            and x.type_ == 'move']
        return line

    def invoiced_quantity(self, name):
        for q in self.quantities:
            if q.type_ == '47':
                return q.quantity
        return Decimal('0')

    def read_LIN(self, message):
        self.code = message.pop(0)
        self.code_type = message.pop(0)
        if self.code_type == 'EN':
            self.code_type = 'EAN8'
        if message:
            self.sequence = int(message.pop(0))


    def read_PIALIN(self, message):
        self.supplier_code = message.pop(0)
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
        self.description = message.pop(0)
        self.characteristic = message.pop(0)
        self.qualifier = message.pop(0)

    def read_QTYLIN(self, message):
        QTY = Pool().get('invoice.edi.line.quantity')
        qty = QTY()
        qty.type_ = message.pop(0)
        qty.quantity = to_decimal(message.pop(0), 4)
        if qty.type_ == '47':
            self.quantity = qty.quantity
        if message:
            qty.uom = message.pop(0)
        if not getattr(self, 'quantities', False):
            self.quantities = []
        self.quantities += (qty,)

    def read_DTMLINE(self, message):
        self.delivery_date = to_date(message.pop(0))

    def read_MOALIN(self, message):
        self.base_amount = to_decimal(message.pop(0))
        if message:
            self.total_amount = to_decimal(message.pop(0))

    def read_PRILIN(self, message):
        type_ = message.pop(0)
        if type_  == 'AAA':
            self.unit_price = to_decimal(message.pop(0), 4)
        elif type_ == 'AAB':
            self.gross_price = to_decimal(message.pop(0), 4)

    def read_RFFLIN(self, message):
        REF = Pool().get('invoice.edi.reference')
        ref = REF()
        ref.type_ = message.pop(0)
        ref.value = message.pop(0)
        ref.search_reference()
        if message:
            ref.line_number = message.pop(0)
        if not getattr(self, 'references', False):
            self.references = []
        self.references += (ref,)

    def read_TAXLIN(self, message):
        Tax = Pool().get('invoice.edi.tax')
        tax = Tax()
        tax.type_ = message.pop(0)
        tax.percent = to_decimal(message.pop(0))
        if message:
            tax.tax_amount = to_decimal(message.pop(0))
        if not getattr(self, 'taxes', False):
            self.taxes = []
        self.taxes += (tax,)


    def read_ALCLIN(self, message):
        Discount =  Pool().get('invoice.edi.discount')
        discount = Discount()
        discount.type_ = message.pop(0)
        discount.sequence = int(message.pop(0) or 0)
        discount.discount = message.pop(0)
        discount.percent = to_decimal(message.pop(0))
        discount.amount = to_decimal(message.pop(0))
        if not getattr(self, 'discounts', False):
            self.discounts = []
        self.discounts += (discount,)


class Invoice:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice'

    use_edi = fields.Boolean('Use EDI',
        help='Use EDI protocol for this purchase', states={
            'readonly': Or(~Bool(Eval('party')), Bool(Eval('edi_state')))})
    edi_invoices = fields.One2Many('invoice.edi', 'invoice',
        'Edi Invoices')

    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()
        cls._error_messages.update({
            'confirm_invoice_with_difference': (
                'You try to post invoices "%(invoices)s" with diferences with '
                ' recived edi invoices')
        })

    @classmethod
    def post(cls, invoices):
        super(Invoice, cls).post(invoices)
        differences = []
        for invoice in invoices:
            if invoice.type == 'out' or not invoice.use_edi:
                continue
            if not invoice.edi_invoices:
                continue
            edi_invoice = invoice.edi_invoices[-1]
            if edi_invoice.differences_state == 'difference':
                differences.append(invoice)

        if differences:
            cls.raise_user_warning(
                'confirm_invoice_with_difference_%s' % (
                    "_".join([str(x.id) for x in differences])),
                'confirm_invoice_with_difference', {
                    'invoices': ",".join([x.reference for x in differences])
                })
