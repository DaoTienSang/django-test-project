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
    path('market/', views.market, name='market'),

    path('add-bank-account/', views.add_bank_account, name='add_bank_account'),     # add bank account
    path('buy-stock/', views.buy_stock, name='buy_stock'),                          # buy stock
    path('sell-stock/', views.sell_stock, name='sell_stock'),                          # buy stock

    # API
    path('api/transaction/<int:id>/', api_services.transaction_detail, name='transaction-detail'),      # Chi tiết giao dịch
    path('api/stock-price/<str:stock_code>/', api_services.stock_price_api, name='stock_price_api'),    # Giá tham chiếu cổ phiếu
    path('api/historical-data/<str:stock_code>/', api_services.get_historical_data_api, name='get_historical_data_api'),    # Giá lịch sử cổ phiếu
]