# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import invoice
from . import sale

def register():
    Pool.register(
        invoice.Cron,
        invoice.InvoiceEdiConfiguration,
        invoice.InvoiceEdi,
        invoice.InvoiceEdiLine,
        invoice.SupplierEdi,
        invoice.InvoiceEdiReference,
        invoice.InvoiceEdiMaturityDates,
        invoice.InvoiceEdiDiscount,
        invoice.InvoiceEdiLineQty,
        invoice.InvoiceEdiTax,
        invoice.Invoice,
        module='account_invoice_edi', type_='model')
    Pool.register(
        sale.Sale,
        module='account_invoice_edi', type_='model',
        depends=['sale', 'sale_edi_ediversa'])