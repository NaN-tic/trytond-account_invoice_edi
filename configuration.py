# -*- coding: utf-8 -*
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton


class InvoiceEdiConfiguration(ModelSingleton, ModelSQL, ModelView):
    'Invoice Edi Configuration'
    __name__ = 'invoice.edi.configuration'

    edi_files_path = fields.Char('EDI Invoice Inbox Path')
    outbox_path_edi = fields.Char('EDI Invoice Outbox Path')
    separator = fields.Char('Separator')
    automatic_edi_invoice_out = fields.Boolean('Send EDI file automatically')
    edi_invoice_file_path = fields.Char("EDI Invoice File Path")
    discount_products = fields.Many2Many(
        'invoice.edi.configuration-product.discount', 'configuration',
        'product', 'Discount Products')
    no_edi_products = fields.Many2Many(
        'invoice.edi.configuration-product.no_edi', 'configuration',
        'product', 'No EDI Products')

    @classmethod
    def default_separator(cls):
        return '|'

    @classmethod
    def default_automatic_edi_invoice_out(cls):
        return True


class InvoiceEdiConfigurationDiscountProduct(ModelSQL):
    'Invoice EDI Configuration - Discount Product'
    __name__ = 'invoice.edi.configuration-product.discount'

    configuration = fields.Many2One(
        'invoice.edi.configuration', 'Configuration', required=True,
        ondelete='CASCADE')
    product = fields.Many2One(
        'product.product', 'Product', required=True, ondelete='RESTRICT')


class InvoiceEdiConfigurationNoEdiProduct(ModelSQL):
    'Invoice EDI Configuration - No EDI Product'
    __name__ = 'invoice.edi.configuration-product.no_edi'

    configuration = fields.Many2One(
        'invoice.edi.configuration', 'Configuration', required=True,
        ondelete='CASCADE')
    product = fields.Many2One(
        'product.product', 'Product', required=True, ondelete='RESTRICT')
