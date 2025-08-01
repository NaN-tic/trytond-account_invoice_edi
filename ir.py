# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta


class Cron(metaclass=PoolMeta):
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.method.selection.extend([
            ('invoice.edi|import_edi_files', 'Import Edi Invoices'),
            ('account.invoice|run_generate_edi_file', 'Generate Edi Invoices'),
        ])
