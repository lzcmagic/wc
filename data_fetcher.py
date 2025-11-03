"""
A股数据获取模块
使用akshare库获取免费的股票数据
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading
from functools import lru_cache, wraps
import functools
import os
import requests
from requests import sessions

# 可选引入 TuShare，作为后备数据源
try:
    import tushare as ts  # type: ignore
except Exception:
    ts = None  # 在运行时检测是否可用

# 读取环境变量（支持 .env）
try:
    from core.env_config import env_config
except Exception:
    env_config = None

class StockDataFetcher:
    # 类级别的锁，用于控制全局请求频率
    _request_lock = threading.Lock()
    _last_request_time = 0

    def __init__(self, config=None):
        # 移除重试机制，使用更长的请求间隔
        self.request_delay = 1.0  # 增加到1秒间隔，减少API调用压力
        self.headers = {
            'User-Agent': 'Mozilla/5.0 ...'
        }
        # 网络环境兼容性：显式为东财域名绕过代理，避免因本地或失效代理导致连接中断
        try:
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            # 常见本地代理地址未启动时会导致连接失败
            maybe_local_proxy = any(
                str(p).startswith('http://127.0.0.1') or str(p).startswith('http://localhost')
                for p in [http_proxy, https_proxy] if p
            )
            # 加入 NO_PROXY 直连东财域名，减少被动断连
            no_proxy = os.environ.get('NO_PROXY') or os.environ.get('no_proxy') or ''
            bypass_hosts = ['.eastmoney.com', 'push2.eastmoney.com', '82.push2.eastmoney.com']
            for host in bypass_hosts:
                if host not in no_proxy:
                    no_proxy = (no_proxy + ',' + host).strip(',') if no_proxy else host
            os.environ['NO_PROXY'] = no_proxy
            os.environ['no_proxy'] = no_proxy
            # 若检测到本地代理地址（可能未运行），则移除代理设置以保证可用性
            if maybe_local_proxy:
                for k in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy']:
                    if k in os.environ:
                        os.environ.pop(k, None)
            # 强制 requests 忽略环境代理设置（akshare内部使用requests）
            sessions.Session.trust_env = False
        except Exception:
            # 忽略代理处理中的异常，使用系统默认环境
            pass

    def _wait_for_rate_limit(self):
        """全局请求频率控制，确保并发环境下也能正确限流"""
        with self._request_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < self.request_delay:
                sleep_time = self.request_delay - time_since_last
                time.sleep(sleep_time)

            self._last_request_time = time.time()

    def _get_tushare_pro(self):
        """获取 TuShare pro 实例（如不可用则返回 None）"""
        try:
            if 'ts' not in globals() or ts is None:
                return None
            token = None
            if env_config:
                token = env_config.get_str('TUSHARE_TOKEN', '')
            if not token:
                token = os.environ.get('TUSHARE_TOKEN', '')
            if not token:
                return None
            ts.set_token(token)
            return ts.pro_api(token)
        except Exception:
            return None

    def _stock_code_to_ts_code(self, code: str) -> str:
        code = str(code).zfill(6)
        if code.startswith('6'):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"

    def _tushare_fetch_all_stocks(self) -> pd.DataFrame:
        """使用 TuShare 获取全量股票列表(仅code,name)，无需付费权限"""
        pro = self._get_tushare_pro()
        if pro is None:
            raise RuntimeError('TuShare 未配置或不可用')
        basics = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        if basics is None or basics.empty:
            raise RuntimeError('TuShare stock_basic 为空')
        df = pd.DataFrame({
            'code': basics['symbol'].astype(str).str.zfill(6),
            'name': basics['name']
        })
        return df

    def _tushare_fetch_hist(self, stock_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """使用 TuShare 获取历史行情，返回与 akshare 对齐的列"""
        pro = self._get_tushare_pro()
        if pro is None:
            raise RuntimeError('TuShare 未配置或不可用')
        ts_code = self._stock_code_to_ts_code(stock_code)
        try:
            # TuShare 的 pro_bar 直接使用全局 ts 接口
            # 需要先确保已经 set_token
            # 在 _get_tushare_pro 中已经 set_token
            df = ts.pro_bar(ts_code=ts_code,
                            start_date=start_date.strftime('%Y%m%d'),
                            end_date=end_date.strftime('%Y%m%d'),
                            adj='qfq',
                            freq='D')
            if df is None or df.empty:
                raise RuntimeError('TuShare pro_bar 返回空')
            # 对齐列名
            mapping = {
                'trade_date': 'date',
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'vol': 'volume',
                'amount': 'turnover'
            }
            keep = [k for k in mapping.keys() if k in df.columns]
            df = df[keep].copy()
            df.rename(columns=mapping, inplace=True)
            # 类型转换
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date')
        except Exception as e:
            raise RuntimeError(f'TuShare 历史行情获取失败: {e}')

    def get_all_stocks_with_market_cap(self):
        """
        获取当前所有A股的列表及其市值信息。
        此函数在数据源头进行预筛选，以提高后续处理效率。
        筛选逻辑:
        1. 排除ST、*ST和退市股票。
        2. 只保留总市值在30亿到500亿之间的股票。
        """
        print(f"   - 正在获取全量A股列表并进行预筛选...")
        cache_path = os.path.join('cache', 'all_a_list.csv')
        max_retries = 5
        base_delay = 1.0
        try:
            df = pd.DataFrame()
            last_err = None
            for i in range(max_retries):
                try:
                    # 限流以避免过频调用
                    self._wait_for_rate_limit()
                    df = ak.stock_zh_a_spot_em()
                    if not df.empty:
                        break
                except Exception as e:
                    last_err = e
                # 指数退避
                time.sleep(base_delay * (2 ** i))
            if df.empty:
                # 在线失败，尝试使用本地缓存
                if os.path.exists(cache_path):
                    print("   - 在线获取失败，使用本地缓存 all_a_list.csv 作为回退数据")
                    try:
                        df = pd.read_csv(cache_path)
                    except Exception:
                        df = pd.DataFrame()
                if df.empty:
                    # 尝试 TuShare 后备
                    try:
                        print("   - Eastmoney 接口失败，尝试使用 TuShare 后备数据源...")
                        df = self._tushare_fetch_all_stocks()
                    except Exception as e2:
                        last_err = e2
                if df.empty:
                    raise RuntimeError(f"无法获取全量A股列表，且无缓存可用: {last_err}")

            # 预筛选前股票数量
            original_count = len(df)
            print(f"   - 获取到 {original_count} 只股票，开始进行市值和状态筛选...")

            # 1. 筛选掉ST、*ST、退市股和新股
            name_col = '名称' if '名称' in df.columns else 'name'
            df = df[~df[name_col].astype(str).str.contains('ST|退|N |C ', na=False)]
            after_st_filter_count = len(df)
            print(f"   - 排除ST、退市股、新股后剩余: {after_st_filter_count} 只")

            # 2. 筛选总市值在50亿到200亿之间的股票 (提高门槛，聚焦优质股票)
            total_cap_col = '总市值' if '总市值' in df.columns else ('total_market_cap' if 'total_market_cap' in df.columns else None)
            if total_cap_col is not None:
                df = df[df[total_cap_col].between(50 * 1e8, 200 * 1e8)]
                after_cap_filter_count = len(df)
                print(f"   - 市值筛选 (50亿-200亿) 后剩余: {after_cap_filter_count} 只")
            else:
                print("   - 当前数据源缺少总市值列，跳过市值筛选")

            # 3. 筛选成交量活跃的股票 (排除成交量过低的股票)
            if '成交量' in df.columns:
                volume_threshold = df['成交量'].quantile(0.3)  # 保留成交量前70%的股票
                df = df[df['成交量'] >= volume_threshold]
                after_volume_filter_count = len(df)
                print(f"   - 成交量筛选后剩余: {after_volume_filter_count} 只")

            # 统一列名
            code_col = '代码' if '代码' in df.columns else 'code'
            name_col = '名称' if '名称' in df.columns else 'name'
            total_cap_col = '总市值' if '总市值' in df.columns else ('total_market_cap' if 'total_market_cap' in df.columns else None)
            flow_cap_col = '流通市值' if '流通市值' in df.columns else ('market_cap' if 'market_cap' in df.columns else None)

            # 若没有市值列（TuShare免费路径），则跳过市值过滤并设置占位列
            if total_cap_col is None or flow_cap_col is None:
                print("   - 未获取到市值列，暂时跳过市值过滤（TuShare免费路径）")
                df = df[[code_col, name_col]].copy()
                df['total_market_cap'] = np.nan
                df['market_cap'] = np.nan
            else:
                df = df[[code_col, name_col, total_cap_col, flow_cap_col]].copy()
                df.columns = ['code', 'name', 'total_market_cap', 'market_cap']
                df['code'] = df['code'].astype(str)
                df = df.dropna(subset=['market_cap'])

            final_count = len(df)
            print(f"   - ✅ 预筛选完成，最终候选股票数量: {final_count} (从 {original_count} 筛选而来)")

            # 写入缓存以便下次失败回退
            try:
                os.makedirs('cache', exist_ok=True)
                df.to_csv(cache_path, index=False)
            except Exception:
                pass

            return df
        except Exception as e:
            print(f"❌ 获取全量A股列表失败: {e}")
            return pd.DataFrame()
    
    def get_stock_data(self, stock_code, period=120, end_date=None):
        """
        获取股票历史数据，并健壮地处理列名不匹配的问题。
        移除重试机制以提高处理速度，失败的股票直接跳过。

        Args:
            stock_code: 股票代码，如 '000001'
            period: 获取天数，默认120天
            end_date: 结束日期，默认为当前日期
        """
        if end_date is None:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=period * 1.5) # 获取更多数据以计算指标

        try:
            # 使用全局请求频率控制，确保并发环境下也能正确限流
            self._wait_for_rate_limit()

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
            # Eastmoney 失败时尝试 TuShare 回退
            try:
                return self._tushare_fetch_hist(stock_code, start_date, end_date)
            except Exception as e2:
                print(f"❌ 获取 {stock_code} 历史数据失败: {e} | 回退失败: {e2}")
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
                
            # 避免请求过于频繁，使用全局频率控制
            self._wait_for_rate_limit()
        
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
