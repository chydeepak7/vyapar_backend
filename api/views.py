from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    BusinessProfile, Party, Item, Transaction, Expense,
    OtherIncome, BankAccount, Settings,
)
from .serializers import (
    BusinessProfileSerializer, PartySerializer, ItemSerializer,
    TransactionSerializer, ExpenseSerializer, OtherIncomeSerializer,
    BankAccountSerializer, SettingsSerializer,
)


class BusinessProfileViewSet(viewsets.ModelViewSet):
    queryset = BusinessProfile.objects.all()
    serializer_class = BusinessProfileSerializer


class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all().order_by('name')
    serializer_class = PartySerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().order_by('name')
    serializer_class = ItemSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by('-date', '-id')
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
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


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all().order_by('-date')
    serializer_class = ExpenseSerializer


class OtherIncomeViewSet(viewsets.ModelViewSet):
    queryset = OtherIncome.objects.all().order_by('-date')
    serializer_class = OtherIncomeSerializer


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer


class SettingsViewSet(viewsets.ModelViewSet):
    queryset = Settings.objects.all()
    serializer_class = SettingsSerializer


# ============ Aggregate / Dashboard endpoint ============
@api_view(['GET'])
def dashboard(request):
    """Aggregate business stats for the dashboard."""
    business = BusinessProfile.objects.first()
    currency = business.currency if business else '₹'

    sales = Transaction.objects.filter(type='SaleInvoice')
    purchases = Transaction.objects.filter(type='PurchaseBill')
    expenses = Expense.objects.all()
    items = Item.objects.all()
    bank_accounts = BankAccount.objects.all()

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
    recent_qs = Transaction.objects.order_by('-date', '-id')[:8]
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
        'party_count': Party.objects.count(),
    })


# ============ Reports endpoint ============
@api_view(['GET'])
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
        txns = [t for t in Transaction.objects.filter(type='SaleInvoice') if in_range(str(t.date))]
        result['rows'] = [{
            'id': t.id, 'invoice_no': t.invoice_no, 'date': str(t.date),
            'party_name': t.party_name, 'total_amount': float(t.total_amount),
            'paid_amount': float(t.paid_amount), 'balance_amount': float(t.balance_amount),
        } for t in txns]
        result['total'] = float(sum((t.total_amount for t in txns), Decimal(0)))
        result['balance'] = float(sum((t.balance_amount for t in txns), Decimal(0)))

    elif report_type == 'purchase':
        txns = [t for t in Transaction.objects.filter(type='PurchaseBill') if in_range(str(t.date))]
        result['rows'] = [{
            'id': t.id, 'invoice_no': t.invoice_no, 'date': str(t.date),
            'party_name': t.party_name, 'total_amount': float(t.total_amount),
            'paid_amount': float(t.paid_amount), 'balance_amount': float(t.balance_amount),
        } for t in txns]
        result['total'] = float(sum((t.total_amount for t in txns), Decimal(0)))
        result['balance'] = float(sum((t.balance_amount for t in txns), Decimal(0)))

    elif report_type == 'pl':
        sales = [t for t in Transaction.objects.filter(type='SaleInvoice') if in_range(str(t.date))]
        purchases = [t for t in Transaction.objects.filter(type='PurchaseBill') if in_range(str(t.date))]
        exps = [e for e in Expense.objects.all() if in_range(str(e.date))]
        incomes = [i for i in OtherIncome.objects.all() if in_range(str(i.date))]
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
        txns = [t for t in Transaction.objects.filter(type='SaleInvoice') if in_range(str(t.date))]
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
        sales = [t for t in Transaction.objects.filter(type='SaleInvoice') if in_range(str(t.date))]
        purchases = [t for t in Transaction.objects.filter(type='PurchaseBill') if in_range(str(t.date))]
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
        } for i in Item.objects.all().order_by('name')]

    elif report_type == 'all':
        txns = [t for t in Transaction.objects.all() if in_range(str(t.date))]
        txns.sort(key=lambda t: t.date, reverse=True)
        result['rows'] = [{
            'id': t.id, 'date': str(t.date), 'type': t.type,
            'invoice_no': t.invoice_no, 'party_name': t.party_name,
            'total_amount': float(t.total_amount), 'balance_amount': float(t.balance_amount),
        } for t in txns]

    return Response(result)


# ============ Party balances endpoint ============
@api_view(['GET'])
def party_balances(request):
    """Compute receivable/payable balances for each party from transactions."""
    parties = Party.objects.all().order_by('name')
    result = []
    for p in parties:
        txns = Transaction.objects.filter(party_id=p.id)
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
