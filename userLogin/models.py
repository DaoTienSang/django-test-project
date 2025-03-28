from django.db import models

from accounts.models import User



# =============== Bảng cổ phiếu mà người dùng có ======================
class UserAssets(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    stock_code = models.CharField(max_length=3)
    amount = models.PositiveIntegerField()
    average_buy_price = models.DecimalField(max_digits=16, decimal_places=0, null=True, blank=True)
    # company_name = models.CharField(max_length=200)
    
    class Meta:
        unique_together = ('user', 'stock_code')  # khóa chính
    
    def __str__(self):
        return f"{self.user.username} - {self.stock_code}: {self.amount} shares"



# HISTORY STOCK Model (Lịch sử giao dịch cổ phiếu)
class StockTransactions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_transactions')
    stock_code = models.CharField(max_length=10)
    is_sell = models.BooleanField()  # True: Sell, False: Buy
    price = models.DecimalField(max_digits=15, decimal_places=0)
    time = models.DateTimeField(auto_now_add=True)
    amount = models.PositiveIntegerField()
    balance_after = models.DecimalField(max_digits=16, decimal_places=0)
    is_successful = models.BooleanField(default=False)
    
    def __str__(self):
        action = "Sold" if self.is_sell else "Bought"
        return f"{self.user.username} {action} {self.amount} {self.stock_code} at {self.price}"



# ========= BANK ACCOUNT ==================
class UserBankAccounts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    account_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'account_number')
        verbose_name = 'Tài khoản ngân hàng'
        verbose_name_plural = 'Tài khoản ngân hàng'
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number} ({self.user.username})"



# HISTORY (Lịch sử nạp/rút tiền)
class WalletTransactions(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('W', 'Rút'),           # Withdraw
        ('D', 'Nạp'),           # Deposit
    ]
    STATUS_CHOICES = [
        ('P', 'Đang xử lý'),    # Pending
        ('C', 'Hoàn thành'),    # Completed
        ('F', 'Bị hủy'),        # Failed
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    amount = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=1, choices=TRANSACTION_TYPE_CHOICES)
    description = models.CharField(max_length=200,  blank=True, null=True)
    balance_after = models.DecimalField(max_digits=16, decimal_places=0)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    time = models.DateTimeField(auto_now_add=True)
    bank_info = models.ForeignKey(UserBankAccounts, on_delete=models.CASCADE)
    
    def __str__(self):
        action = "Rút" if self.is_withdraw else "Bán"
        return f"Bạn đã {action} {self.amount}VND. (Số tiền của bạn còn lại: {self.balance_after})"
        
    @property
    def is_withdraw(self):
        return self.transaction_type == 'W'
    @property
    def is_deposit(self):
        return self.transaction_type == 'D'
    @property
    def is_pending(self):
        return self.status == 'P'
    @property
    def is_completed(self):
        return self.status == 'C'
    @property
    def is_failed(self):
        return self.status == 'F'