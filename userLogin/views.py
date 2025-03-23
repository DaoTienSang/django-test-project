from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum
from django.db import transaction
from django.http import Http404
# from django.contrib.auth.models import User

from accounts.models import User
from .models import WalletTransactions, StockTransactions, UserBankAccounts, UserAssets

from .vnstock_services import stock, get_ticker_companyname, get_match_price

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
    # Lấy thông tin về số dư của user
    user_balance = request.user.balance
    
    # Lấy danh sách cổ phiếu mà user đang sở hữu
    user_stocks = UserAssets.objects.filter(user=request.user)
    
    # Lấy thông tin về các mã cổ phiếu và tên công ty
    list_stock_market = get_ticker_companyname()
    ticker_to_company = {stock['ticker']: stock['organ_name'] for stock in list_stock_market}
    
    # Tính tổng giá trị danh mục đầu tư
    portfolio_value = Decimal('0')
    
    # Chuẩn bị dữ liệu về danh mục đầu tư
    portfolio = []
    for user_stock in user_stocks:
        # Lấy tên công ty
        user_stock.organ_name = ticker_to_company.get(user_stock.stock_code, "Không có thông tin")
        
        # Lấy giá hiện tại
        try:
            current_price = get_match_price(user_stock.stock_code)
            if current_price:
                current_price = Decimal(str(current_price))
        except:
            current_price = Decimal('0')
        
        # Tính tổng giá trị hiện tại của cổ phiếu
        total_price_stock = current_price * user_stock.amount
        portfolio_value += total_price_stock
        
        # Tính giá mua trung bình
        avg_buy_data = StockTransactions.objects.filter(
            user=request.user,
            stock_code=user_stock.stock_code,
            is_sell=False
        ).aggregate(
            total_cost=Sum(F('price') * F('amount')),
            total_amount=Sum('amount')
        )
        
        total_cost = avg_buy_data['total_cost'] or Decimal('0')
        total_amount = avg_buy_data['total_amount'] or 0
        
        # Tính tổng số lượng đã bán
        total_sold = StockTransactions.objects.filter(
            user=request.user,
            stock_code=user_stock.stock_code,
            is_sell=True
        ).aggregate(sum_amount=Sum('amount'))['sum_amount'] or 0
        
        # Tính giá mua trung bình
        avg_buy_price = Decimal('0')
        if total_amount > 0:
            avg_buy_price = total_cost / total_amount
        
        # Tính lãi/lỗ
        profit_loss = (current_price - avg_buy_price) * user_stock.amount
        profit_loss_percent = Decimal('0')
        if avg_buy_price > 0:
            profit_loss_percent = (current_price - avg_buy_price) / avg_buy_price * 100
        
        portfolio.append({
            'stock_code': user_stock.stock_code,
            # 'organ_name': organ_name,
            'amount': user_stock.amount,
            'avg_buy_price': avg_buy_price,
            'current_price': current_price,
            # 'current_value': current_value,
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent,
            'total_bought': total_amount,
            'total_sold': total_sold
        })
    
    # Lấy 10 giao dịch gần nhất
    recent_transactions = StockTransactions.objects.filter(
        user=request.user
    ).order_by('-time')[:10]
    
    # Thêm thông tin về tên công ty và tổng giá trị
    for transaction in recent_transactions:
        transaction.organ_name = ticker_to_company.get(transaction.stock_code, "Không có thông tin")
        transaction.total_value = transaction.price * transaction.amount
    
    # Tính các thống kê về tài sản
    # Tổng tiền đã nạp vào hệ thống
    total_deposit = WalletTransactions.objects.filter(
        user=request.user,
        transaction_type='D'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Tổng tiền đã rút
    total_withdraw = WalletTransactions.objects.filter(
        user=request.user,
        transaction_type='W'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Tổng giá trị tài sản (số dư + giá trị danh mục)
    total_assets_value = user_balance + portfolio_value
    
    # Lãi/lỗ tổng (tổng tài sản - tổng nạp + tổng rút)
    total_profit_loss = total_assets_value - total_deposit + total_withdraw
    
    context = {
        'user_balance': user_balance,
        'portfolio': portfolio,
        'portfolio_value': portfolio_value,
        'recent_transactions': recent_transactions,
        'total_deposit': total_deposit,
        'total_withdraw': total_withdraw,
        'total_assets_value': total_assets_value,
        'total_profit_loss': total_profit_loss
    }
    
    return render(request, 'userLogin/assets_management.html', context)



# =========== view nạp tiền
@login_required
def deposit_management(request):
    if request.method == 'POST':
        deposit_amount = request.POST.get('deposit-amount')
        if (deposit_amount and request.user.is_authenticated):
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
    return render(request, '404.html')


# Lấy nhóm các lịch sử giao dịch mua theo mã, giá cổ phiếu
# user_assets = StockTransactions.objects.filter(is_sell=False, user=user).values("user", "stock_code", "is_sell", "price").annotate(total_amount=Sum('amount'))
# for a in user_assets:
#     print(a.get("stock_code"))


# - MANAGE TRADING
@login_required
def trading_management(request):
    user = request.user

    # Tính số giao dịch trong tháng này
    one_month_ago = timezone.now() - relativedelta(months=1)
    monthly_transactions_count = StockTransactions.objects.filter(
        user=user,
        time__gte=one_month_ago
    ).count()

    user_balance = user.balance                                 # balance user
    list_stock_market = get_ticker_companyname()                # Lấy mã cổ phiếu và tên công ty
    user_stocks = UserAssets.objects.filter(user=user)  # Cổ phiếu của user
    # Tạo dictionary để map từ ticker sang organ_name
    ticker_to_company = {stock['ticker']: stock['organ_name'] for stock in list_stock_market}
    
    # Lấy lịch sử giao dịch
    transaction_history = StockTransactions.objects.filter(user=user).order_by('-time')[:10]
    for transaction in transaction_history:
        transaction.total_value = transaction.amount*transaction.price
    
    context = {
        'user_balance'                  : user_balance,
        'monthly_transactions_count'    : monthly_transactions_count,
        'list_stock_market'             : list_stock_market,
        'user_stocks'                   : user_stocks,
        'transaction_history'           : transaction_history,
    }

    return render(request, 'userLogin/trading_management.html', context)

    

# - BUY STOCK VIEW
@login_required
def buy_stock(request):
    if request.method == "POST":
        stock_code = request.POST.get("stock-code")  # Mã cổ phiếu
        stock_price = request.POST.get("stock-price")  # Giá cổ phiếu
        stock_amount = request.POST.get("stock-amount")  # Số lượng cổ phiếu muốn mua
        
        # Chuyển đổi kiểu dữ liệu
        stock_price = Decimal(stock_price.replace(',',''))
        stock_amount = int(stock_amount)
        total_value = stock_price * stock_amount  # Tổng giá trị giao dịch
        user = request.user  # Lấy user hiện tại

        # # Kiểm tra số dư của người dùng có đủ không
        if user.balance < total_value:
            messages.error(request, "Số dư không đủ để thực hiện giao dịch!")
            return redirect("userLogin:trading")
        try:
            # Bắt đầu giao dịch database
            with transaction.atomic():
                # Trừ tiền trong tài khoản người dùng
                user.balance = F("balance") - total_value
                user.save(update_fields=["balance"])

                # Cập nhật hoặc tạo mới UserAssets (cổ phiếu sở hữu)
                user_asset, created = UserAssets.objects.get_or_create(
                    user=user,
                    stock_code=stock_code,
                    # buy_price=stock_price,    
                    defaults={"amount": stock_amount}
                )
                if not created:
                    user_asset.amount = F("amount") + stock_amount
                    user_asset.save(update_fields=["amount"])

                # Ghi lại giao dịch mua vào StockTransactions
                user.refresh_from_db()      
                StockTransactions.objects.create(
                    user            = user,
                    stock_code      = stock_code,
                    is_sell         = False,  # False: giao dịch MUA
                    price           = stock_price,
                    amount          = stock_amount,
                    balance_after   = user.balance,
                    is_successful   = True,
                )

                messages.success(request, "Mua cổ phiếu thành công!")
                return redirect("userLogin:trading")
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {e}")
            return redirect("userLogin:trading")
        return redirect("userLogin:trading")

    return render(request, '404.html')



# - SELL STOCK VIEW
@login_required
def sell_stock(request):
    if request.method == "POST":
        stock_code = request.POST.get("stock-code")  # Mã cổ phiếu
        stock_price = request.POST.get("stock-price")  # Giá cổ phiếu
        stock_amount = request.POST.get("stock-amount")  # Số lượng cổ phiếu muốn bán
        
        # Chuyển đổi kiểu dữ liệu
        stock_price = Decimal(stock_price.replace(',',''))
        stock_amount = int(stock_amount)
        total_value = stock_price * stock_amount  # Tổng giá trị giao dịch

        user = request.user  # Lấy user hiện tại

        try:
            # Lấy tất cả các bản ghi của user cho mã cổ phiếu này
            user_assets = UserAssets.objects.filter(user=user, stock_code=stock_code).order_by('id')
            print('='*100)
            print(user_assets)
            
            
            # Tính tổng số lượng cổ phiếu mà user đang sở hữu
            total_owned = user_assets.aggregate(total=Sum('amount'))['total'] or 0
            print(total_owned)
            
            # Kiểm tra người dùng có đủ cổ phiếu để bán không
            if total_owned < stock_amount:
                messages.error(request, "Bạn không có đủ cổ phiếu để thực hiện giao dịch này!")
                return redirect("userLogin:trading")
            
            # Bắt đầu giao dịch database
            with transaction.atomic():
                # Cộng tiền vào tài khoản người dùng
                user.balance = F("balance") + total_value
                user.save(update_fields=["balance"])

                # Áp dụng chiến lược FIFO (First In First Out) để bán cổ phiếu
                remaining_to_sell = stock_amount
                
                for asset in user_assets:
                    if remaining_to_sell <= 0:
                        break
                        
                    # Số lượng có thể bán từ bản ghi hiện tại
                    can_sell_from_current = min(asset.amount, remaining_to_sell)
                    
                    # Cập nhật số lượng
                    asset.amount -= can_sell_from_current
                    remaining_to_sell -= can_sell_from_current
                    
                    # Lưu hoặc xóa nếu số lượng = 0
                    if asset.amount > 0:
                        asset.save()
                    else:
                        asset.delete()
                
                # Ghi lại giao dịch bán vào StockTransactions
                user.refresh_from_db()      
                StockTransactions.objects.create(
                    user            = user,
                    stock_code      = stock_code,
                    is_sell         = True,  # True: giao dịch BÁN
                    price           = stock_price,
                    amount          = stock_amount,
                    balance_after   = user.balance,
                    is_successful   = True,
                )

                messages.success(request, f"Bán thành công {stock_amount} cổ phiếu {stock_code} với giá {stock_price:,} VND!")
                return redirect("userLogin:trading")
                
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {e}")
            return redirect("userLogin:trading")

    return render(request, '404.html')


