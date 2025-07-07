"""
增强版选股指标系统
包含技术面、基本面、资金面、市场情绪等多维度指标
"""

import pandas as pd
import numpy as np
import akshare as ak
from indicators import TechnicalIndicators

class EnhancedIndicators(TechnicalIndicators):
    """增强版技术指标"""
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """计算真实波动范围 (ATR)"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_adx(high, low, close, period=14):
        """计算平均趋向指数 (ADX) - 趋势强度指标"""
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        atr = EnhancedIndicators.calculate_atr(high, low, close, period)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def calculate_williams_r(high, low, close, period=14):
        """计算威廉指标 %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)
        return wr
    
    @staticmethod
    def calculate_cci(high, low, close, period=20):
        """计算顺势指标 (CCI)"""
        typical_price = (high + low + close) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        
        cci = (typical_price - sma) / (0.015 * mad)
        return cci
    
    @staticmethod
    def calculate_trix(close, period=14):
        """计算TRIX指标 - 三重指数平滑移动平均"""
        ema1 = close.ewm(span=period).mean()
        ema2 = ema1.ewm(span=period).mean()
        ema3 = ema2.ewm(span=period).mean()
        
        trix = 100 * (ema3.diff() / ema3.shift())
        return trix
    
    @staticmethod
    def calculate_obv(close, volume):
        """计算能量潮指标 (OBV)"""
        obv = np.where(close > close.shift(), volume, 
               np.where(close < close.shift(), -volume, 0)).cumsum()
        return pd.Series(obv, index=close.index)

class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self):
        self.cache = {}
    
    def get_financial_data(self, stock_code):
        """获取财务数据"""
        if stock_code in self.cache:
            return self.cache[stock_code]
        
        try:
            # 获取基本财务指标
            financial_data = ak.stock_zh_a_hist_163(symbol=stock_code)
            
            # 获取估值指标
            valuation = ak.stock_individual_info_em(symbol=stock_code)
            
            result = {
                'pe_ratio': None,
                'pb_ratio': None,
                'roe': None,
                'debt_ratio': None,
                'revenue_growth': None,
                'profit_growth': None
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
                'debt_ratio': None,
                'revenue_growth': None,
                'profit_growth': None
            }
    
    def score_fundamentals(self, financial_data):
        """基本面评分"""
        score = 0
        reasons = []
        
        # PE估值评分 (0-20分)
        if financial_data['pe_ratio']:
            pe = financial_data['pe_ratio']
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
        if financial_data['pb_ratio']:
            pb = financial_data['pb_ratio']
            if 1 <= pb <= 3:
                score += 15
                reasons.append("PB估值合理")
            elif pb < 1:
                score += 20
                reasons.append("PB估值偏低")
        
        # ROE盈利能力评分 (0-25分)
        if financial_data['roe']:
            roe = financial_data['roe']
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
    def calculate_turnover_momentum(volume, close, period=20):
        """计算换手率动量"""
        # 简化的换手率计算（实际需要流通股本数据）
        avg_volume = volume.rolling(window=period).mean()
        volume_ratio = volume / avg_volume
        return volume_ratio
    
    @staticmethod
    def calculate_price_momentum(close, period=20):
        """计算价格动量"""
        return close / close.shift(period) - 1
    
    @staticmethod
    def calculate_volatility_score(close, period=20):
        """计算波动率评分"""
        returns = close.pct_change()
        volatility = returns.rolling(window=period).std()
        
        # 低波动率给高分，高波动率给低分
        volatility_percentile = volatility.rolling(window=60).rank(pct=True)
        return 1 - volatility_percentile  # 反转，低波动率高分

class IndustryAnalyzer:
    """行业分析器"""
    
    def __init__(self):
        self.industry_performance = {}
    
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
            if industry in ['新能源', '半导体', '医药', '军工']:
                return 80, f"{industry}(热门)"
            elif industry in ['银行', '保险', '地产']:
                return 30, f"{industry}(传统)"
            else:
                return 50, f"{industry}(一般)"
                
        except:
            return 50, "未知行业"

class EnhancedStockScorer:
    """增强版股票评分系统"""
    
    def __init__(self):
        self.weights = {
            # 技术面指标 (60%)
            'macd': 0.12,
            'rsi': 0.10,
            'kdj': 0.10,
            'bollinger': 0.08,
            'volume': 0.08,
            'ma': 0.06,
            'adx': 0.06,  # 新增：趋势强度
            
            # 基本面指标 (25%)
            'fundamentals': 0.25,
            
            # 市场情绪 (10%)
            'sentiment': 0.10,
            
            # 行业因子 (5%)
            'industry': 0.05
        }
        
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.industry_analyzer = IndustryAnalyzer()
    
    def calculate_enhanced_score(self, stock_data, stock_code):
        """计算增强版综合评分"""
        if stock_data.empty or len(stock_data) < 30:
            return 0, []
        
        try:
            total_score = 0
            all_reasons = []
            
            # 提取数据
            high = stock_data['high']
            low = stock_data['low']
            close = stock_data['close']
            volume = stock_data['volume']
            
            # 1. 技术指标评分
            tech_score, tech_reasons = self._calculate_technical_score(high, low, close, volume)
            total_score += tech_score * 0.6  # 技术面占60%
            all_reasons.extend(tech_reasons)
            
            # 2. 基本面评分
            fundamental_score, fund_reasons = self._calculate_fundamental_score(stock_code)
            total_score += fundamental_score * 0.25  # 基本面占25%
            all_reasons.extend(fund_reasons)
            
            # 3. 市场情绪评分
            sentiment_score, sent_reasons = self._calculate_sentiment_score(close, volume)
            total_score += sentiment_score * 0.10  # 市场情绪占10%
            all_reasons.extend(sent_reasons)
            
            # 4. 行业因子评分
            industry_score, industry_reason = self.industry_analyzer.get_industry_strength(stock_code)
            total_score += industry_score * 0.05  # 行业因子占5%
            all_reasons.append(industry_reason)
            
            return min(100, max(0, total_score)), all_reasons
            
        except Exception as e:
            print(f"计算增强评分时出错: {e}")
            return 0, []
    
    def _calculate_technical_score(self, high, low, close, volume):
        """计算技术面评分"""
        score = 0
        reasons = []
        
        # 原有技术指标
        from indicators import TechnicalIndicators, StockSignals
        
        # MACD评分
        dif, dea, macd = TechnicalIndicators.calculate_macd(close)
        if StockSignals.macd_golden_cross(dif, dea):
            score += 25
            reasons.append("MACD金叉")
        elif StockSignals.macd_above_zero(dif):
            score += 15
            reasons.append("MACD多头")
        
        # RSI评分
        rsi = TechnicalIndicators.calculate_rsi(close)
        if StockSignals.rsi_normal_range(rsi):
            score += 20
            reasons.append("RSI正常")
        elif StockSignals.rsi_oversold_rebound(rsi):
            score += 25
            reasons.append("RSI超卖反弹")
        
        # 新增：ADX趋势强度评分
        adx, plus_di, minus_di = EnhancedIndicators.calculate_adx(high, low, close)
        if adx.iloc[-1] > 25:  # 强趋势
            score += 15
            reasons.append("趋势强劲")
        elif adx.iloc[-1] > 20:
            score += 10
            reasons.append("趋势明确")
        
        # 新增：威廉指标评分
        wr = EnhancedIndicators.calculate_williams_r(high, low, close)
        if -20 <= wr.iloc[-1] <= -80:  # 正常范围
            score += 10
            reasons.append("威廉指标正常")
        
        # 成交量OBV评分
        obv = EnhancedIndicators.calculate_obv(close, volume)
        obv_ma = obv.rolling(window=10).mean()
        if obv.iloc[-1] > obv_ma.iloc[-1]:
            score += 15
            reasons.append("资金流入")
        
        return score, reasons
    
    def _calculate_fundamental_score(self, stock_code):
        """计算基本面评分"""
        financial_data = self.fundamental_analyzer.get_financial_data(stock_code)
        return self.fundamental_analyzer.score_fundamentals(financial_data)
    
    def _calculate_sentiment_score(self, close, volume):
        """计算市场情绪评分"""
        score = 0
        reasons = []
        
        # 价格动量
        momentum = MarketSentimentAnalyzer.calculate_price_momentum(close)
        if momentum.iloc[-1] > 0.05:  # 近期涨幅5%以上
            score += 15
            reasons.append("价格动量积极")
        
        # 成交量动量
        volume_momentum = MarketSentimentAnalyzer.calculate_turnover_momentum(volume, close)
        if volume_momentum.iloc[-1] > 1.5:  # 成交量放大
            score += 20
            reasons.append("成交活跃")
        
        # 波动率评分
        volatility_score = MarketSentimentAnalyzer.calculate_volatility_score(close)
        if volatility_score.iloc[-1] > 0.7:  # 低波动率
            score += 15
            reasons.append("波动率适中")
        
        return score, reasons

# 使用示例
def enhanced_stock_selection_demo():
    """增强版选股演示"""
    print("🚀 增强版选股系统演示")
    
    # 创建增强评分器
    enhanced_scorer = EnhancedStockScorer()
    
    # 测试股票
    test_stocks = ['000001', '000002', '600036']
    
    for stock_code in test_stocks:
        print(f"\n分析股票: {stock_code}")
        
        # 这里需要实际的股票数据
        # stock_data = get_stock_data(stock_code)
        # score, reasons = enhanced_scorer.calculate_enhanced_score(stock_data, stock_code)
        # print(f"综合评分: {score:.1f}")
        # print(f"推荐理由: {', '.join(reasons)}")

if __name__ == "__main__":
    enhanced_stock_selection_demo() 