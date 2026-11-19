from rest_framework.routers import DefaultRouter
from .views import (
    BusinessProfileViewSet, PartyViewSet, ItemViewSet,
    TransactionViewSet, ExpenseViewSet, OtherIncomeViewSet,
    BankAccountViewSet, SettingsViewSet,
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

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard, name='dashboard'),
    path('reports/', reports, name='reports'),
    path('party-balances/', party_balances, name='party-balances'),
]
