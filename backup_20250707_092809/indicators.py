"""
技术指标计算模块
包含常用的股票技术分析指标
"""

import pandas as pd
import numpy as np

class TechnicalIndicators:
    
    @staticmethod
    def calculate_ma(prices, period):
        """计算移动平均线"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices, period):
        """计算指数移动平均线"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """
        计算MACD指标
        返回: DIF, DEA, MACD柱状图
        """
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)
        
        dif = ema_fast - ema_slow
        dea = TechnicalIndicators.calculate_ema(dif, signal)
        macd = (dif - dea) * 2
        
        return dif, dea, macd
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """计算RSI相对强弱指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_kdj(high, low, close, period=9, k_period=3, d_period=3):
        """计算KDJ指标"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        
        k = rsv.ewm(com=k_period-1).mean()
        d = k.ewm(com=d_period-1).mean()
        j = 3 * k - 2 * d
        
        return k, d, j
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """计算布林带"""
        ma = TechnicalIndicators.calculate_ma(prices, period)
        std = prices.rolling(window=period).std()
        
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        
        return upper, ma, lower
    
    @staticmethod
    def check_volume_amplification(volume, period=3, threshold=1.5):
        """检查成交量是否放大"""
        avg_volume = volume.rolling(window=period).mean()
        current_volume = volume.iloc[-1]
        avg_recent = avg_volume.iloc[-period-1:-1].mean()
        
        return current_volume > (avg_recent * threshold)
    
    @staticmethod
    def check_ma_bullish_arrangement(prices, periods=[5, 10, 20]):
        """检查均线多头排列"""
        mas = []
        for period in periods:
            ma = TechnicalIndicators.calculate_ma(prices, period)
            mas.append(ma.iloc[-1])
        
        # 检查是否为多头排列 (短期均线 > 中期均线 > 长期均线)
        return all(mas[i] > mas[i+1] for i in range(len(mas)-1))

class StockSignals:
    """股票买卖信号判断"""
    
    @staticmethod
    def macd_golden_cross(dif, dea):
        """MACD金叉信号"""
        if len(dif) < 2 or len(dea) < 2:
            return False
        
        # 当前DIF > DEA 且前一日 DIF <= DEA
        return (dif.iloc[-1] > dea.iloc[-1] and 
                dif.iloc[-2] <= dea.iloc[-2])
    
    @staticmethod
    def macd_above_zero(dif):
        """MACD在零轴上方"""
        return dif.iloc[-1] > 0
    
    @staticmethod
    def rsi_oversold_rebound(rsi, oversold=30):
        """RSI超卖反弹"""
        if len(rsi) < 2:
            return False
        
        # RSI从超卖区域反弹
        return (rsi.iloc[-2] <= oversold and 
                rsi.iloc[-1] > oversold)
    
    @staticmethod
    def rsi_normal_range(rsi, low=30, high=70):
        """RSI在正常范围内"""
        return low <= rsi.iloc[-1] <= high
    
    @staticmethod
    def kdj_golden_cross(k, d):
        """KDJ金叉"""
        if len(k) < 2 or len(d) < 2:
            return False
        
        return (k.iloc[-1] > d.iloc[-1] and 
                k.iloc[-2] <= d.iloc[-2])
    
    @staticmethod
    def bollinger_near_lower(prices, lower_band, threshold=0.02):
        """股价接近布林带下轨"""
        current_price = prices.iloc[-1]
        lower = lower_band.iloc[-1]
        
        return abs(current_price - lower) / lower <= threshold
    
    @staticmethod
    def bollinger_break_middle(prices, middle_band):
        """股价突破布林带中轨"""
        if len(prices) < 2:
            return False
        
        return (prices.iloc[-1] > middle_band.iloc[-1] and 
                prices.iloc[-2] <= middle_band.iloc[-2])

class StockScorer:
    """股票评分系统"""
    
    def __init__(self):
        self.weights = {
            'macd': 0.25,
            'rsi': 0.20,
            'kdj': 0.20,
            'bollinger': 0.15,
            'volume': 0.10,
            'ma': 0.10
        }
    
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
            
            # 提取数据
            high = stock_data['high']
            low = stock_data['low']
            close = stock_data['close']
            volume = stock_data['volume']
            
            # 计算技术指标
            dif, dea, macd = TechnicalIndicators.calculate_macd(close)
            rsi = TechnicalIndicators.calculate_rsi(close)
            k, d, j = TechnicalIndicators.calculate_kdj(high, low, close)
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(close)
            
            # MACD评分
            macd_score = 0
            if StockSignals.macd_golden_cross(dif, dea):
                macd_score = 25
            elif StockSignals.macd_above_zero(dif):
                macd_score = 15
            score += macd_score * self.weights['macd'] / 0.25
            
            # RSI评分
            rsi_score = 0
            if StockSignals.rsi_oversold_rebound(rsi):
                rsi_score = 25
            elif StockSignals.rsi_normal_range(rsi):
                rsi_score = 20
            score += rsi_score * self.weights['rsi'] / 0.20
            
            # KDJ评分
            kdj_score = 0
            if StockSignals.kdj_golden_cross(k, d) and j.iloc[-1] < 80:
                kdj_score = 20
            score += kdj_score * self.weights['kdj'] / 0.20
            
            # 布林带评分
            bb_score = 0
            if StockSignals.bollinger_near_lower(close, lower):
                bb_score = 15
            elif StockSignals.bollinger_break_middle(close, middle):
                bb_score = 12
            score += bb_score * self.weights['bollinger'] / 0.15
            
            # 成交量评分
            volume_score = 0
            if TechnicalIndicators.check_volume_amplification(volume):
                volume_score = 10
            score += volume_score * self.weights['volume'] / 0.10
            
            # 均线评分
            ma_score = 0
            if TechnicalIndicators.check_ma_bullish_arrangement(close):
                ma_score = 10
            score += ma_score * self.weights['ma'] / 0.10
            
            return min(100, max(0, score))
            
        except Exception as e:
            print(f"计算评分时出错: {e}")
            return 0
    
    def get_signal_reasons(self, stock_data):
        """获取信号原因"""
        reasons = []
        
        if stock_data.empty or len(stock_data) < 30:
            return reasons
        
        try:
            high = stock_data['high']
            low = stock_data['low']
            close = stock_data['close']
            volume = stock_data['volume']
            
            # 计算技术指标
            dif, dea, macd = TechnicalIndicators.calculate_macd(close)
            rsi = TechnicalIndicators.calculate_rsi(close)
            k, d, j = TechnicalIndicators.calculate_kdj(high, low, close)
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(close)
            
            # 检查各种信号
            if StockSignals.macd_golden_cross(dif, dea):
                reasons.append("MACD金叉")
            
            if StockSignals.rsi_oversold_rebound(rsi):
                reasons.append("RSI超卖反弹")
            
            if StockSignals.kdj_golden_cross(k, d):
                reasons.append("KDJ金叉")
            
            if StockSignals.bollinger_near_lower(close, lower):
                reasons.append("布林带下轨反弹")
            
            if TechnicalIndicators.check_volume_amplification(volume):
                reasons.append("成交量放大")
            
            if TechnicalIndicators.check_ma_bullish_arrangement(close):
                reasons.append("均线多头排列")
                
        except Exception as e:
            print(f"获取信号原因时出错: {e}")
        
        return reasons