"""
A股数据获取模块
使用akshare库获取免费的股票数据
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from functools import lru_cache, wraps
import functools
import os
import requests
from requests import sessions

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

    def get_all_stocks_with_market_cap(self):
        """
        获取当前所有A股的列表及其市值信息。
        此函数在数据源头进行预筛选，以提高后续处理效率。
        筛选逻辑:
        1. 排除ST、*ST和退市股票。
        2. 只保留总市值在30亿到500亿之间的股票。
        """
        print(f"   - 正在获取全量A股列表并进行预筛选...")
        try:
            df = ak.stock_zh_a_spot_em()
            if df.empty: 
                print("   - 警告：未能从akshare获取到股票列表。")
                return pd.DataFrame()

            # 预筛选前股票数量
            original_count = len(df)
            print(f"   - 获取到 {original_count} 只股票，开始进行市值和状态筛选...")

            # 1. 筛选掉ST、*ST和退市股 (名称中包含'ST'或'退')
            df = df[~df['名称'].str.contains('ST|退', na=False)]
            after_st_filter_count = len(df)
            print(f"   - 排除ST和退市股后剩余: {after_st_filter_count} 只")

            # 2. 筛选总市值在30亿到300亿之间的股票 (修正单位问题)
            market_cap_min = 30 * 100000000  # 30亿
            market_cap_max = 300 * 100000000 # 300亿
            df = df[df['总市值'].between(market_cap_min, market_cap_max)]
            after_cap_filter_count = len(df)
            print(f"   - 市值筛选 (30亿-300亿) 后剩余: {after_cap_filter_count} 只")

            df = df[['代码', '名称', '总市值', '流通市值']].copy()
            df.columns = ['code', 'name', 'total_market_cap', 'market_cap']
            
            df['code'] = df['code'].astype(str)
            df = df.dropna(subset=['market_cap'])
            
            final_count = len(df)
            print(f"   - ✅ 预筛选完成，最终候选股票数量: {final_count} (从 {original_count} 筛选而来)")
            
            return df
        except Exception as e:
            print(f"❌ 获取全量A股列表失败: {e}")
            return pd.DataFrame()
    
    def get_stock_data(self, stock_code, period=120, end_date=None):
        """
        获取股票历史数据，并健壮地处理列名不匹配的问题。
        
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

            # --- 健壮的列处理方式 ---
            # 1. 定义我们需要的列和它们的映射关系
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'turnover',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '换手率': 'turnover_rate'
            }

            # 2. 只保留原始df中存在的、我们需要的列
            existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df[existing_columns.keys()].copy()

            # 3. 对这些存在的列进行重命名
            df.rename(columns=existing_columns, inplace=True)

            # 4. 类型转换
            df['date'] = pd.to_datetime(df['date'])
            
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
    
    def get_realtime_quotes(self, stock_codes: list) -> dict:
        """
        获取一批股票的实时行情快照。
        返回一个字典，key是股票代码，value是包含价格、涨跌幅等信息的字典。
        """
        if not stock_codes:
            return {}

        print(f"   - 正在获取 {len(stock_codes)} 只股票的实时行情...")
        try:
            # ak.stock_zh_a_spot_em() 不接受symbol参数，获取全部股票数据然后筛选
            df = ak.stock_zh_a_spot_em()
            if df.empty:
                return {}

            # 筛选出我们需要的股票
            df_filtered = df[df['代码'].isin(stock_codes)]

            # 将数据处理成 {code: {price: val, change_pct: val}} 的格式
            quotes = {}
            for _, row in df_filtered.iterrows():
                code = str(row['代码'])
                quotes[code] = {
                    'price': row['最新价'],
                    'change_pct': row['涨跌幅']
                }
            return quotes
        except Exception as e:
            print(f"❌ 获取实时行情失败: {e}")
            return {}

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
        
        try:
            date_str = for_date.strftime('%Y%m%d')
            all_prices_df = ak.stock_zh_a_hist(period="daily", start_date=date_str, end_date=date_str, adjust="qfq")
            if all_prices_df.empty:
                return {}
            
            stock_codes = [s['code'] for s in stocks]
            target_prices_df = all_prices_df[all_prices_df['代码'].isin(stock_codes)]
            
            return dict(zip(target_prices_df['代码'], target_prices_df['收盘']))
            
        except Exception as e:
            print(f"❌ 获取 {date_str} 的价格失败: {e}")
            return {}

    @lru_cache(maxsize=1)
    def get_fundamental_data(self, stock_code: str) -> dict:
        """
        获取单个股票的核心基本面数据 (PE, PB, ROE).
        使用 lru_cache 缓存结果以提高性能。
        """
        try:
            # akshare的这个接口可以提供非常详细的财务指标
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            if df.empty:
                return {}

            # 我们通常关心最新的季报或年报数据，这里取第一行
            latest_data = df.iloc[0]

            return {
                # 市盈率(TTM)
                'pe_ttm': latest_data.get('市盈率(TTM)', np.nan),
                # 市净率
                'pb': latest_data.get('市净率', np.nan),
                # 净资产收益率(ROE)
                'roe': latest_data.get('净资产收益率(加权)', np.nan)
            }
        except Exception as e:
            print(f"❌ 获取 {stock_code} 基本面数据失败: {e}")
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

    # 测试获取基本面数据
    print("\n正在获取平安银行基本面数据...")
    fundamentals = fetcher.get_fundamental_data('000001')
    if fundamentals:
        print(f"PE(TTM): {fundamentals.get('pe_ttm')}")
        print(f"PB: {fundamentals.get('pb')}")
        print(f"ROE: {fundamentals.get('roe')}")
    else:
        print("获取基本面数据失败") 
