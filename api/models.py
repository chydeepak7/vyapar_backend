from django.db import models


# ============ Master Setup Models ============

class Category(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class ItemUnitConversion(models.Model):
    """
    Alternate unit for an item with a conversion factor to the item's base unit.
    Example: 1 Carton = 12 Pieces  →  unit_name='Carton', conversion_factor=12
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='unit_conversions')
    unit_name = models.CharField(max_length=50, help_text='e.g. Carton, Box, Dozen, Bag')
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=4, default=1,
        help_text='1 of this unit = how many base units (e.g. 1 Carton = 12 pcs → 12)',
    )
    purchase_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    sale_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)

    class Meta:
        ordering = ['unit_name']
        unique_together = [('item', 'unit_name')]

    def __str__(self):
        return f'{self.item.name} – {self.unit_name} (×{self.conversion_factor})'


class Unit(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50, unique=True)   # e.g. "Pieces"
    short_name = models.CharField(max_length=20, unique=True)  # e.g. "PCS"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.short_name} – {self.name}'


class Warehouse(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ItemUnitConversion(models.Model):
    """
    Alternate unit for an item with a conversion factor to the item's base unit.
    Example: 1 Carton = 12 Pieces  →  unit_name='Carton', conversion_factor=12
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='unit_conversions')
    unit_name = models.CharField(max_length=50, help_text='e.g. Carton, Box, Dozen, Bag')
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=4, default=1,
        help_text='1 of this unit = how many base units (e.g. 1 Carton = 12 pcs → 12)',
    )
    purchase_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    sale_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)

    class Meta:
        ordering = ['unit_name']
        unique_together = [('item', 'unit_name')]

    def __str__(self):
        return f'{self.item.name} – {self.unit_name} (×{self.conversion_factor})'


class BusinessProfile(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
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


class ItemUnitConversion(models.Model):
    """
    Alternate unit for an item with a conversion factor to the item's base unit.
    Example: 1 Carton = 12 Pieces  →  unit_name='Carton', conversion_factor=12
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='unit_conversions')
    unit_name = models.CharField(max_length=50, help_text='e.g. Carton, Box, Dozen, Bag')
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=4, default=1,
        help_text='1 of this unit = how many base units (e.g. 1 Carton = 12 pcs → 12)',
    )
    purchase_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    sale_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)

    class Meta:
        ordering = ['unit_name']
        unique_together = [('item', 'unit_name')]

    def __str__(self):
        return f'{self.item.name} – {self.unit_name} (×{self.conversion_factor})'


class Party(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
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
    opening_balance = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    balance_type = models.CharField(max_length=20, choices=BALANCE_TYPES, default='To Receive')
    group = models.CharField(max_length=100, blank=True)
    credit_limit = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    payment_terms = models.CharField(max_length=100, blank=True)  # e.g. "Net 30"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ItemUnitConversion(models.Model):
    """
    Alternate unit for an item with a conversion factor to the item's base unit.
    Example: 1 Carton = 12 Pieces  →  unit_name='Carton', conversion_factor=12
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='unit_conversions')
    unit_name = models.CharField(max_length=50, help_text='e.g. Carton, Box, Dozen, Bag')
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=4, default=1,
        help_text='1 of this unit = how many base units (e.g. 1 Carton = 12 pcs → 12)',
    )
    purchase_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    sale_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)

    class Meta:
        ordering = ['unit_name']
        unique_together = [('item', 'unit_name')]

    def __str__(self):
        return f'{self.item.name} – {self.unit_name} (×{self.conversion_factor})'


class Item(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='items',
    )
    category_name = models.CharField(max_length=100, blank=True)  # denormalised fallback
    hsn = models.CharField(max_length=20, blank=True)
    unit = models.ForeignKey(
        Unit, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='items',
    )
    unit_name = models.CharField(max_length=20, blank=True)  # denormalised fallback
    sale_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    purchase_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    gst_rate = models.DecimalField(max_digits=15, decimal_places=10, default=0)
    stock = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    min_stock = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    barcode = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    mrp = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ItemUnitConversion(models.Model):
    """
    Alternate unit for an item with a conversion factor to the item's base unit.
    Example: 1 Carton = 12 Pieces  →  unit_name='Carton', conversion_factor=12
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='unit_conversions')
    unit_name = models.CharField(max_length=50, help_text='e.g. Carton, Box, Dozen, Bag')
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=4, default=1,
        help_text='1 of this unit = how many base units (e.g. 1 Carton = 12 pcs → 12)',
    )
    purchase_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    sale_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)

    class Meta:
        ordering = ['unit_name']
        unique_together = [('item', 'unit_name')]

    def __str__(self):
        return f'{self.item.name} – {self.unit_name} (×{self.conversion_factor})'


class Transaction(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
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
    sub_total = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    discount_amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    additional_charges = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    round_off = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    cgst = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    sgst = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    igst = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    cess = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    total_amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    paid_amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    balance_amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
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
    qty = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    free_qty = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    unit = models.CharField(max_length=20, blank=True)
    rate = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    discount_percent = models.DecimalField(max_digits=15, decimal_places=10, default=0)
    gst_rate = models.DecimalField(max_digits=15, decimal_places=10, default=0)
    amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    # Conversion: how many base-unit stock items does 1 qty of `unit` equal?
    # e.g. if unit=Carton and 1 Carton = 12 pcs → conversion_factor=12
    conversion_factor = models.DecimalField(max_digits=15, decimal_places=4, default=1)

    def __str__(self):
        return f'{self.item_name} x {self.qty}'


class Expense(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    PAYMENT_TYPES = [
        ('Cash', 'Cash'), ('Cheque', 'Cheque'),
        ('UPI', 'UPI'), ('Bank Transfer', 'Bank Transfer'),
    ]
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='Cash')
    note = models.TextField(blank=True)
    gst_amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    is_gst = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.category} - {self.amount}'


class OtherIncome(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    PAYMENT_TYPES = [
        ('Cash', 'Cash'), ('Cheque', 'Cheque'),
        ('UPI', 'UPI'), ('Bank Transfer', 'Bank Transfer'),
    ]
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='Cash')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.category} - {self.amount}'


class BankAccount(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
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
    opening_balance = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ItemUnitConversion(models.Model):
    """
    Alternate unit for an item with a conversion factor to the item's base unit.
    Example: 1 Carton = 12 Pieces  →  unit_name='Carton', conversion_factor=12
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='unit_conversions')
    unit_name = models.CharField(max_length=50, help_text='e.g. Carton, Box, Dozen, Bag')
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=4, default=1,
        help_text='1 of this unit = how many base units (e.g. 1 Carton = 12 pcs → 12)',
    )
    purchase_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    sale_price = models.DecimalField(max_digits=24, decimal_places=10, default=0)

    class Meta:
        ordering = ['unit_name']
        unique_together = [('item', 'unit_name')]

    def __str__(self):
        return f'{self.item.name} – {self.unit_name} (×{self.conversion_factor})'


class Settings(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
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


class OpeningStock(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='opening_stocks')
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='opening_stocks',
    )
    quantity = models.DecimalField(max_digits=24, decimal_places=10, default=0)
    rate = models.DecimalField(max_digits=24, decimal_places=10, default=0)   # purchase/cost price at time of entry
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.item.name} – {self.quantity}'
