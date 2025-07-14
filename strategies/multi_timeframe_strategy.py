import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.base_selector import BaseSelector
from data_fetcher import StockDataFetcher
from core.indicators import EnhancedStockScorer
from core.config import get_strategy_config

class MultiTimeframeStrategy(BaseSelector):
    """
    多时间周期分析策略
    - 结合日线、周线、月线多个时间周期进行分析
    - 只在多个时间周期信号一致时给出推荐
    - 大幅提高选股准确率
    """
    
    def __init__(self, strategy_name='multi_timeframe'):
        super().__init__(strategy_name)
        self.fetcher = StockDataFetcher()
        self.scorer = EnhancedStockScorer()
        
        # 多时间周期配置
        self.timeframes = {
            'daily': {'period': 60, 'weight': 0.5},
            'weekly': {'period': 260, 'weight': 0.3},
            'monthly': {'period': 1200, 'weight': 0.2}
        }
        
        # 一致性要求
        self.min_consensus_score = 0.7  # 至少70%时间周期一致
    
    def _apply_strategy(self, data):
        """多时间周期综合分析"""
        stock_code = data.iloc[-1].get('code_in_df', '')
        
        # 获取不同时间周期数据
        timeframe_scores = {}
        timeframe_trends = {}
        
        for tf_name, tf_config in self.timeframes.items():
            period = tf_config['period']
            
            # 获取对应周期的数据
            tf_data = self._get_timeframe_data(stock_code, period, tf_name)
            
            if tf_data is not None and not tf_data.empty:
                # 计算该时间周期的评分
                score, reasons = self.scorer.calculate_enhanced_score(tf_data)
                timeframe_scores[tf_name] = {
                    'score': score,
                    'weight': tf_config['weight'],
                    'reasons': reasons
                }
                
                # 判断趋势方向
                trend = self._determine_trend_direction(tf_data)
                timeframe_trends[tf_name] = trend
        
        # 检查时间周期一致性
        consensus = self._calculate_consensus(timeframe_trends)
        
        if consensus < self.min_consensus_score:
            return 0, ["多时间周期信号不一致"]
        
        # 计算加权综合得分
        weighted_score = self._calculate_weighted_score(timeframe_scores)
        
        # 生成推荐理由
        reasons = self._generate_multi_tf_reasons(timeframe_scores, consensus)
        
        return weighted_score, reasons
    
    def _get_timeframe_data(self, stock_code, period, timeframe):
        """获取指定时间周期的数据"""
        try:
            # 根据时间周期调整数据获取方式
            if timeframe == 'weekly':
                # 获取更多数据然后重采样为周线
                daily_data = self.fetcher.get_stock_data(stock_code, period * 5)
                if daily_data is not None and not daily_data.empty:
                    # 转换为周线数据
                    weekly_data = self._resample_to_weekly(daily_data)
                    return weekly_data.tail(period // 5)
            elif timeframe == 'monthly':
                # 获取更多数据然后重采样为月线
                daily_data = self.fetcher.get_stock_data(stock_code, period * 2)
                if daily_data is not None and not daily_data.empty:
                    # 转换为月线数据
                    monthly_data = self._resample_to_monthly(daily_data)
                    return monthly_data.tail(period // 20)
            else:
                # 日线数据
                return self.fetcher.get_stock_data(stock_code, period)
        except Exception as e:
            print(f"获取{timeframe}数据失败: {e}")
            return None
    
    def _resample_to_weekly(self, daily_data):
        """将日线数据转换为周线数据"""
        daily_data['date'] = pd.to_datetime(daily_data.index)
        daily_data.set_index('date', inplace=True)
        
        weekly_data = daily_data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return weekly_data
    
    def _calculate_consensus(self, timeframe_trends):
        """计算时间周期一致性"""
        if not timeframe_trends:
            return 0
        
        trend_counts = {}
        total_weight = 0
        
        for tf_name, trend in timeframe_trends.items():
            weight = self.timeframes[tf_name]['weight']
            
            if trend not in trend_counts:
                trend_counts[trend] = 0
            trend_counts[trend] += weight
            total_weight += weight
        
        # 找出主导趋势的权重占比
        max_consensus = max(trend_counts.values()) / total_weight if total_weight > 0 else 0
        
        return max_consensus 