# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import ir
from . import invoice
from . import sale
from . import configuration
from . import company


def register():
    Pool.register(
        ir.Cron,
        invoice.InvoiceEdi,
        invoice.InvoiceEdiLine,
        invoice.SupplierEdi,
        invoice.InvoiceEdiReference,
        invoice.InvoiceEdiMaturityDates,
        invoice.InvoiceEdiDiscount,
        invoice.InvoiceEdiLineQty,
        invoice.InvoiceEdiTax,
        invoice.Invoice,
        invoice.InvoiceLine,
        configuration.InvoiceEdiConfiguration,
        company.Company,
        module='account_invoice_edi', type_='model')
    Pool.register(
        sale.Sale,
        module='account_invoice_edi', type_='model',
        depends=['sale', 'sale_edi_ediversa'])
