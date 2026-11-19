from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from api.models import (
    BusinessProfile, Party, Item, Transaction, TransactionLine,
    BankAccount, Settings, Expense, OtherIncome,
)


class Command(BaseCommand):
    help = 'Seed the database with sample Vyapar data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding database...'))

        Transaction.objects.all().delete()
        Item.objects.all().delete()
        Party.objects.all().delete()
        BankAccount.objects.all().delete()
        Settings.objects.all().delete()
        BusinessProfile.objects.all().delete()
        Expense.objects.all().delete()
        OtherIncome.objects.all().delete()

        BusinessProfile.objects.create(
            name='My Business', phone='+91 98765 43210', email='business@example.com',
            address='123 Main Street, City, State - 560001', gstin='29ABCDE1234F1Z5',
            state='Karnataka', currency='₹', decimal_places=2,
        )

        Settings.objects.create(
            tax_rates=[0, 5, 12, 18, 28], invoice_prefix='INV', purchase_prefix='PUR',
            estimate_prefix='EST', payment_in_prefix='PIN', payment_out_prefix='POU',
            credit_note_prefix='CN', debit_note_prefix='DN', default_payment_terms='30',
            enable_gst=True, inclusive_tax=False, round_off=True, invoice_theme='classic',
        )

        BankAccount.objects.create(name='Cash in Hand', type='Cash', opening_balance=50000)
        BankAccount.objects.create(name='HDFC Bank', type='Bank', bank_name='HDFC',
                                   account_number='1234567890', ifsc='HDFC0001234', opening_balance=100000)

        ramesh = Party.objects.create(name='Ramesh Traders', type='Customer', phone='+91 90000 11111',
            email='ramesh@example.com', gstin='29AAAAA0000A1Z1', group='Wholesale',
            billing_address='MG Road, Bengaluru, Karnataka')
        sharma = Party.objects.create(name='Sharma Suppliers', type='Supplier', phone='+91 90000 22222',
            email='sharma@example.com', gstin='29BBBBB1111B1Z2', group='Wholesale',
            billing_address='Commercial Street, Bengaluru, Karnataka',
            opening_balance=Decimal('5000'), balance_type='To Pay')
        walkin = Party.objects.create(name='Walk-in Customer', type='Customer', group='Retail')

        cement = Item.objects.create(name='Cement Bag 50kg', category='Construction', hsn='2523',
            unit='BAG', sale_price=380, purchase_price=340, gst_rate=28, stock=120, min_stock=20, mrp=420)
        steel = Item.objects.create(name='Steel Rod 12mm', category='Construction', hsn='7213',
            unit='MTR', sale_price=85, purchase_price=72, gst_rate=18, stock=500, min_stock=50)
        bricks = Item.objects.create(name='Bricks (100 pcs)', category='Construction', hsn='6901',
            unit='BOX', sale_price=6500, purchase_price=5500, gst_rate=5, stock=30, min_stock=5)
        paint = Item.objects.create(name='Paint 20L White', category='Paint', hsn='3208',
            unit='PCS', sale_price=2400, purchase_price=1950, gst_rate=18, stock=45, min_stock=10, mrp=2800)
        sand = Item.objects.create(name='Sand (1 unit)', category='Construction', hsn='2505',
            unit='KG', sale_price=45, purchase_price=30, gst_rate=5, stock=0, min_stock=100)

        today = date.today()

        inv1 = Transaction.objects.create(type='SaleInvoice', invoice_no='INV-001', party=ramesh,
            party_name='Ramesh Traders', date=today - timedelta(days=20),
            due_date=today - timedelta(days=20) + timedelta(days=30),
            sub_total=Decimal('11637.50'), cgst=Decimal('1285.69'), sgst=Decimal('1285.69'),
            total_amount=Decimal('14208.88'), paid_amount=Decimal('10000'),
            balance_amount=Decimal('4208.88'), payment_type='Credit',
            terms='Payment due within 30 days', is_gst=True)
        TransactionLine.objects.create(transaction=inv1, item=cement, item_name='Cement Bag 50kg',
            hsn='2523', qty=20, unit='BAG', rate=380, gst_rate=28, amount=Decimal('7600'))
        TransactionLine.objects.create(transaction=inv1, item=steel, item_name='Steel Rod 12mm',
            hsn='7213', qty=50, unit='MTR', rate=85, discount_percent=5, gst_rate=18, amount=Decimal('4037.50'))

        inv2 = Transaction.objects.create(type='SaleInvoice', invoice_no='INV-002', party=walkin,
            party_name='Walk-in Customer', date=today - timedelta(days=10),
            sub_total=Decimal('4800'), cgst=Decimal('432'), sgst=Decimal('432'),
            total_amount=Decimal('5664'), paid_amount=Decimal('5664'), payment_type='Cash', is_gst=True)
        TransactionLine.objects.create(transaction=inv2, item=paint, item_name='Paint 20L White',
            hsn='3208', qty=2, unit='PCS', rate=2400, gst_rate=18, amount=Decimal('4800'))

        pur1 = Transaction.objects.create(type='PurchaseBill', invoice_no='PUR-001', party=sharma,
            party_name='Sharma Suppliers', date=today - timedelta(days=15),
            sub_total=Decimal('17000'), additional_charges=Decimal('500'),
            cgst=Decimal('2450'), sgst=Decimal('2450'),
            total_amount=Decimal('22400'), paid_amount=Decimal('15000'),
            balance_amount=Decimal('7400'), payment_type='Credit', is_gst=True)
        TransactionLine.objects.create(transaction=pur1, item=cement, item_name='Cement Bag 50kg',
            hsn='2523', qty=50, unit='BAG', rate=340, gst_rate=28, amount=Decimal('17000'))

        Expense.objects.create(category='Office Rent', amount=Decimal('2500'),
            date=today - timedelta(days=10), payment_type='Cash', note='Monthly rent')
        OtherIncome.objects.create(category='Interest', amount=Decimal('1500'),
            date=today - timedelta(days=10), payment_type='Bank Transfer', note='Bank interest')

        self.stdout.write(self.style.SUCCESS('Seed complete!'))
        self.stdout.write('  1 Business, 3 Parties, 5 Items, 3 Transactions, 1 Expense, 1 Income, 2 Accounts, 1 Settings')
