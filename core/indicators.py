"""
技术指标计算模块
包含常用的股票技术分析指标
"""

import pandas as pd
import numpy as np
import pandas_ta as ta

# 兼容 numpy 2.x 移除了 NaN 常量的问题，供 pandas-ta 导入
if not hasattr(np, 'NaN'):
    np.NaN = np.nan  # type: ignore[attr-defined]

class TechnicalIndicators:
    """封装各类技术指标的计算"""

    @staticmethod
    def calculate_macd(close_prices, fast=12, slow=26, signal=9):
        macd_line = ta.macd(close_prices, fast=fast, slow=slow, signal=signal)
        if macd_line is None or macd_line.empty:
            return pd.DataFrame()
        return macd_line.iloc[:, 0]

    @staticmethod
    def calculate_rsi(close_prices, period=14):
        return ta.rsi(close_prices, length=period)

    @staticmethod
    def calculate_kdj(high_prices, low_prices, close_prices, n=9, m1=3, m2=3):
        """计算KDJ指标"""
        kdj_df = ta.kdj(high_prices, low_prices, close_prices, length=n, signal=m1)
        # pandas-ta returns K, D, J - we might need to adjust based on usage
        return kdj_df

    @staticmethod
    def calculate_bollinger_bands(close_prices, period=20, std_dev=2):
        """计算布林带"""
        return ta.bbands(close_prices, length=period, std=std_dev)
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """计算真实波动范围 (ATR)"""
        return ta.atr(high, low, close, length=period)

    @staticmethod
    def calculate_adx(high, low, close, period=14):
        """计算平均趋向指数 (ADX) - 趋势强度指标"""
        adx_df = ta.adx(high, low, close, length=period)
        if adx_df is None or adx_df.empty:
            return pd.Series(dtype='float64'), pd.Series(dtype='float64'), pd.Series(dtype='float64')
        
        adx_series = adx_df.iloc[:, 0]
        plus_di = adx_df.iloc[:, 1]
        minus_di = adx_df.iloc[:, 2]
        return adx_series, plus_di, minus_di

    @staticmethod
    def calculate_williams_r(high, low, close, period=14):
        """计算威廉指标 %R"""
        return ta.willr(high, low, close, length=period)
    
    @staticmethod
    def calculate_cci(high, low, close, period=20):
        """计算顺势指标 (CCI)"""
        return ta.cci(high, low, close, length=period)

    @staticmethod
    def calculate_trix(close, period=14):
        """计算TRIX指标 - 三重指数平滑移动平均"""
        return ta.trix(close, length=period).iloc[:, 0]
    
    @staticmethod
    def calculate_obv(close, volume):
        """计算能量潮指标 (OBV)"""
        return ta.obv(close, volume)


class StockScorer:
    """根据技术指标为股票打分"""

    def __init__(self):
        self.weights = {
            'macd': 0.25,
            'rsi': 0.20,
            'kdj': 0.20,
            'bollinger': 0.15,
            'volume': 0.10,
            'ma': 0.10
        }
        self.last_reasons = []
    
    def calculate_score(self, stock_data):
        """
        计算股票综合评分
        
        Args:
            stock_data: DataFrame包含OHLCV数据
        """
        if stock_data.empty or len(stock_data) < 30:
            return 0
        
        try:
            score = 0
            reasons = []
            
            # MACD 指标 (25% 权重)
            macd = TechnicalIndicators.calculate_macd(stock_data['close'])
            if not macd.empty:
                if macd.iloc[-1] > 0 and macd.iloc[-2] < 0:
                    score += 25
                    reasons.append("MACD金叉")
                if macd.iloc[-1] > 0:
                    score += 10
                    reasons.append("MACD在零轴上方")
            
            # RSI 指标 (20% 权重)
            rsi = TechnicalIndicators.calculate_rsi(stock_data['close'])
            if not rsi.empty:
                if rsi.iloc[-1] > 70:
                    score += 5
                    reasons.append("RSI超买")
                elif rsi.iloc[-1] < 30:
                    score += 20
                    reasons.append("RSI超卖")
                else:
                    score += 10
                    reasons.append("RSI正常")
            
            # KDJ 指标 (20% 权重)
            kdj = TechnicalIndicators.calculate_kdj(stock_data['high'], stock_data['low'], stock_data['close'])
            if not kdj.empty:
                k_line, d_line = kdj.iloc[:, 0], kdj.iloc[:, 1]
                if k_line.iloc[-1] > d_line.iloc[-1] and k_line.iloc[-2] < d_line.iloc[-2]:
                    score += 20
                    reasons.append("KDJ金叉")
                if kdj.iloc[-1, 2] < 20: # J值
                    score += 5
                    reasons.append("KDJ超卖")
            
            # 布林带 (15% 权重)
            bollinger = TechnicalIndicators.calculate_bollinger_bands(stock_data['close'])
            if not bollinger.empty:
                lower_band, upper_band = bollinger.iloc[:, 0], bollinger.iloc[:, 2]
                if stock_data['close'].iloc[-1] < lower_band.iloc[-1] * 1.05:
                    score += 15
                    reasons.append("接近布林带下轨")
            
            # 成交量 (10% 权重)
            volume_amplification = TechnicalIndicators.check_volume_amplification(stock_data['volume'])
            if volume_amplification:
                score += 10
                reasons.append("成交量放大")
            
            # 均线 (10% 权重)
            ma_bullish_arrangement = TechnicalIndicators.check_ma_bullish_arrangement(stock_data['close'])
            if ma_bullish_arrangement:
                score += 10
                reasons.append("均线多头排列")
            
            self.last_reasons = reasons
            return score
            
        except Exception as e:
            print(f"计算评分时出错: {e}")
            return 0
    
    def get_signal_reasons(self, stock_data=None):
        """获取最近一次评分的信号原因"""
        return self.last_reasons
        

class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self):
        self.cache = {}
    
    def get_financial_data(self, stock_code):
        """获取财务数据"""
        if stock_code in self.cache:
            return self.cache[stock_code]
        
        try:
            # 获取估值指标
            valuation = ak.stock_individual_info_em(symbol=stock_code)
            
            result = {
                'pe_ratio': None,
                'pb_ratio': None,
                'roe': None,
            }
            
            # 解析估值数据
            if not valuation.empty:
                for _, row in valuation.iterrows():
                    item = row['item']
                    value = row['value']
                    
                    if 'PE' in item or '市盈率' in item:
                        try:
                            result['pe_ratio'] = float(value)
                        except:
                            pass
                    elif 'PB' in item or '市净率' in item:
                        try:
                            result['pb_ratio'] = float(value)
                        except:
                            pass
                    elif 'ROE' in item or '净资产收益率' in item:
                        try:
                            result['roe'] = float(value.replace('%', ''))
                        except:
                            pass
            
            self.cache[stock_code] = result
            return result
            
        except Exception as e:
            print(f"获取 {stock_code} 财务数据失败: {e}")
            return {
                'pe_ratio': None,
                'pb_ratio': None,
                'roe': None,
            }
    
    def score_fundamentals(self, financial_data):
        """基本面评分"""
        score = 0
        reasons = []
        
        # PE估值评分 (0-20分)
        pe = financial_data.get('pe_ratio')
        if pe:
            if 10 <= pe <= 25:
                score += 20
                reasons.append("PE估值合理")
            elif 25 < pe <= 35:
                score += 10
                reasons.append("PE估值偏高")
            elif pe < 10:
                score += 15
                reasons.append("PE估值偏低")
        
        # PB估值评分 (0-15分)
        pb = financial_data.get('pb_ratio')
        if pb:
            if 1 <= pb <= 3:
                score += 15
                reasons.append("PB估值合理")
            elif pb < 1:
                score += 20
                reasons.append("PB估值偏低")
        
        # ROE盈利能力评分 (0-25分)
        roe = financial_data.get('roe')
        if roe:
            if roe >= 15:
                score += 25
                reasons.append("ROE优秀")
            elif roe >= 10:
                score += 15
                reasons.append("ROE良好")
            elif roe >= 5:
                score += 5
                reasons.append("ROE一般")
        
        return min(60, score), reasons

class MarketSentimentAnalyzer:
    """市场情绪分析器"""
    
    @staticmethod
    def calculate_turnover_momentum(volume, period=20):
        """计算成交量动量"""
        avg_volume = volume.rolling(window=period).mean()
        volume_ratio = volume / avg_volume
        return volume_ratio.fillna(1)
    
    @staticmethod
    def calculate_price_momentum(close, period=20):
        """计算价格动量"""
        return (close / close.shift(period) - 1) * 100
    
    @staticmethod
    def calculate_volatility_score(close, period=20):
        """计算波动率评分"""
        returns = close.pct_change()
        volatility = returns.rolling(window=period).std()
        
        # 低波动率给高分，高波动率给低分
        volatility_percentile = volatility.rolling(window=60).rank(pct=True)
        return (1 - volatility_percentile.fillna(0.5)) * 100

class IndustryAnalyzer:
    """行业分析器"""
    
    def get_industry_strength(self, stock_code):
        """获取行业强度"""
        try:
            # 获取行业信息
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            industry = None
            
            for _, row in stock_info.iterrows():
                if '行业' in row['item']:
                    industry = row['value']
                    break
            
            if not industry:
                return 50, "未知行业"
            
            # 简化的行业强度评分
            # 实际应该获取行业指数表现
            if industry in ['新能源', '半导体', '医药', '军工', '人工智能', '芯片']:
                return 80, f"{industry}(热门)"
            elif industry in ['银行', '保险', '地产', '石油']:
                return 30, f"{industry}(传统)"
            else:
                return 50, f"{industry}(一般)"
                
        except Exception:
            return 50, "未知行业"

def calculate_indicators(df, indicator_configs):
    """
    根据配置为DataFrame计算所有需要的技术指标。
    
    :param df: 包含OHLCV数据的Pandas DataFrame。
    :param indicator_configs: 策略配置中定义的指标列表。
    :return: 带有技术指标新列的DataFrame。
    """

    if df is None or df.empty:
        return df

    # 使用pandas-ta的strategy功能来批量计算
    strategy = ta.Strategy(
        name="Dynamic Strategy",
        description="Calculates indicators based on config",
        ta=indicator_configs
    )
    
    # 将指标附加到DataFrame上
    df.ta.strategy(strategy)
    
    return df