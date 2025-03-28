from datetime import datetime


from vnstock import Vnstock


stock = Vnstock().stock(source='VCI')

def get_list_stock_market():
    return stock.listing.all_symbols().ticker.values      # danh sách các mã chứng khoán niêm yết


# - hàm lấy mã cổ phiếu và tên công ty
def get_ticker_companyname():
    list_ticker = [
        {"ticker": row[0], "organ_name": row[1]}
        for row in stock.listing.all_symbols().itertuples(index=False, name=None)
    ]
    return list_ticker


# - Lấy giá khớp lệnh gần nhất của cổ phiếu
def get_refer_price(stock_code):
    try:
        data = stock.trading.price_board(symbols_list=[stock_code])
        ref_price = int(data[('listing', 'ref_price')].iloc[0])
        return ref_price
    except Exception as e:
        return f'Không tìm thấy mã cổ phiếu {stock_code}!'


# ===== Lấy thông tin bảng giá thị trường ====
def get_price_board():
    return stock.trading.price_board(symbols_list=list(stock.listing.all_symbols().ticker.values))


# ==== Lấy giá lịch sử ====
def get_historical_data(stock_code):
    today = datetime.now().strftime('%Y-%m-%d')
    return Vnstock().stock(symbol=stock_code, source='VCI').quote.history(start='2000-01-01', end=today)