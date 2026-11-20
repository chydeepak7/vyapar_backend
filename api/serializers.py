from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    BusinessProfile, Party, Item, Transaction, TransactionLine,
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
        user.save()
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


class ItemSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    unit_detail = UnitSerializer(source='unit', read_only=True)

    class Meta:
        model = Item
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Provide convenient string fields so frontend forms work without change
        rep['category_name'] = instance.category.name if instance.category else instance.category_name
        rep['unit_name'] = instance.unit.short_name if instance.unit else instance.unit_name
        return rep


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
        ]


class TransactionSerializer(serializers.ModelSerializer):
    lines = TransactionLineSerializer(many=True, required=False)
    party_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Transaction
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        transaction = Transaction.objects.create(**validated_data)
        for line_data in lines_data:
            TransactionLine.objects.create(transaction=transaction, **line_data)
        self._update_stock(transaction, lines_data, create=True)
        return transaction

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)

        # Restore stock from old lines before update
        self._update_stock(instance, list(instance.lines.values()), create=False, restore=True)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                TransactionLine.objects.create(transaction=instance, **line_data)
            self._update_stock(instance, lines_data, create=True)

        return instance

    def _update_stock(self, transaction, lines_data, create=False, restore=False):
        """Adjust item stock based on transaction lines."""
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
            qty = Decimal(line_data.get('qty', 0))
            if restore:
                # Revert previous effect
                delta = qty if transaction.type == 'SaleInvoice' else -qty
            elif create:
                delta = -qty if transaction.type == 'SaleInvoice' else qty
            else:
                continue
            item.stock += delta
            item.save()


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}


class OtherIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherIncome
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}


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
