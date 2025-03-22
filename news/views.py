from django.shortcuts import render
from django.contrib import messages
from vnstock import Vnstock
from django.contrib.auth.decorators import login_required




# list_stock = Vnstock().stock(source='VCI').listing.all_symbols()['ticker'].values



def home(request):
    return render(request, 'index.html')


# @login_required
def candle_chart(request):
    # if request.method == 'POST':
    #     # stock_code = request.POST['stock-code']
    #     stock_code = request.POST.get('stock-code').strip()
    #     print(stock_code)
    #     if stock_code in list_stock:
    #         print(stock_code)
    #     else:
    #         messages.error(request, f"Can't find the {stock_code} stock!")
    #         print(f'Stock with code {stock_code} is not in list')
    #     return render(request, 'news/candle_chart.html')
    # print('-'*100)
    # print(request.GET.get('stock_code'))
    return render(request, 'news/candle_chart.html')