from django.db import models


class BusinessProfile(models.Model):
    name = models.CharField(max_length=255, default='My Business')
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    state = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    currency = models.CharField(max_length=10, default='₹')
    decimal_places = models.IntegerField(default=2)
    financial_year_start = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Business Profile'

    def __str__(self):
        return self.name


class Party(models.Model):
    PARTY_TYPES = [
        ('Customer', 'Customer'),
        ('Supplier', 'Supplier'),
        ('Both', 'Both'),
    ]
    BALANCE_TYPES = [
        ('To Receive', 'To Receive'),
        ('To Pay', 'To Pay'),
    ]
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=PARTY_TYPES, default='Customer')
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_type = models.CharField(max_length=20, choices=BALANCE_TYPES, default='To Receive')
    group = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    UNIT_CHOICES = [
        ('PCS', 'PCS'), ('KG', 'KG'), ('LTR', 'LTR'), ('MTR', 'MTR'),
        ('BOX', 'BOX'), ('SET', 'SET'), ('NOS', 'NOS'), ('PAIR', 'PAIR'),
        ('ROLL', 'ROLL'), ('BAG', 'BAG'),
    ]
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    hsn = models.CharField(max_length=20, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='PCS')
    sale_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    barcode = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    mrp = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TXN_TYPES = [
        ('SaleInvoice', 'Sale Invoice'),
        ('PurchaseBill', 'Purchase Bill'),
        ('PaymentIn', 'Payment In'),
        ('PaymentOut', 'Payment Out'),
        ('SaleReturn', 'Sale Return'),
        ('PurchaseReturn', 'Purchase Return'),
        ('Estimate', 'Estimate'),
        ('DeliveryChallan', 'Delivery Challan'),
        ('SaleOrder', 'Sale Order'),
        ('PurchaseOrder', 'Purchase Order'),
    ]
    PAYMENT_TYPES = [
        ('Cash', 'Cash'),
        ('Cheque', 'Cheque'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Credit', 'Credit'),
    ]
    type = models.CharField(max_length=30, choices=TXN_TYPES)
    invoice_no = models.CharField(max_length=50)
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True)
    party_name = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    sub_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    additional_charges = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    round_off = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cess = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='Credit')
    payment_mode = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    transport_details = models.TextField(blank=True)
    state_of_supply = models.CharField(max_length=100, blank=True)
    reverse_charge = models.BooleanField(default=False)
    is_gst = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.invoice_no} - {self.party_name}'


class TransactionLine(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=255, blank=True)
    hsn = models.CharField(max_length=20, blank=True)
    qty = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    free_qty = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, blank=True)
    rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.item_name} x {self.qty}'


class Expense(models.Model):
    PAYMENT_TYPES = [
        ('Cash', 'Cash'), ('Cheque', 'Cheque'),
        ('UPI', 'UPI'), ('Bank Transfer', 'Bank Transfer'),
    ]
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='Cash')
    note = models.TextField(blank=True)
    gst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_gst = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.category} - {self.amount}'


class OtherIncome(models.Model):
    PAYMENT_TYPES = [
        ('Cash', 'Cash'), ('Cheque', 'Cheque'),
        ('UPI', 'UPI'), ('Bank Transfer', 'Bank Transfer'),
    ]
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='Cash')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.category} - {self.amount}'


class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ('Bank', 'Bank'), ('Cash', 'Cash'),
        ('Wallet', 'Wallet'), ('Loan', 'Loan'),
    ]
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='Bank')
    bank_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    branch = models.CharField(max_length=255, blank=True)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Settings(models.Model):
    tax_rates = models.JSONField(default=list)
    invoice_prefix = models.CharField(max_length=20, default='INV')
    purchase_prefix = models.CharField(max_length=20, default='PUR')
    estimate_prefix = models.CharField(max_length=20, default='EST')
    payment_in_prefix = models.CharField(max_length=20, default='PIN')
    payment_out_prefix = models.CharField(max_length=20, default='POU')
    credit_note_prefix = models.CharField(max_length=20, default='CN')
    debit_note_prefix = models.CharField(max_length=20, default='DN')
    default_payment_terms = models.CharField(max_length=50, default='30')
    enable_gst = models.BooleanField(default=True)
    inclusive_tax = models.BooleanField(default=False)
    round_off = models.BooleanField(default=True)
    invoice_theme = models.CharField(max_length=50, default='classic')
    print_company_info = models.BooleanField(default=True)
    print_terms = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Settings'

    def __str__(self):
        return 'App Settings'
