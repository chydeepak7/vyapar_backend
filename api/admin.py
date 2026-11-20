from django.contrib import admin
from .models import (
    BusinessProfile, Party, Item, Transaction, TransactionLine,
    Expense, OtherIncome, BankAccount, Settings,
    Category, Unit, Warehouse, OpeningStock,
)


class TransactionLineInline(admin.TabularInline):
    model = TransactionLine
    extra = 1


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'gstin', 'state')


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'phone', 'gstin', 'group')
    list_filter = ('type', 'group')
    search_fields = ('name', 'phone', 'gstin')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'hsn', 'unit', 'sale_price', 'stock', 'min_stock', 'gst_rate')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'hsn', 'barcode')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', 'type', 'party_name', 'date', 'total_amount', 'balance_amount')
    list_filter = ('type', 'payment_type')
    search_fields = ('invoice_no', 'party_name')
    inlines = [TransactionLineInline]
    date_hierarchy = 'date'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'payment_type')
    list_filter = ('category', 'payment_type')


@admin.register(OtherIncome)
class OtherIncomeAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'payment_type')
    list_filter = ('category', 'payment_type')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'bank_name', 'opening_balance')


admin.site.register(Settings)
admin.site.register(TransactionLine)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name')
    search_fields = ('name', 'short_name')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'is_default')
    list_filter = ('is_default',)


@admin.register(OpeningStock)
class OpeningStockAdmin(admin.ModelAdmin):
    list_display = ('item', 'warehouse', 'quantity', 'rate', 'date')
    list_filter = ('warehouse', 'date')
    search_fields = ('item__name',)
