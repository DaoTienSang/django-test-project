from django.urls import re_path
from .consumers import CandlestickConsumer

websocket_urlpatterns = [
    re_path(r'ws/candlestick/(?P<stock_code>\w+)/$', CandlestickConsumer.as_asgi()),
]
