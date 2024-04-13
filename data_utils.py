from datetime import datetime, timedelta
import akshare as ak
from cachetools import TTLCache, cached
# 设置缓存时间为2小时
cache = TTLCache(maxsize=None, ttl=7200)  # maxsize=None 表示不限制缓存大小

# 定义一个函数来计算开始日期
def calculate_start_date(end_date, num_days):
    end_date_obj = datetime.strptime(end_date, '%Y%m%d')
    start_date_obj = end_date_obj - timedelta(days=num_days)
    return start_date_obj.strftime('%Y%m%d')

def calculate_return_rates(etf_codes, end_date):
    periods = [1, 5, 10, 20, 60]
    return_rates = {f"{p}日": {} for p in periods}
    start_date = calculate_start_date(end_date, 60*2)  # 往前推120天作为开始日期
    
    for name, code in etf_codes.items():
        try:
            # 获取ETF历史数据，只获取从开始日期到结束日期的数据
            df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            # 确保获取足够的数据行
            if len(df) >= max(periods):
                # 计算不同时间尺度的涨跌幅
                latest_close = df['收盘'].iloc[-1]  # 最新的收盘价
                for period in periods:
                    if len(df) >= period:
                        past_close = df['收盘'].iloc[-period-1]  # period天前的收盘价
                        return_rate = (latest_close - past_close) / past_close * 100  # 转换为百分比
                        return_rates[f"{period}日"][name] = return_rate
            else:
                continue  # 如果数据不足，跳过当前ETF
        except Exception as e:
            print(f"Error fetching data for ETF {name}: {e}")
            continue  # 发生错误时跳过当前ETF
    
    # 删除所有值为None的键值对
    for period in return_rates.keys():
        return_rates[period] = {k: v for k, v in return_rates[period].items() if v is not None}
    return return_rates

def format_return_rates(return_rates):
    formatted_rates = {}
    for period, rates in return_rates.items():
        formatted_rates[period] = {k: round(v, 2) for k, v in rates.items()}
    return formatted_rates

def get_index_data(symbol, start_date, end_date):
    return ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)

def get_north_fund_flow_data(symbol):
    return ak.stock_hsgt_north_net_flow_in_em(symbol=symbol)

def get_south_fund_flow_data(symbol):
    return ak.stock_hsgt_south_net_flow_in_em(symbol=symbol)

def get_zt_pool_strong_data(date):
    return ak.stock_zt_pool_strong_em(date=date)

def get_zt_pool_previous_data(date):
    return ak.stock_zt_pool_previous_em(date=date)

def get_latest_trade_date():
    """
    获取最近的交易日期。

    如果今天是交易日，则返回今天的日期；
    否则，返回过去离今天最近的交易日期。
    """
    today = datetime.now().date()
    trade_dates_df = ak.tool_trade_date_hist_sina()
    trade_dates = trade_dates_df["trade_date"].tolist()
    
    if today in trade_dates:
        return today.strftime("%Y%m%d")
    else:
        # 找到过去离今天最近的交易日期
        for date in reversed(trade_dates):
            if date < today:
                return date.strftime("%Y%m%d")
