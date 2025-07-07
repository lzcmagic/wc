"""
A股数据获取模块
使用akshare库获取免费的股票数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time

class StockDataFetcher:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1
    
    def get_stock_list(self):
        """获取A股列表（使用新浪接口，兼容受限网络）"""
        try:
            # 新浪财经 A 股行情（含实时数据及代码、名称）
            spot_df = ak.stock_zh_a_spot()

            # 保留代码与名称列，并重命名为统一字段
            stock_list = spot_df.rename(columns={'代码': 'code', '名称': 'name'})[['code', 'name']]
            return stock_list.reset_index(drop=True)
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            # 返回空 DataFrame 以便调用方处理
            return pd.DataFrame()
    
    def get_stock_data(self, stock_code, period=60):
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码，如 '000001'
            period: 获取天数，默认60天
        """
        for attempt in range(self.max_retries):
            try:
                # 计算开始日期
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')
                
                # 获取历史行情数据
                stock_data = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=""
                )
                
                if not stock_data.empty:
                    # AkShare 近期已调整返回字段，现统一使用映射方式重命名，避免列数不匹配
                    rename_map = {
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

                    stock_data = stock_data.rename(columns=rename_map)

                    # 去除不需要的列，如 '股票代码'
                    if '股票代码' in stock_data.columns:
                        stock_data = stock_data.drop(columns=['股票代码'])

                    stock_data['date'] = pd.to_datetime(stock_data['date'])
                    stock_data = stock_data.sort_values('date').reset_index(drop=True)
                    return stock_data
                    
            except Exception as e:
                print(f"获取股票 {stock_code} 数据失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return pd.DataFrame()
        
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