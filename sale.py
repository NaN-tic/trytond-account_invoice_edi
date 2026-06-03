from trytond.pool import PoolMeta


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    def create_invoice(self):
        invoice = super().create_invoice()
        if not invoice:
            return invoice
        if self.is_edi:
            invoice.is_edi = True
            if self.reference and self.number:
                invoice.reference = self.reference + '-' + self.number
        invoice.set_edi_defaults_from_party()
        if self.is_edi or invoice._party_forces_edi_invoice():
            invoice.save()
        return invoice
