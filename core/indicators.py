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

    @staticmethod
    def check_volume_amplification(volume_series, period=5, threshold=1.5):
        """
        检查成交量是否放大

        Args:
            volume_series: 成交量序列
            period: 比较周期，默认5天
            threshold: 放大倍数阈值，默认1.5倍

        Returns:
            bool: 是否成交量放大
        """
        if len(volume_series) < period + 1:
            return False

        try:
            # 计算最近一天的成交量与前period天平均成交量的比值
            recent_volume = volume_series.iloc[-1]
            avg_volume = volume_series.iloc[-(period+1):-1].mean()

            if avg_volume == 0:
                return False

            volume_ratio = recent_volume / avg_volume
            return volume_ratio >= threshold

        except Exception:
            return False

    @staticmethod
    def check_ma_bullish_arrangement(close_series, periods=[5, 10, 20]):
        """
        检查均线多头排列

        Args:
            close_series: 收盘价序列
            periods: 均线周期列表，默认[5, 10, 20]

        Returns:
            bool: 是否均线多头排列
        """
        if len(close_series) < max(periods):
            return False

        try:
            # 计算各周期均线
            mas = []
            for period in periods:
                ma = close_series.rolling(window=period).mean()
                if ma.empty or pd.isna(ma.iloc[-1]):
                    return False
                mas.append(ma.iloc[-1])

            # 检查是否多头排列（短期均线 > 中期均线 > 长期均线）
            for i in range(len(mas) - 1):
                if mas[i] <= mas[i + 1]:
                    return False

            return True

        except Exception:
            return False


class EnhancedStockScorer:
    """增强版技术指标评分器"""
    
    def __init__(self):
        # 基础权重
        self.base_weights = {
            'macd': 0.20,
            'rsi': 0.15,
            'kdj': 0.15,
            'bollinger': 0.12,
            'volume': 0.18,  # 提升成交量权重
            'ma': 0.10,
            'adx': 0.10      # 新增趋势强度
        }
        self.last_reasons = []
    
    def calculate_enhanced_score(self, stock_data, market_trend='neutral'):
        """
        增强版评分系统
        """
        if stock_data.empty or len(stock_data) < 60:
            return 0, []
        
        try:
            # 1. 动态权重调整
            weights = self._adjust_weights_by_market(market_trend)
            
            # 2. 计算各项指标
            scores = self._calculate_all_indicators(stock_data)
            
            # 3. 多指标组合确认
            confirmed_signals = self._cross_validate_signals(scores, stock_data)
            
            # 4. 趋势强度加权
            trend_strength = self._calculate_trend_strength(stock_data)
            
            # 5. 综合评分
            total_score = self._weighted_score(scores, weights, trend_strength)
            
            # 6. 生成推荐理由
            reasons = self._generate_reasons(confirmed_signals, trend_strength)
            
            return min(100, max(0, total_score)), reasons
            
        except Exception as e:
            print(f"增强评分计算错误: {e}")
            return 0, []
    
    def _adjust_weights_by_market(self, market_trend):
        """根据市场趋势动态调整权重"""
        weights = self.base_weights.copy()
        
        if market_trend == 'bull':
            # 牛市：加重趋势指标
            weights['macd'] *= 1.2
            weights['ma'] *= 1.3
            weights['volume'] *= 1.1
        elif market_trend == 'bear':
            # 熊市：加重超跌指标
            weights['rsi'] *= 1.3
            weights['bollinger'] *= 1.2
            weights['kdj'] *= 1.1
        elif market_trend == 'volatile':
            # 震荡市：加重ADX和成交量
            weights['adx'] *= 1.4
            weights['volume'] *= 1.2
            
        # 归一化权重
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
    
    def _calculate_all_indicators(self, stock_data):
        """计算所有技术指标得分"""
        scores = {}
        
        # MACD
        scores['macd'] = self._score_macd_enhanced(stock_data)
        
        # RSI
        scores['rsi'] = self._score_rsi_enhanced(stock_data)
        
        # KDJ
        scores['kdj'] = self._score_kdj_enhanced(stock_data)
        
        # 布林带
        scores['bollinger'] = self._score_bollinger_enhanced(stock_data)
        
        # 成交量（增强版）
        scores['volume'] = self._score_volume_enhanced(stock_data)
        
        # 均线
        scores['ma'] = self._score_ma_enhanced(stock_data)
        
        # ADX趋势强度
        scores['adx'] = self._score_adx(stock_data)
        
        return scores
    
    def _score_macd_enhanced(self, data):
        """增强版MACD评分"""
        score = 0
        macd = TechnicalIndicators.calculate_macd(data['close'])
        
        if macd.empty:
            return 0
            
        # 金叉确认
        if len(macd) >= 2:
            if macd.iloc[-1] > 0 and macd.iloc[-2] <= 0:
                score += 30  # 金叉
            elif macd.iloc[-1] > macd.iloc[-2] > 0:
                score += 20  # 加速上涨
            elif macd.iloc[-1] > 0:
                score += 10  # 零轴上方
        
        # MACD柱状图趋势
        if len(macd) >= 3:
            recent_trend = macd.iloc[-3:].diff().mean()
            if recent_trend > 0:
                score += 10  # 向上趋势
                
        return min(100, score)
    
    def _score_volume_enhanced(self, data):
        """增强版成交量评分"""
        score = 0
        volume = data['volume']
        close = data['close']
        
        # 1. 成交量放大
        if self._check_volume_breakout(volume):
            score += 25
        
        # 2. 量价配合
        if self._check_price_volume_confirmation(close, volume):
            score += 20
        
        # 3. OBV资金流向
        obv_score = self._calculate_obv_score(close, volume)
        score += obv_score
        
        # 4. 换手率分析
        turnover_score = self._analyze_turnover_rate(volume, data.get('market_cap', 0))
        score += turnover_score
        
        return min(100, score)
    
    def _check_volume_breakout(self, volume, lookback=20, threshold=2.0):
        """检查成交量突破"""
        if len(volume) < lookback + 1:
            return False
        
        recent_avg = volume.iloc[-5:].mean()
        historical_avg = volume.iloc[-(lookback+5):-5].mean()
        
        return recent_avg > historical_avg * threshold
    
    def _check_price_volume_confirmation(self, close, volume):
        """检查量价配合"""
        if len(close) < 5:
            return False
        
        price_trend = close.iloc[-5:].diff().mean()
        volume_trend = volume.iloc[-5:].diff().mean()
        
        # 价涨量增或价跌量缩
        return (price_trend > 0 and volume_trend > 0) or (price_trend < 0 and volume_trend < 0)
    
    def _calculate_trend_strength(self, data):
        """计算趋势强度"""
        adx_series, plus_di, minus_di = TechnicalIndicators.calculate_adx(
            data['high'], data['low'], data['close']
        )
        
        if adx_series.empty:
            return 0.5  # 中性
        
        adx_value = adx_series.iloc[-1] if not pd.isna(adx_series.iloc[-1]) else 25
        
        # ADX > 25 为强趋势
        if adx_value > 40:
            return 1.0  # 强趋势
        elif adx_value > 25:
            return 0.8  # 中等趋势
        else:
            return 0.6  # 弱趋势


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
    
    def calculate_score(self, stock_data, config=None):
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
            return score, reasons

        except Exception as e:
            print(f"计算评分时出错: {e}")
            return 0, []
    
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
                        except (ValueError, TypeError):
                            pass
                    elif 'PB' in item or '市净率' in item:
                        try:
                            result['pb_ratio'] = float(value)
                        except (ValueError, TypeError):
                            pass
                    elif 'ROE' in item or '净资产收益率' in item:
                        try:
                            result['roe'] = float(value.replace('%', ''))
                        except (ValueError, TypeError):
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
                
        except Exception as e:
            print(f"获取行业信息失败: {e}")
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