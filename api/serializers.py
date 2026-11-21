from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    BusinessProfile, Party, Item, ItemUnitConversion,
    Transaction, TransactionLine, PaymentLine,
    Expense, OtherIncome, BankAccount, Settings,
    Category, Unit, Warehouse, OpeningStock,
)


# ============ User Serializers ============
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_superuser', 'is_active', 'date_joined']


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'is_superuser']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_staff = validated_data.get('is_superuser', False)
        user.save()
        # Bootstrap default Settings + BusinessProfile for the new user
        from .models import BusinessProfile, Settings
        BusinessProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': 'My Business',
                'currency': '₹',
                'decimal_places': 2,
            },
        )
        Settings.objects.get_or_create(
            user=user,
            defaults={
                'tax_rates': [0, 5, 12, 18, 28],
                'invoice_prefix': 'INV',
                'purchase_prefix': 'PUR',
                'estimate_prefix': 'EST',
                'payment_in_prefix': 'PIN',
                'payment_out_prefix': 'POU',
                'credit_note_prefix': 'CN',
                'debit_note_prefix': 'DN',
                'default_payment_terms': '30',
                'enable_gst': True,
                'inclusive_tax': False,
                'round_off': True,
                'invoice_theme': 'classic',
                'print_company_info': True,
                'print_terms': True,
            },
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'user', 'name', 'description', 'created_at', 'item_count']
        extra_kwargs = {'user': {'read_only': True}}

    def get_item_count(self, obj):
        return obj.items.count()


class UnitSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = ['id', 'user', 'name', 'short_name', 'created_at', 'item_count']
        extra_kwargs = {'user': {'read_only': True}}

    def get_item_count(self, obj):
        return obj.items.count()


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}


class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}


class ItemUnitConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemUnitConversion
        fields = ['id', 'unit_name', 'conversion_factor', 'purchase_price', 'sale_price']


class ItemSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    unit_detail = UnitSerializer(source='unit', read_only=True)
    unit_conversions = ItemUnitConversionSerializer(many=True, required=False)

    class Meta:
        model = Item
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['category_name'] = instance.category.name if instance.category else instance.category_name
        rep['unit_name'] = instance.unit.short_name if instance.unit else instance.unit_name
        return rep

    def _save_conversions(self, item, conversions_data, user):
        # Replace all conversions for this item
        item.unit_conversions.all().delete()
        for c in conversions_data:
            ItemUnitConversion.objects.create(item=item, user=user, **c)

    def create(self, validated_data):
        conversions_data = validated_data.pop('unit_conversions', [])
        item = Item.objects.create(**validated_data)
        self._save_conversions(item, conversions_data, validated_data.get('user'))
        return item

    def update(self, instance, validated_data):
        conversions_data = validated_data.pop('unit_conversions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if conversions_data is not None:
            self._save_conversions(instance, conversions_data, instance.user)
        return instance


class OpeningStockSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True, allow_null=True)

    class Meta:
        model = OpeningStock
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}


class TransactionLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(required=False, allow_blank=True)
    hsn = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = TransactionLine
        fields = [
            'id', 'item', 'item_name', 'hsn', 'qty', 'free_qty',
            'unit', 'rate', 'discount_percent', 'gst_rate', 'amount',
            'conversion_factor',
        ]


class PaymentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLine
        fields = ['id', 'payment_type', 'amount', 'reference_no', 'bank_account', 'date']


class TransactionSerializer(serializers.ModelSerializer):
    lines = TransactionLineSerializer(many=True, required=False)
    party_name = serializers.CharField(required=False, allow_blank=True)
    payment_lines = PaymentLineSerializer(many=True, required=False)

    class Meta:
        model = Transaction
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Synthesize payment_lines for legacy transactions that have none
        if not rep.get('payment_lines'):
            paid = instance.paid_amount or 0
            if paid and paid > 0:
                rep['payment_lines'] = [{
                    'id': None,
                    'payment_type': instance.payment_type or 'Cash',
                    'amount': str(paid),
                    'reference_no': instance.payment_mode or '',
                    'bank_account': None,
                    'date': str(instance.date) if instance.date else None,
                }]
        return rep

    def create(self, validated_data):
        from decimal import Decimal
        lines_data = validated_data.pop('lines', [])
        payment_lines_data = validated_data.pop('payment_lines', None)

        # Auto-compute paid_amount from payment_lines if provided
        if payment_lines_data is not None:
            validated_data['paid_amount'] = sum(
                (Decimal(str(pl.get('amount', 0))) for pl in payment_lines_data),
                Decimal(0),
            )
            total = validated_data.get('total_amount', Decimal(0))
            validated_data['balance_amount'] = max(
                Decimal(0), total - validated_data['paid_amount'],
            )

        transaction = Transaction.objects.create(**validated_data)
        for line_data in lines_data:
            TransactionLine.objects.create(transaction=transaction, **line_data)
        self._update_stock(transaction, lines_data, create=True)

        if payment_lines_data is not None:
            for pl_data in payment_lines_data:
                PaymentLine.objects.create(transaction=transaction, **pl_data)

        return transaction

    def update(self, instance, validated_data):
        from decimal import Decimal
        lines_data = validated_data.pop('lines', None)
        payment_lines_data = validated_data.pop('payment_lines', None)

        # Restore stock from old lines before update
        self._update_stock(instance, list(instance.lines.values()), create=False, restore=True)

        # Auto-compute paid_amount from payment_lines if provided
        if payment_lines_data is not None:
            validated_data['paid_amount'] = sum(
                (Decimal(str(pl.get('amount', 0))) for pl in payment_lines_data),
                Decimal(0),
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if payment_lines_data is not None:
            total = instance.total_amount or Decimal(0)
            instance.balance_amount = max(Decimal(0), total - instance.paid_amount)

        instance.save()

        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                TransactionLine.objects.create(transaction=instance, **line_data)
            self._update_stock(instance, lines_data, create=True)

        if payment_lines_data is not None:
            instance.payment_lines.all().delete()
            for pl_data in payment_lines_data:
                PaymentLine.objects.create(transaction=instance, **pl_data)

        return instance

    def _update_stock(self, transaction, lines_data, create=False, restore=False):
        """Adjust item stock based on transaction lines.
        Uses conversion_factor so that selling 2 Cartons (factor=12) deducts 24 base units.
        """
        from decimal import Decimal
        if transaction.type not in ('SaleInvoice', 'PurchaseBill'):
            return
        for line_data in lines_data:
            item_id = line_data.get('item')
            if not item_id:
                continue
            try:
                item = Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                continue
            qty = Decimal(str(line_data.get('qty', 0)))
            factor = Decimal(str(line_data.get('conversion_factor', 1)))
            base_qty = qty * factor   # actual stock units affected
            if restore:
                delta = base_qty if transaction.type == 'SaleInvoice' else -base_qty
            elif create:
                delta = -base_qty if transaction.type == 'SaleInvoice' else base_qty
            else:
                continue
            item.stock += delta
            item.save()


class ExpenseSerializer(serializers.ModelSerializer):
    payment_lines = PaymentLineSerializer(many=True, required=False)

    class Meta:
        model = Expense
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not rep.get('payment_lines'):
            if instance.amount and instance.amount > 0:
                rep['payment_lines'] = [{
                    'id': None,
                    'payment_type': instance.payment_type or 'Cash',
                    'amount': str(instance.amount),
                    'reference_no': '',
                    'bank_account': None,
                    'date': str(instance.date) if instance.date else None,
                }]
        return rep

    def create(self, validated_data):
        payment_lines_data = validated_data.pop('payment_lines', None)
        if payment_lines_data:
            validated_data['payment_type'] = payment_lines_data[0].get('payment_type', 'Cash')
        expense = Expense.objects.create(**validated_data)
        if payment_lines_data:
            for pl_data in payment_lines_data:
                PaymentLine.objects.create(expense=expense, **pl_data)
        return expense

    def update(self, instance, validated_data):
        payment_lines_data = validated_data.pop('payment_lines', None)
        if payment_lines_data:
            validated_data['payment_type'] = payment_lines_data[0].get('payment_type', 'Cash')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if payment_lines_data is not None:
            instance.payment_lines.all().delete()
            for pl_data in payment_lines_data:
                PaymentLine.objects.create(expense=instance, **pl_data)
        return instance


class OtherIncomeSerializer(serializers.ModelSerializer):
    payment_lines = PaymentLineSerializer(many=True, required=False)

    class Meta:
        model = OtherIncome
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not rep.get('payment_lines'):
            if instance.amount and instance.amount > 0:
                rep['payment_lines'] = [{
                    'id': None,
                    'payment_type': instance.payment_type or 'Cash',
                    'amount': str(instance.amount),
                    'reference_no': '',
                    'bank_account': None,
                    'date': str(instance.date) if instance.date else None,
                }]
        return rep

    def create(self, validated_data):
        payment_lines_data = validated_data.pop('payment_lines', None)
        if payment_lines_data:
            validated_data['payment_type'] = payment_lines_data[0].get('payment_type', 'Cash')
        income = OtherIncome.objects.create(**validated_data)
        if payment_lines_data:
            for pl_data in payment_lines_data:
                PaymentLine.objects.create(other_income=income, **pl_data)
        return income

    def update(self, instance, validated_data):
        payment_lines_data = validated_data.pop('payment_lines', None)
        if payment_lines_data:
            validated_data['payment_type'] = payment_lines_data[0].get('payment_type', 'Cash')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if payment_lines_data is not None:
            instance.payment_lines.all().delete()
            for pl_data in payment_lines_data:
                PaymentLine.objects.create(other_income=instance, **pl_data)
        return instance


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}
