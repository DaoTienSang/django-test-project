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

