from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import WalletTransactionSerializer

from .vnstock_services import get_match_price

from .models import WalletTransactions


# ======= API để lấy chi tiết lịch sử giao dịch =========
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, id):
    transaction = get_object_or_404(WalletTransactions, id=id, user=request.user)
    serializer = WalletTransactionSerializer(transaction)
    return Response(serializer.data)


# ========== API LẤY GIÁ CỔ PHIẾU ======================= 
@api_view(['GET'])
def stock_price_api(request, stock_code):
    """API lấy giá khớp lệnh của mã chứng khoán"""
    match_price = get_match_price(stock_code)
    
    if match_price is not None:
        return Response({
            "stock_code": stock_code,
            "match_price": match_price
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "error": "Không tìm thấy giá cổ phiếu hoặc mã không hợp lệ!"
        }, status=status.HTTP_400_BAD_REQUEST)
