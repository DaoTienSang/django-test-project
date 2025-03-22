from vnstock import Vnstock


stock = Vnstock().stock(source='VCI')

def get_list_stock_market():
    return stock.listing.all_symbols().ticker.values      # danh sách các mã chứng khoán niêm yết


# == hàm lấy mã cổ phiếu và tên công ty
def get_ticker_companyname():
    list_ticker = [
        {"ticker": row[0], "organ_name": row[1]}
        for row in stock.listing.all_symbols().itertuples(index=False, name=None)
    ]
    return list_ticker


# Lấy giá khớp lệnh gần nhất của cổ phiếu
def get_match_price(stock_code):
    return int(stock.trading.price_board(symbols_list=['AAA'])[('match', 'match_price')].iloc[0])


# class VnstockServices:
#     stock = None  # Khai báo biến class để lưu trữ đối tượng stock

#     @classmethod
#     def initialize(cls):
#         from vnstock import Vnstock
#         """Khởi tạo dữ liệu nếu chưa có"""
#         if cls.stock is None:
#             cls.stock = Vnstock().stock(source='VCI')

#     @classmethod
#     def get_list_stock(cls):
#         """Lấy danh sách mã chứng khoán niêm yết"""
#         cls.initialize()  # Đảm bảo đã khởi tạo stock trước khi gọi
#         return cls.stock.listing.all_symbols()['ticker'].values