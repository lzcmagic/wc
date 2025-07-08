import pandas as pd
import time
from datetime import datetime

from core.base_selector import BaseSelector
from data_fetcher import StockDataFetcher
from core.indicators import StockScorer
from core.config import get_strategy_config

class TechnicalStrategySelector(BaseSelector):
    """
    技术分析选股策略
    - 基于各种技术指标（如均线、MACD、RSI等）对股票进行评分和筛选。
    - 适合于寻找短期技术形态较好的股票。
    """
    def __init__(self, strategy_name='technical'):
        super().__init__(strategy_name)
        self.fetcher = StockDataFetcher()
        self.scorer = StockScorer()
        # 加载技术分析策略的特定配置
        self.config = get_strategy_config(strategy_name)

    def _apply_strategy(self, data):
        """
        应用技术策略对单只股票进行评分。
        此方法在 BaseSelector 中被并发调用。
        """
        score, reasons = self.scorer.calculate_score(data, self.config)
        return score, reasons

    def run_selection(self, all_stocks=None, for_date=None):
        """
        执行技术分析选股策略的主函数。
        复用 BaseSelector 的骨架，只关注策略实现本身。
        """
        # run_selection 的核心逻辑已上移至 BaseSelector
        # 这里只需调用父类的方法即可
        return super().run_selection(all_stocks=all_stocks, for_date=for_date) 