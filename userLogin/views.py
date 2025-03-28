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

from .vnstock_services import stock, get_ticker_companyname, get_refer_price

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
    user = request.user

    # Lấy danh sách cổ phiếu mà user đang sở hữu
    user_stocks = UserAssets.objects.filter(user=user)
    
    # Lấy thông tin về các mã cổ phiếu và tên công ty
    list_stock_market = get_ticker_companyname()
    ticker_to_company = {stock['ticker']: stock['organ_name'] for stock in list_stock_market}
    
    # Tổng giá trị danh mục đầu tư
    portfolio_value = Decimal('0')

    # Tính lãi/lỗ = (Tổng giá hiện tại - tổng giá mua) * số lượng
    total_profit_loss = Decimal('0')

    # Số cổ phiếu có lãi
    number_profit_stock = 0
    
    # Chuẩn bị dữ liệu về danh mục đầu tư
    portfolios = []
    for user_stock in user_stocks:
        # Lấy tên công ty
        company_name = ticker_to_company.get(user_stock.stock_code, "Không có thông tin")
        
        # Lấy giá hiện tại
        try:
            current_price = get_refer_price(user_stock.stock_code)
            if current_price:
                current_price = Decimal(str(current_price))
            else:
                current_price = Decimal('0')
        except:
            current_price = Decimal('0')
        
        # Tính tổng giá trị hiện tại của cổ phiếu
        total_value = current_price * user_stock.amount
        portfolio_value += total_value

        # Giá mua trung bình
        avg_buy_price = user_stock.average_buy_price
        
        # Tính lãi/lỗ
        profit_loss = (current_price - avg_buy_price) * user_stock.amount
        total_profit_loss += profit_loss
        if profit_loss >= 0:
            number_profit_stock += 1
        
        # Tính thay đổi giá (có thể là so với ngày hôm trước hoặc so với giá mua)
        price_change = current_price - avg_buy_price
        price_change_percent = Decimal('0')
        if avg_buy_price > 0:
            price_change_percent = (price_change / avg_buy_price) * 100
        
        portfolios.append({
            'stock_code': user_stock.stock_code,
            'company_name': company_name,
            'amount': user_stock.amount,
            'avg_buy_price': avg_buy_price,
            'current_price': current_price,
            'total_value': total_value,
            'price_change_percent': round(price_change_percent, 2),
            'profit_loss': profit_loss,
        })
    
    # Lấy 10 giao dịch gần nhất
    recent_transactions = StockTransactions.objects.filter(
        user=request.user
    ).order_by('-time')[:10]
    
    # Thêm thông tin về tên công ty và tổng giá trị
    for transaction in recent_transactions:
        transaction.organ_name = ticker_to_company.get(transaction.stock_code, "Không có thông tin")
        transaction.total_value = transaction.price * transaction.amount
    
    context = {
        # 'user_balance': user_balance,
        'portfolio_value': portfolio_value,
        'total_profit_loss': total_profit_loss,
        'number_of_stock':len(user_stocks),
        'number_profit_stock': number_profit_stock,
        'number_loss_stock':len(user_stocks)-number_profit_stock,
        'portfolios': portfolios,
        # 'recent_transactions': recent_transactions,
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
    history_deposit = WalletTransactions.objects.filter(user=request.user, transaction_type='D').order_by('-time')
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
    if request.method != "POST":
        return render(request, '404.html')
    
    try:
        # Lấy thông tin từ form
        stock_code = request.POST.get("stock-code")
        stock_price_str = request.POST.get("stock-price", "0")
        stock_amount_str = request.POST.get("stock-amount", "0")
        
        # Kiểm tra dữ liệu đầu vào
        if not all([stock_code, stock_price_str, stock_amount_str]):
            messages.error(request, "Vui lòng nhập đầy đủ thông tin giao dịch!")
            return redirect("userLogin:trading")
        
        # Chuyển đổi và làm sạch dữ liệu
        stock_price = Decimal(stock_price_str.replace(',',''))
        stock_amount = int(stock_amount_str)
        total_value = stock_price * stock_amount
        
        # Kiểm tra số lượng hợp lệ
        if stock_amount <= 0:
            messages.error(request, "Số lượng cổ phiếu phải lớn hơn 0!")
            return redirect("userLogin:trading")
        
        # Kiểm tra số dư
        user = request.user
        if user.balance < total_value:
            messages.error(request, f"Số dư không đủ để thực hiện giao dịch! Cần {total_value:,} VND.")
            return redirect("userLogin:trading")
        
        # Bắt đầu giao dịch database
        with transaction.atomic():
            # Trừ tiền trong tài khoản người dùng
            user.balance = F("balance") - total_value
            user.save(update_fields=["balance"])
            user.refresh_from_db()
            
            # Cập nhật hoặc tạo mới tài sản cổ phiếu
            try:
                # Kiểm tra xem user đã có cổ phiếu này chưa
                user_asset = UserAssets.objects.get(user=user, stock_code=stock_code)
                
                # Tính giá mua trung bình mới
                current_total_value = user_asset.amount * user_asset.average_buy_price
                new_total_value = current_total_value + (stock_amount * stock_price)
                new_total_amount = user_asset.amount + stock_amount
                new_average_price = new_total_value / new_total_amount
                
                # Cập nhật số lượng và giá trung bình
                user_asset.amount = new_total_amount
                user_asset.average_buy_price = new_average_price
                user_asset.save()
                
            except UserAssets.DoesNotExist:
                # Tạo mới nếu chưa có
                UserAssets.objects.create(
                    user=user,
                    stock_code=stock_code,
                    amount=stock_amount,
                    average_buy_price=stock_price,
                )
            
            # Ghi lại giao dịch vào lịch sử
            StockTransactions.objects.create(
                user=user,
                stock_code=stock_code,
                is_sell=False,  # False: giao dịch MUA
                price=stock_price,
                amount=stock_amount,
                balance_after=user.balance,
                is_successful=True,
            )
            
            messages.success(request, f"Mua thành công {stock_amount} cổ phiếu {stock_code} với giá {stock_price:,} VND!")
            
    except ValueError as e:
        messages.error(request, f"Dữ liệu không hợp lệ: {str(e)}")
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    return redirect("userLogin:trading")




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


