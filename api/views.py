from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta

from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User

from .models import (
    BusinessProfile, Party, Item, ItemUnitConversion, Transaction, Expense,
    OtherIncome, BankAccount, Settings,
    Category, Unit, Warehouse, OpeningStock,
)
from .serializers import (
    BusinessProfileSerializer, PartySerializer, ItemSerializer,
    TransactionSerializer, ExpenseSerializer, OtherIncomeSerializer,
    BankAccountSerializer, SettingsSerializer,
    CategorySerializer, UnitSerializer, WarehouseSerializer, OpeningStockSerializer,
    UserSerializer, CreateUserSerializer, ItemUnitConversionSerializer,
)


# ============ Base ViewSet with user scoping ============
class UserScopedViewSet(viewsets.ModelViewSet):
    """Base ViewSet that filters all data by the authenticated user."""

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryViewSet(UserScopedViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class UnitViewSet(UserScopedViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class WarehouseViewSet(UserScopedViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class OpeningStockViewSet(UserScopedViewSet):
    queryset = OpeningStock.objects.select_related('item', 'warehouse').all()
    serializer_class = OpeningStockSerializer

    def get_queryset(self):
        qs = super().get_queryset()  # applies user filter from UserScopedViewSet
        item_id = self.request.query_params.get('item')
        if item_id:
            qs = qs.filter(item_id=item_id)
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        # Adjust item stock when opening stock entry is created
        item = instance.item
        item.stock += instance.quantity
        item.save()

    def perform_destroy(self, instance):
        # Reverse stock when deleted
        item = instance.item
        item.stock -= instance.quantity
        item.save()
        instance.delete()


class BusinessProfileViewSet(UserScopedViewSet):
    queryset = BusinessProfile.objects.all()
    serializer_class = BusinessProfileSerializer

    def list(self, request, *args, **kwargs):
        _ensure_user_defaults(request.user)
        return super().list(request, *args, **kwargs)


class PartyViewSet(UserScopedViewSet):
    queryset = Party.objects.all().order_by('name')
    serializer_class = PartySerializer


class ItemViewSet(UserScopedViewSet):
    queryset = Item.objects.all().order_by('name')
    serializer_class = ItemSerializer


class ItemUnitConversionViewSet(UserScopedViewSet):
    """CRUD for alternate units of a specific item."""
    serializer_class = ItemUnitConversionSerializer

    def get_queryset(self):
        qs = ItemUnitConversion.objects.filter(user=self.request.user)
        item_id = self.request.query_params.get('item')
        if item_id:
            qs = qs.filter(item_id=item_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(UserScopedViewSet):
    queryset = Transaction.objects.all().order_by('-date', '-id')
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = super().get_queryset()  # applies user filter from UserScopedViewSet
        txn_type = self.request.query_params.get('type')
        if txn_type:
            qs = qs.filter(type=txn_type)
        party = self.request.query_params.get('party')
        if party:
            qs = qs.filter(party_id=party)
        date_from = self.request.query_params.get('from_date')
        date_to = self.request.query_params.get('to_date')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs


class ExpenseViewSet(UserScopedViewSet):
    queryset = Expense.objects.all().order_by('-date')
    serializer_class = ExpenseSerializer


class OtherIncomeViewSet(UserScopedViewSet):
    queryset = OtherIncome.objects.all().order_by('-date')
    serializer_class = OtherIncomeSerializer


class BankAccountViewSet(UserScopedViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer


class SettingsViewSet(UserScopedViewSet):
    queryset = Settings.objects.all()
    serializer_class = SettingsSerializer

    def list(self, request, *args, **kwargs):
        _ensure_user_defaults(request.user)
        return super().list(request, *args, **kwargs)


# ============ Aggregate / Dashboard endpoint ============
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Aggregate business stats for the dashboard."""
    business = BusinessProfile.objects.filter(user=request.user).first()
    currency = business.currency if business else '₹'

    sales = Transaction.objects.filter(type='SaleInvoice', user=request.user)
    purchases = Transaction.objects.filter(type='PurchaseBill', user=request.user)
    expenses = Expense.objects.filter(user=request.user)
    items = Item.objects.filter(user=request.user)
    bank_accounts = BankAccount.objects.filter(user=request.user)

    now = datetime.now()
    month_start = now.replace(day=1).date()

    this_month_sales = sum(
        (t.total_amount for t in sales if t.date >= month_start),
        Decimal(0),
    )
    this_month_purchases = sum(
        (t.total_amount for t in purchases if t.date >= month_start),
        Decimal(0),
    )
    total_receivable = sum((t.balance_amount for t in sales), Decimal(0))
    total_payable = sum((t.balance_amount for t in purchases), Decimal(0))
    stock_value = sum((i.stock * i.purchase_price for i in items), Decimal(0))
    total_expenses = sum((e.amount for e in expenses), Decimal(0))

    cash_in_hand = sum(
        (a.opening_balance for a in bank_accounts if a.type == 'Cash'),
        Decimal(0),
    ) + sum(
        (t.paid_amount for t in sales if t.payment_type == 'Cash'),
        Decimal(0),
    )

    # Monthly trend - last 12 months
    monthly = []
    for i in range(11, -1, -1):
        start = (now.replace(day=1) - relativedelta(months=i)).date()
        end = (start + relativedelta(months=1))
        m_sales = sum(
            (t.total_amount for t in sales if start <= t.date < end),
            Decimal(0),
        )
        m_purchases = sum(
            (t.total_amount for t in purchases if start <= t.date < end),
            Decimal(0),
        )
        monthly.append({
            'month': start.strftime('%b'),
            'month_year': start.strftime('%b %Y'),
            'sales': float(m_sales),
            'purchases': float(m_purchases),
        })

    # Sales by category
    category_map = {}
    for t in sales:
        for line in t.lines.all():
            if line.item:
                cat = line.item.category or 'Uncategorized'
                category_map[cat] = category_map.get(cat, 0) + float(line.amount)
    colors = ['#2563eb', '#16a34a', '#d97706', '#9333ea', '#dc2626', '#0891b2']
    category_data = [
        {'name': k, 'value': round(v), 'color': colors[idx % len(colors)]}
        for idx, (k, v) in enumerate(category_map.items())
    ]

    # Recent transactions
    recent_qs = Transaction.objects.filter(user=request.user).order_by('-date', '-id')[:8]
    recent = []
    for t in recent_qs:
        recent.append({
            'id': t.id,
            'type': t.type,
            'invoice_no': t.invoice_no,
            'party_name': t.party_name,
            'date': str(t.date),
            'total_amount': float(t.total_amount),
            'balance_amount': float(t.balance_amount),
        })

    return Response({
        'currency': currency,
        'stats': {
            'this_month_sales': float(this_month_sales),
            'this_month_purchases': float(this_month_purchases),
            'cash_in_hand': float(cash_in_hand),
            'stock_value': float(stock_value),
            'total_receivable': float(total_receivable),
            'total_payable': float(total_payable),
            'total_expenses': float(total_expenses),
        },
        'monthly': monthly,
        'category_data': category_data,
        'recent': recent,
        'item_count': items.count(),
        'party_count': Party.objects.filter(user=request.user).count(),
    })


# ============ Reports endpoint ============
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports(request):
    report_type = request.query_params.get('type', 'sale')
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date')

    def in_range(date):
        if from_date and date < from_date:
            return False
        if to_date and date > to_date:
            return False
        return True

    result = {}

    if report_type == 'sale':
        txns = [t for t in Transaction.objects.filter(type='SaleInvoice', user=request.user) if in_range(str(t.date))]
        result['rows'] = [{
            'id': t.id, 'invoice_no': t.invoice_no, 'date': str(t.date),
            'party_name': t.party_name, 'total_amount': float(t.total_amount),
            'paid_amount': float(t.paid_amount), 'balance_amount': float(t.balance_amount),
        } for t in txns]
        result['total'] = float(sum((t.total_amount for t in txns), Decimal(0)))
        result['balance'] = float(sum((t.balance_amount for t in txns), Decimal(0)))

    elif report_type == 'purchase':
        txns = [t for t in Transaction.objects.filter(type='PurchaseBill', user=request.user) if in_range(str(t.date))]
        result['rows'] = [{
            'id': t.id, 'invoice_no': t.invoice_no, 'date': str(t.date),
            'party_name': t.party_name, 'total_amount': float(t.total_amount),
            'paid_amount': float(t.paid_amount), 'balance_amount': float(t.balance_amount),
        } for t in txns]
        result['total'] = float(sum((t.total_amount for t in txns), Decimal(0)))
        result['balance'] = float(sum((t.balance_amount for t in txns), Decimal(0)))

    elif report_type == 'pl':
        sales = [t for t in Transaction.objects.filter(type='SaleInvoice', user=request.user) if in_range(str(t.date))]
        purchases = [t for t in Transaction.objects.filter(type='PurchaseBill', user=request.user) if in_range(str(t.date))]
        exps = [e for e in Expense.objects.filter(user=request.user) if in_range(str(e.date))]
        incomes = [i for i in OtherIncome.objects.filter(user=request.user) if in_range(str(i.date))]
        sales_revenue = float(sum((t.sub_total for t in sales), Decimal(0)))
        purchase_cost = float(sum((t.sub_total for t in purchases), Decimal(0)))
        exp_total = float(sum((e.amount for e in exps), Decimal(0)))
        income_total = float(sum((i.amount for i in incomes), Decimal(0)))
        result = {
            'sales_revenue': sales_revenue,
            'purchase_cost': purchase_cost,
            'expense_total': exp_total,
            'income_total': income_total,
            'gross_profit': sales_revenue - purchase_cost,
            'net_profit': sales_revenue - purchase_cost - exp_total + income_total,
        }

    elif report_type == 'gstr1':
        txns = [t for t in Transaction.objects.filter(type='SaleInvoice', user=request.user) if in_range(str(t.date))]
        hsn_map = {}
        for t in txns:
            for line in t.lines.all():
                hsn = line.hsn or 'N/A'
                if hsn not in hsn_map:
                    hsn_map[hsn] = {'taxable_value': 0, 'cgst': 0, 'sgst': 0, 'igst': 0}
                hsn_map[hsn]['taxable_value'] += float(line.amount)
                line_gst = float(line.amount) * float(line.gst_rate) / 100
                if float(t.igst) > 0:
                    hsn_map[hsn]['igst'] += line_gst
                else:
                    hsn_map[hsn]['cgst'] += line_gst / 2
                    hsn_map[hsn]['sgst'] += line_gst / 2
        result['rows'] = [{
            'hsn': k, 'taxable_value': round(v['taxable_value']),
            'cgst': round(v['cgst']), 'sgst': round(v['sgst']), 'igst': round(v['igst']),
            'total': round(v['taxable_value'] + v['cgst'] + v['sgst'] + v['igst']),
        } for k, v in hsn_map.items()]

    elif report_type == 'gstr3b':
        sales = [t for t in Transaction.objects.filter(type='SaleInvoice', user=request.user) if in_range(str(t.date))]
        purchases = [t for t in Transaction.objects.filter(type='PurchaseBill', user=request.user) if in_range(str(t.date))]
        outward_taxable = float(sum((t.sub_total for t in sales), Decimal(0)))
        outward_tax = float(sum((t.cgst + t.sgst + t.igst for t in sales), Decimal(0)))
        inward_taxable = float(sum((t.sub_total for t in purchases), Decimal(0)))
        inward_tax = float(sum((t.cgst + t.sgst + t.igst for t in purchases), Decimal(0)))
        result = {
            'outward_taxable': outward_taxable,
            'outward_tax': outward_tax,
            'inward_taxable': inward_taxable,
            'inward_tax': inward_tax,
            'net_tax_payable': max(0, outward_tax - inward_tax),
        }

    elif report_type == 'stock':
        result['rows'] = [{
            'name': i.name, 'hsn': i.hsn, 'stock': float(i.stock),
            'unit': i.unit, 'value': float(i.stock * i.purchase_price),
            'min_stock': float(i.min_stock),
            'low': i.stock <= i.min_stock,
        } for i in Item.objects.filter(user=request.user).order_by('name')]

    elif report_type == 'all':
        txns = [t for t in Transaction.objects.filter(user=request.user) if in_range(str(t.date))]
        txns.sort(key=lambda t: t.date, reverse=True)
        result['rows'] = [{
            'id': t.id, 'date': str(t.date), 'type': t.type,
            'invoice_no': t.invoice_no, 'party_name': t.party_name,
            'total_amount': float(t.total_amount), 'balance_amount': float(t.balance_amount),
        } for t in txns]

    return Response(result)


# ============ Party balances endpoint ============
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def party_balances(request):
    """Compute receivable/payable balances for each party from transactions."""
    parties = Party.objects.filter(user=request.user).order_by('name')
    result = []
    for p in parties:
        txns = Transaction.objects.filter(party_id=p.id, user=request.user)
        receivable = sum(
            (t.balance_amount for t in txns if t.type in ('SaleInvoice', 'SaleReturn')),
            Decimal(0),
        )
        payable = sum(
            (t.balance_amount for t in txns if t.type in ('PurchaseBill', 'PurchaseReturn')),
            Decimal(0),
        )
        opening = p.opening_balance * (Decimal(1) if p.balance_type == 'To Receive' else Decimal(-1))
        if p.balance_type == 'To Receive':
            receivable += opening
        else:
            payable += abs(opening)
        result.append({
            'id': p.id, 'name': p.name, 'type': p.type, 'phone': p.phone,
            'gstin': p.gstin, 'group': p.group,
            'receivable': float(max(0, receivable - payable)) if receivable > payable else 0,
            'payable': float(max(0, payable - receivable)) if payable > receivable else 0,
        })
    return Response(result)


# ============ Auth / User Management ============
class UserListView(generics.ListCreateAPIView):
    """List all users (superadmin only) or create a new user."""
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user (superadmin only)."""
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_destroy(self, instance):
        # Prevent self-deletion
        if instance == self.request.user:
            raise ValidationError({'detail': 'Cannot delete your own account.'})
        instance.delete()


def _ensure_user_defaults(user):
    """Auto-create Settings and BusinessProfile for a user if they don't exist yet."""
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current authenticated user's info.
    Also bootstraps Settings + BusinessProfile on first login."""
    user = request.user
    _ensure_user_defaults(user)
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Allow the authenticated user to change their own password."""
    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')

    if not old_password or not new_password:
        return Response(
            {'detail': 'Both old_password and new_password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.user.check_password(old_password):
        return Response(
            {'detail': 'Current password is incorrect.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 6:
        return Response(
            {'detail': 'New password must be at least 6 characters.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request.user.set_password(new_password)
    request.user.save()
    return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)
