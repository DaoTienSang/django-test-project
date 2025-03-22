from django.urls import path

from . import views



app_name = 'news'
urlpatterns = [
    path('', views.home, name='home'),
    path('candle/', views.candle_chart, name='candle_chart1,')

]