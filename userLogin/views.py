from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum
# from django.contrib.auth.models import User


from accounts.models import User
from .models import WalletTransactions, StockTransactions, UserBankAccounts, UserAssets

from .vnstock_services import stock, get_ticker_companyname

import random
import string
from decimal import Decimal



# ========= DASHBOARD ========================
@login_required
def dashboard(request):
    return render(request, 'userLogin/dashboard.html')


# ========== view xem tài sản ==================
@login_required
def assets_management(request):
    return render(request, 'userLogin/assets_management.html')


# =========== view nạp tiền
@login_required
def deposit_management(request):
    if request.method == 'POST':
        deposit_amount = request.POST.get('deposit-amount')
        if deposit_amount and request.user.is_authenticated:
            try:
                deposit_amount = deposit_amount.replace(',','')
                if len(deposit_amount) > 16 :
                    messages.error(request, "Vui lòng nhập số hợp lệ.")
                else:
                    deposit_amount = int(deposit_amount)
                    if deposit_amount < 100000:
                        messages.error(request, "Số tiền nạp phải từ 100,000VND!")
                    else:
                        user = request.user
                        description = request.POST.get('deposit-description')
                        bank_id = request.POST.get('bank-info')
                        try:
                            bank = UserBankAccounts.objects.get(id=bank_id, user=request.user)
                        except UserBankAccounts.DoesNotExist:
                            messages.error(request, "Tài khoản ngân hàng không hợp lệ!")
                            return redirect("userLogin:withdraw")
                        # user deposit
                        User.objects.filter(id=user.id).update(balance = F('balance')+deposit_amount)
                        
                        # code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                        # print(code)
                        WalletTransactions.objects.create(user=request.user, 
                                                        amount=Decimal(deposit_amount),
                                                        transaction_type='D',
                                                        balance_after=user.balance+Decimal(deposit_amount),
                                                        status='C',
                                                        description=description,
                                                        bank_info=bank,
                                                        )
                        messages.success(request, f'Nạp thành công {deposit_amount:,} VND vào tài khoản.')
            except ValueError:
                messages.error(request, "Vui lòng nhập số hợp lệ.")
        return redirect("userLogin:deposit")
    user_banks = UserBankAccounts.objects.filter(user=request.user)
    history_deposit = WalletTransactions.objects.filter(user=request.user).order_by('-time')
    one_month_ago = timezone.now() - relativedelta(months=1)
    amount_deposit_amonth = history_deposit.filter(time__gte=one_month_ago).aggregate(Sum('amount'))['amount__sum'] or 0
    context = {
        "amount_deposit_amonth":amount_deposit_amonth,
        "history_deposit":history_deposit,
        "user_banks":user_banks,
    }
    return render(request, 'userLogin/deposit_management.html', context)


# ========== view rút tiền =============
@login_required
def withdraw_management(request):
    if request.method == 'POST':
        withdraw_amount = request.POST.get('withdraw-amount')
        withdraw_description = request.POST.get('withdraw-description')
        bank_id = request.POST.get('bank-info')
        
        if withdraw_amount and bank_id and request.user.is_authenticated:
            try:
                # Xử lý số tiền (loại bỏ dấu phẩy nếu có)
                withdraw_amount = int(withdraw_amount.replace(',', ''))
                print('='*100)
                print(withdraw_amount)
                
                # Kiểm tra số tiền tối thiểu
                if withdraw_amount < 100000:
                    messages.error(request, "Số tiền rút phải từ 100,000 VND!")
                    return redirect("userLogin:withdraw")
                
                # Kiểm tra số dư
                if withdraw_amount > request.user.balance:
                    messages.error(request, "Số dư không đủ để thực hiện giao dịch!")
                    return redirect("userLogin:withdraw")
                
                # Kiểm tra tài khoản ngân hàng
                try:
                    bank = UserBankAccounts.objects.get(id=bank_id, user=request.user)
                except UserBankAccounts.DoesNotExist:
                    messages.error(request, "Tài khoản ngân hàng không hợp lệ!")
                    return redirect("userLogin:withdraw")
                
                # Trừ tiền từ tài khoản user
                user_id = request.user.id
                User.objects.filter(id=user_id).update(balance=F('balance')-withdraw_amount)
                
                # Tạo mã giao dịch
                # code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                
                # Lưu lịch sử giao dịch
                WalletTransactions.objects.create(
                    user=request.user, 
                    amount=Decimal(withdraw_amount), 
                    transaction_type='W',
                    balance_after=request.user.balance-Decimal(withdraw_amount),
                    description=withdraw_description,
                    bank_info=bank,
                    status='C',
                )
                
                messages.success(request, f'Yêu cầu rút {withdraw_amount:,} VND thành công.')
            except ValueError:
                messages.error(request, "Vui lòng nhập số tiền hợp lệ.")
        else:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin.")
        return redirect("userLogin:withdraw")
    
    # Lấy lịch sử rút tiền
    history_withdraw = WalletTransactions.objects.filter(user=request.user, transaction_type='W').order_by('-time')
    
    # Tính tổng rút tiền trong tháng
    one_month_ago = timezone.now() - relativedelta(months=1)
    amount_withdraw_amonth = history_withdraw.filter(time__gte=one_month_ago).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Lấy danh sách tài khoản ngân hàng của user
    user_banks = UserBankAccounts.objects.filter(user=request.user)
    
    # Chuẩn bị dữ liệu cho hiển thị lịch sử giao dịch
    withdraw_history = []
    for transaction in history_withdraw:
        status_text = "Đang xử lý"
        status_class = "status-processing"
        
        # Xác định trạng thái giao dịch (giả sử có một trường status hoặc dựa vào thời gian)
        # if hasattr(transaction, 'status'):
        if transaction.is_completed:
            status_text = "Hoàn thành"
            status_class = "status-completed"
        elif transaction.is_failed:
            status_text = "Bị hủy"
            status_class = "status-cancelled"
        
        withdraw_history.append({
            'id': transaction.id,
            'time': transaction.time,
            'amount': transaction.amount,
            'bank_info': transaction.bank_info if hasattr(transaction, 'bank_info') else "Không có thông tin",
            'status_text': status_text,
            'status_class': status_class
        })
    
    context = {
        "amount_withdraw_amonth": amount_withdraw_amonth,
        "user_banks": user_banks,
        "withdraw_history": withdraw_history
    }
    
    return render(request, 'userLogin/withdraw_management.html', context)


# ============= view thêm tài khoản ngân hàng
@login_required
def add_bank_account(request):
    if request.method == 'POST':
        bank_name = request.POST.get('bank-name')
        account_number = request.POST.get('account-number')
        account_name = request.POST.get('account-name')
        
        if bank_name and account_number and account_name:
            # Kiểm tra xem tài khoản đã tồn tại chưa
            if UserBankAccounts.objects.filter(user=request.user, account_number=account_number, bank_name=bank_name).exists():
                messages.error(request, "Số tài khoản này đã tồn tại trong hệ thống của bạn!")
            else:
                UserBankAccounts.objects.create(
                    user=request.user,
                    bank_name=bank_name,
                    account_number=account_number,
                    account_name=account_name
                )
                messages.success(request, "Thêm tài khoản ngân hàng thành công!")
        else:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin!")
        url = request.META.get('HTTP_REFERER')
        return redirect(url)
    


def get_latest_stock_price(stock):
    latest_transaction = StockTransactions.objects.filter(stock=stock).order_by('-time').first()
    if latest_transaction:
        return latest_transaction.price
    return Decimal('100')  # Default price for demo



@login_required
def trading_management(request):
    user_balance = request.user.balance
    list_stock_market = get_ticker_companyname()
    print(list_stock_market)

    user_stocks = UserAssets.objects.filter(user=request.user)
    portfolio_value = Decimal('0')
    
    for user_stock in user_stocks:
        current_price = get_latest_stock_price(user_stock.stock)
        user_stock.current_price = current_price
        user_stock.total_value = current_price * user_stock.amount
        portfolio_value += user_stock.total_value
    from .models import list_stock
    available_stocks = list_stock
    transactions = StockTransactions.objects.filter(user=request.user).order_by('-time')[:10]
    
    context = {
        'user_balance': user_balance,
        'list_stock_market': list_stock_market,
        'portfolio_value': portfolio_value,
        'user_stocks': user_stocks,
        'transactions': transactions,
        # 'available_stocks': available_stocks,
    }
    return render(request, 'userLogin/trading_management.html', context)