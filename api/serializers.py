from rest_framework import serializers
from .models import (
    BusinessProfile, Party, Item, Transaction, TransactionLine,
    Expense, OtherIncome, BankAccount, Settings,
)


class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = '__all__'


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


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


class OtherIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherIncome
        fields = '__all__'


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'
