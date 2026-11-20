from rest_framework.routers import DefaultRouter
from .views import (
    BusinessProfileViewSet, PartyViewSet, ItemViewSet,
    TransactionViewSet, ExpenseViewSet, OtherIncomeViewSet,
    BankAccountViewSet, SettingsViewSet,
    CategoryViewSet, UnitViewSet, WarehouseViewSet, OpeningStockViewSet,
    dashboard, reports, party_balances,
)
from django.urls import path, include

router = DefaultRouter()
router.register(r'business', BusinessProfileViewSet, basename='business')
router.register(r'parties', PartyViewSet, basename='party')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'other-incomes', OtherIncomeViewSet, basename='otherincome')
router.register(r'bank-accounts', BankAccountViewSet, basename='bankaccount')
router.register(r'settings', SettingsViewSet, basename='settings')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'opening-stocks', OpeningStockViewSet, basename='openingstock')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard, name='dashboard'),
    path('reports/', reports, name='reports'),
    path('party-balances/', party_balances, name='party-balances'),
]
