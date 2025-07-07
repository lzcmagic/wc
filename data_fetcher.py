"""
A股数据获取模块
使用akshare库获取免费的股票数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
from functools import lru_cache

class StockDataFetcher:
    def __init__(self, config=None):
        self.max_retries = 3
        self.retry_delay = 1
        self.headers = {
            'User-Agent': 'Mozilla/5.0 ...'
        }
    
    @lru_cache(maxsize=1)
    def get_trade_days(self, start_date, end_date):
        """获取指定时间范围内的所有交易日"""
        try:
            df = ak.tool_trade_date_hist_sina()
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            trade_days = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            return trade_days['trade_date'].tolist()
        except Exception as e:
            print(f"❌ 获取交易日历失败: {e}")
            return pd.date_range(start=start_date, end=end_date, freq='B').tolist()

    @lru_cache(maxsize=128)
    def get_stock_list(self, for_date=None):
        """
        获取A股所有股票列表及其市值信息。
        如果指定 for_date，则获取该日期的市值快照。
        """
        print(f"   - 正在获取A股列表 (日期: {for_date or '最新'})...")
        try:
            # akshare.stock_zh_a_spot_em() 可以获取最新的数据
            date_str = for_date.strftime('%Y%m%d') if for_date else datetime.now().strftime('%Y%m%d')
            # 使用一个能获取指定日期市值的接口
            df = ak.stock_zh_a_hist(period="daily", start_date=date_str, end_date=date_str, adjust="qfq")
            if df.empty: return pd.DataFrame()

            # 数据清洗和重命名
            df = df[['代码', '名称', '最新价', '总市值', '流通市值']].copy()
            df.columns = ['code', 'name', 'price', 'total_market_cap', 'market_cap']
            
            # 清理代码，确保格式正确
            df['code'] = df['code'].astype(str)
            return df
        except Exception as e:
            print(f"❌ 获取A股列表失败: {e}")
            return pd.DataFrame()
    
    @lru_cache(maxsize=512)
    def get_stock_data(self, stock_code, period=120, end_date=None):
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码，如 '000001'
            period: 获取天数，默认120天
            end_date: 结束日期，默认为当前日期
        """
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=period * 1.5) # 获取更多数据以计算指标

        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"  # 前复权
            )
            # ... 此处省略数据清洗和重命名 ...
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude', 'change_pct', 'change_amount', 'turnover_rate']
            df['date'] = pd.to_datetime(df['日期'])
            return df
        except Exception as e:
            print(f"❌ 获取 {stock_code} 历史数据失败: {e}")
            return pd.DataFrame()
            
    def get_stock_info(self, stock_code):
        """获取股票基本信息"""
        try:
            # 获取股票基本信息
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            
            # 获取实时价格
            current_price = ak.stock_zh_a_spot_em()
            current_price = current_price[current_price['代码'] == stock_code]
            
            info = {}
            if not stock_info.empty:
                for _, row in stock_info.iterrows():
                    info[row['item']] = row['value']
            
            if not current_price.empty:
                info['current_price'] = current_price.iloc[0]['最新价']
                info['change_pct'] = current_price.iloc[0]['涨跌幅']
            
            return info
            
        except Exception as e:
            print(f"获取股票 {stock_code} 信息失败: {e}")
            return {}
    
    def get_market_cap(self, stock_code):
        """获取股票市值信息"""
        try:
            # 获取市值数据
            market_data = ak.stock_zh_a_spot_em()
            stock_market = market_data[market_data['代码'] == stock_code]
            
            if not stock_market.empty:
                return {
                    'market_cap': stock_market.iloc[0]['总市值'],
                    'circulation_market_cap': stock_market.iloc[0]['流通市值']
                }
            return {'market_cap': 0, 'circulation_market_cap': 0}
            
        except Exception as e:
            print(f"获取股票 {stock_code} 市值失败: {e}")
            return {'market_cap': 0, 'circulation_market_cap': 0}
    
    def filter_stocks(self, stock_list, min_market_cap=5000000000):
        """
        基础股票过滤
        
        Args:
            stock_list: 股票列表DataFrame
            min_market_cap: 最小流通市值，默认50亿
        """
        filtered_stocks = []
        
        for _, stock in stock_list.iterrows():
            stock_code = stock['code']
            stock_name = stock['name']
            
            # 过滤ST股票
            if 'ST' in stock_name or '*ST' in stock_name:
                continue
            
            # 过滤退市风险股
            if '退' in stock_name:
                continue
            
            # 获取市值信息
            market_info = self.get_market_cap(stock_code)
            if market_info['circulation_market_cap'] < min_market_cap:
                continue
            
            # 获取近期涨幅
            recent_data = self.get_stock_data(stock_code, 30)
            if recent_data.empty:
                continue
            
            recent_gain = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[0] - 1) * 100
            if recent_gain > 30:  # 过滤近30日涨幅超过30%的股票
                continue
            
            filtered_stocks.append({
                'code': stock_code,
                'name': stock_name,
                'market_cap': market_info['circulation_market_cap'],
                'recent_gain': recent_gain
            })
            
            # 为了演示，限制处理数量
            if len(filtered_stocks) >= 50:
                break
                
            # 避免请求过于频繁
            time.sleep(0.1)
        
        return pd.DataFrame(filtered_stocks)

    def get_prices_for_date(self, stocks, for_date):
        """获取一批股票在特定日期的收盘价"""
        if not stocks:
            return {}
        
        date_str = for_date.strftime('%Y%m%d')
        prices = {}
        
        # 优化: 一次性获取当日所有股票行情
        try:
            all_prices_df = ak.stock_zh_a_hist(period="daily", start_date=date_str, end_date=date_str, adjust="qfq")
            if all_prices_df.empty:
                return {}
            
            stock_codes = [s['code'] for s in stocks]
            
            # 从当日行情中筛选出我们需要的股票价格
            target_prices_df = all_prices_df[all_prices_df['代码'].isin(stock_codes)]
            
            for _, row in target_prices_df.iterrows():
                prices[row['代码']] = row['收盘']
                
            return prices
            
        except Exception as e:
            print(f"❌ 获取 {date_str} 的价格失败: {e}")
            return {}

# 测试代码
if __name__ == "__main__":
    fetcher = StockDataFetcher()
    
    # 测试获取股票数据
    print("正在获取平安银行数据...")
    data = fetcher.get_stock_data('000001')
    if not data.empty:
        print(f"成功获取 {len(data)} 条数据")
        print(data.tail())
    else:
        print("获取数据失败")
    
    # 测试获取股票信息
    print("\n正在获取股票信息...")
    info = fetcher.get_stock_info('000001')
    print(info) 