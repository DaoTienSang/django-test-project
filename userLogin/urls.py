from django.urls import path

from . import views
from . import api_services



app_name = 'userLogin'

urlpatterns = [
    path("dashboard/", views.dashboard, name='dashboard'),
    path("assets/", views.assets_management, name='assets'),
    path("deposit/", views.deposit_management, name='deposit'),
    path('withdraw/', views.withdraw_management, name='withdraw'),
    path('trading/', views.trading_management, name='trading'),
    path('add-bank-account/', views.add_bank_account, name='add_bank_account'),

    # API lấy chi tiết lịch sử giao dịch
    path('api/transaction/<int:id>/', api_services.transaction_detail, name='transaction-detail'),
    path('api/stock-price/<str:stock_code>/', api_services.stock_price_api, name='stock_price_api'),
]