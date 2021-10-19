from trytond.pool import PoolMeta


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    def create_invoice(self):
        invoice = super().create_invoice()
        if invoice and self.edi:
            invoice.is_edi = True
            if self.reference and self.number:
                invoice.reference = self.reference + '-' + self.number
            invoice.save()
        return invoice