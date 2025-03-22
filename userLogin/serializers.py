from rest_framework import serializers
from .models import WalletTransactions, UserBankAccounts



class UserBankAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBankAccounts
        fields = ['bank_name', 'account_number', 'account_name']


class WalletTransactionSerializer(serializers.ModelSerializer):
    bank_info = UserBankAccountsSerializer()

    status_display = serializers.SerializerMethodField()
    transaction_type_display = serializers.SerializerMethodField()

    class Meta:
        model = WalletTransactions
        fields = ['id', 'time', 'amount', 'transaction_type', 'description', 'balance_after', 'status', 'bank_info', 'status_display', 'transaction_type_display']

    def get_status_display(self, obj):
        return obj.get_status_display()  # Lấy chuỗi đầy đủ từ STATUS_CHOICES

    def get_transaction_type_display(self, obj):
        return obj.get_transaction_type_display()  # Lấy chuỗi đầy đủ từ TRANSACTION_TYPE_CHOICES
    

