"""
短线交易专用选股策略
针对1-10天持股周期的短线操作优化
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.base_selector import BaseSelector
from data_fetcher import StockDataFetcher
from core.indicators import TechnicalIndicators
from core.config import get_strategy_config

class ShortTermTradingStrategy(BaseSelector):
    """
    短线交易专用策略
    - 持股周期：1-10天
    - 重点关注：成交量、热点题材、资金流向
    - 快进快出，抓住短期波动机会
    """
    
    def __init__(self, strategy_name='short_term'):
        super().__init__(strategy_name)
        self.fetcher = StockDataFetcher()
        
        # 短线专用配置
        self.config = {
            'period': 20,                    # 只看20天数据，够用
            'min_market_cap': 2000000000,    # 20亿即可，中小盘更活跃
            'max_market_cap': 80000000000,   # 800亿以下，避免大象股
            'max_recent_gain': 50,           # 允许50%涨幅，抓妖股机会
            'min_score': 60,                 # 降低门槛，增加机会
            'max_stocks': 15,                # 多一些选择
            'min_turnover_rate': 3,          # 换手率>3%，活跃度要求
            'max_pe': 100,                   # PE放宽，成长股估值高正常
        }
        
        # 短线专用权重 - 重成交量轻基本面
        self.weights = {
            'volume_momentum': 0.25,     # 成交量动量 - 最重要
            'price_momentum': 0.20,      # 价格动量 - 短期趋势
            'technical_breakthrough': 0.20, # 技术突破信号
            'market_sentiment': 0.15,    # 市场情绪/热点
            'liquidity': 0.10,          # 流动性指标
            'volatility': 0.10,         # 波动率 - 短线需要波动
        }
    
    def _apply_strategy(self, data):
        """短线专用评分算法"""
        if data.empty or len(data) < 10:
            return 0, []
        
        total_score = 0
        reasons = []
        
        # 1. 成交量动量分析 (25%) - 短线最重要
        volume_score, volume_reasons = self._analyze_volume_momentum(data)
        total_score += volume_score * self.weights['volume_momentum']
        reasons.extend(volume_reasons)
        
        # 2. 价格动量分析 (20%) - 短期趋势
        price_score, price_reasons = self._analyze_price_momentum(data)
        total_score += price_score * self.weights['price_momentum']
        reasons.extend(price_reasons)
        
        # 3. 技术突破信号 (20%) - 关键位突破
        breakthrough_score, bt_reasons = self._analyze_technical_breakthrough(data)
        total_score += breakthrough_score * self.weights['technical_breakthrough']
        reasons.extend(bt_reasons)
        
        # 4. 市场情绪指标 (15%) - 热点判断
        sentiment_score, sentiment_reasons = self._analyze_market_sentiment(data)
        total_score += sentiment_score * self.weights['market_sentiment']
        reasons.extend(sentiment_reasons)
        
        # 5. 流动性分析 (10%) - 确保能买能卖
        liquidity_score, liquidity_reasons = self._analyze_liquidity(data)
        total_score += liquidity_score * self.weights['liquidity']
        reasons.extend(liquidity_reasons)
        
        # 6. 波动率分析 (10%) - 短线需要波动
        volatility_score, vol_reasons = self._analyze_volatility(data)
        total_score += volatility_score * self.weights['volatility']
        reasons.extend(vol_reasons)
        
        return total_score, reasons[:5]  # 只保留前5个理由
    
    def _analyze_volume_momentum(self, data):
        """分析成交量动量 - 短线核心指标"""
        score = 0
        reasons = []
        
        volume = data['volume']
        close = data['close']
        
        # 1. 近3日放量 (30分)
        if len(volume) >= 5:
            recent_avg = volume.iloc[-3:].mean()
            historical_avg = volume.iloc[-10:-3].mean()
            
            if recent_avg > historical_avg * 2.0:
                score += 30
                reasons.append("近3日大幅放量")
            elif recent_avg > historical_avg * 1.5:
                score += 20
                reasons.append("近3日适度放量")
        
        # 2. 量价配合 (25分)
        if len(close) >= 3:
            price_change = (close.iloc[-1] - close.iloc[-3]) / close.iloc[-3]
            volume_change = (volume.iloc[-1] - volume.iloc[-3]) / volume.iloc[-3]
            
            if price_change > 0 and volume_change > 0:
                score += 25
                reasons.append("量价齐升")
            elif price_change > 0.05 and volume_change > 0.3:
                score += 35  # 加分项
                reasons.append("强势量价配合")
        
        # 3. 连续放量 (20分)
        if len(volume) >= 5:
            consecutive_growth = 0
            for i in range(1, min(5, len(volume))):
                if volume.iloc[-i] > volume.iloc[-i-1]:
                    consecutive_growth += 1
                else:
                    break
            
            if consecutive_growth >= 3:
                score += 20
                reasons.append(f"连续{consecutive_growth}日放量")
        
        # 4. 换手率检查 (25分)
        # 注意：这里需要市值数据计算换手率，暂时用成交额/流通市值简化
        if len(volume) >= 1:
            # 简化版：以成交量判断活跃度
            avg_volume = volume.mean()
            if volume.iloc[-1] > avg_volume * 2:
                score += 25
                reasons.append("当日成交活跃")
        
        return min(100, score), reasons
    
    def _analyze_price_momentum(self, data):
        """分析价格动量 - 短期趋势"""
        score = 0
        reasons = []
        
        close = data['close']
        high = data['high']
        low = data['low']
        
        # 1. 短期均线突破 (30分)
        if len(close) >= 10:
            ma5 = close.rolling(5).mean()
            ma10 = close.rolling(10).mean()
            
            # 均线多头排列
            if ma5.iloc[-1] > ma10.iloc[-1] and close.iloc[-1] > ma5.iloc[-1]:
                score += 30
                reasons.append("短期均线多头排列")
            # 金叉
            elif ma5.iloc[-1] > ma10.iloc[-1] and ma5.iloc[-2] <= ma10.iloc[-2]:
                score += 25
                reasons.append("5日线金叉10日线")
        
        # 2. 近期涨幅 (25分)
        if len(close) >= 5:
            gain_3d = (close.iloc[-1] - close.iloc[-4]) / close.iloc[-4]
            gain_5d = (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] if len(close) >= 6 else 0
            
            if gain_3d > 0.15:  # 3日涨超15%
                score += 25
                reasons.append(f"3日涨幅{gain_3d:.1%}")
            elif gain_3d > 0.08:  # 3日涨超8%
                score += 15
                reasons.append(f"3日涨幅{gain_3d:.1%}")
        
        # 3. 关键位突破 (25分)
        if len(high) >= 20:
            recent_high = high.iloc[-20:-1].max()  # 前20日最高点
            current_price = close.iloc[-1]
            
            if current_price > recent_high:
                score += 25
                reasons.append("突破20日新高")
            elif current_price > recent_high * 0.98:
                score += 15
                reasons.append("接近20日高点")
        
        # 4. 涨停板信号 (20分)
        if len(close) >= 2:
            yesterday_close = close.iloc[-2]
            today_close = close.iloc[-1]
            today_high = high.iloc[-1]
            
            # 涨停或接近涨停
            limit_up_price = yesterday_close * 1.1  # 10%涨停
            if today_high >= limit_up_price * 0.99:
                score += 20
                reasons.append("触及涨停板")
        
        return min(100, score), reasons
    
    def _analyze_technical_breakthrough(self, data):
        """分析技术突破信号"""
        score = 0
        reasons = []
        
        close = data['close']
        volume = data['volume']
        
        # 1. MACD金叉 (使用更敏感参数)
        macd = TechnicalIndicators.calculate_macd(close, fast=6, slow=12, signal=4)
        if not macd.empty and len(macd) >= 2:
            if macd.iloc[-1] > 0 and macd.iloc[-2] <= 0:
                score += 30
                reasons.append("MACD快速金叉")
        
        # 2. KDJ金叉
        if len(data) >= 9:
            kdj = TechnicalIndicators.calculate_kdj(data['high'], data['low'], close)
            if not kdj.empty and len(kdj) >= 2:
                k_line, d_line = kdj.iloc[:, 0], kdj.iloc[:, 1]
                if (k_line.iloc[-1] > d_line.iloc[-1] and 
                    k_line.iloc[-2] <= d_line.iloc[-2] and 
                    k_line.iloc[-1] < 80):  # 非超买区金叉
                    score += 25
                    reasons.append("KDJ金叉")
        
        # 3. 布林带突破
        bollinger = TechnicalIndicators.calculate_bollinger_bands(close, period=10, std_dev=1.5)
        if not bollinger.empty:
            upper_band = bollinger.iloc[:, 2]
            if close.iloc[-1] > upper_band.iloc[-1]:
                score += 20
                reasons.append("突破布林上轨")
        
        # 4. 成交量确认
        if len(volume) >= 3:
            avg_volume = volume.iloc[-5:-1].mean() if len(volume) >= 5 else volume.iloc[:-1].mean()
            if volume.iloc[-1] > avg_volume * 1.5:
                score += 25
                reasons.append("放量确认突破")
        
        return min(100, score), reasons
    
    def _analyze_market_sentiment(self, data):
        """分析市场情绪 - 简化版本"""
        score = 50  # 基础分，未来可接入情绪数据
        reasons = ["市场情绪中性"]
        
        # 简化版：基于成交量和价格变化判断情绪
        close = data['close']
        volume = data['volume']
        
        if len(close) >= 5:
            # 连续上涨判断市场情绪好
            consecutive_up = 0
            for i in range(1, min(4, len(close))):
                if close.iloc[-i] > close.iloc[-i-1]:
                    consecutive_up += 1
                else:
                    break
            
            if consecutive_up >= 3:
                score += 30
                reasons = ["连续上涨，情绪乐观"]
            elif consecutive_up >= 2:
                score += 15
                reasons = ["短期上涨，情绪良好"]
        
        return min(100, score), reasons
    
    def _analyze_liquidity(self, data):
        """分析流动性"""
        score = 0
        reasons = []
        
        volume = data['volume']
        
        # 平均成交量检查
        avg_volume = volume.mean()
        if avg_volume > 0:
            score += 50  # 基础分
            reasons.append("流动性充足")
            
            # 最近成交量是否稳定
            recent_volume = volume.iloc[-5:].mean() if len(volume) >= 5 else volume.iloc[-1]
            if recent_volume > avg_volume * 0.8:
                score += 30
                reasons = ["流动性活跃"]
        
        return min(100, score), reasons
    
    def _analyze_volatility(self, data):
        """分析波动率 - 短线需要一定波动"""
        score = 0
        reasons = []
        
        close = data['close']
        
        if len(close) >= 10:
            # 计算10日波动率
            returns = close.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # 年化波动率
            
            if 0.3 <= volatility <= 0.8:  # 合适的波动率区间
                score += 80
                reasons.append("波动率适中")
            elif volatility > 0.8:
                score += 60
                reasons.append("高波动率")
            elif volatility > 0.15:
                score += 40
                reasons.append("低波动率")
        
        return min(100, score), reasons
    
    def get_strategy_config(self):
        """返回短线策略配置"""
        return {
            'strategy_name': 'short_term',
            'display_name': '短线交易策略',
            'period': self.config['period'],
            'min_market_cap': self.config['min_market_cap'],
            'max_market_cap': self.config['max_market_cap'],
            'max_recent_gain': self.config['max_recent_gain'],
            'min_score': self.config['min_score'],
            'max_stocks': self.config['max_stocks'],
            'weights': self.weights
        } 