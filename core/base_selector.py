import os
import json
from datetime import datetime
import time
import pandas as pd
from tqdm import tqdm
import numpy as np

from data_fetcher import StockDataFetcher
from core.config import config
from core.indicators import calculate_indicators

class BaseSelector:
    """
    选股器基类.
    - 定义了选股流程的统一骨架 (run_selection).
    - 封装了通用的市值过滤、结果保存/打印功能.
    - 子类需要实现具体的评分逻辑 _apply_strategy.
    """
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        # 根据策略名称动态获取配置
        config_attr_name = f"{strategy_name.upper()}_STRATEGY_CONFIG"
        self.config = getattr(config, config_attr_name, {})
        if not self.config:
            raise ValueError(f"未在 config.py 中找到名为 {config_attr_name} 的配置")

        self.fetcher = StockDataFetcher()
        self.results_dir = 'results'
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def run_selection(self, all_stocks=None, for_date=None):
        """
        运行选股过程。
        :param all_stocks: 预先获取的全量股票池 (DataFrame)
        :param for_date: 如果提供，则为该历史日期运行选择，否则为今天。
        """
        run_date = for_date or datetime.now()
        print(f"🚀 开始为日期 {run_date.strftime('%Y-%m-%d')} 运行 {self.strategy_name} 策略...")

        # 如果没有预先提供股票池（例如，非回测模式），则实时获取
        if all_stocks is None:
            all_stocks = self.fetcher.get_all_stocks_with_market_cap()

        # 1. 初步筛选
        candidate_stocks = self._filter_by_market_cap(all_stocks)
        if candidate_stocks.empty:
            print("❌ 在初筛阶段未能找到任何候选股票。")
            return []

        # 2. 评分
        scored_stocks = self._score_stocks(candidate_stocks, for_date=for_date)
        if not scored_stocks:
            print("❌ 在评分阶段未能找到任何股票。")
            return []

        # 3. 排序和选择
        final_selection = self._filter_and_sort(scored_stocks)

        print(f"✅ 成功选出 {len(final_selection)} 只股票。")
        self.save_results(final_selection, for_date)
        self.print_results(final_selection, for_date)
        return final_selection

    def _filter_by_market_cap(self, df):
        """根据配置中的市值要求过滤股票"""
        max_cap = self.config.get('max_market_cap')
        if max_cap and 'market_cap' in df.columns:
            return df[df['market_cap'] <= max_cap].copy()
        return df

    def _score_stocks(self, candidate_stocks, for_date=None):
        """为候选股票评分"""
        period = self.config.get('period', 120)
        results = []
        total = len(candidate_stocks)

        print(f"\n给 {total} 只候选股票进行评分...")
        with tqdm(total=total, desc=f"{self.strategy_name} 评分进度") as pbar:
            for index, row in candidate_stocks.iterrows():
                stock_code = row['code']
                stock_name = row['name']
                
                stock_data = self.fetcher.get_stock_data(stock_code, period=period, end_date=for_date)

                if stock_data is None or stock_data.empty or len(stock_data) < period / 2:
                    pbar.update(1)
                    continue

                stock_data_with_indicators = calculate_indicators(stock_data, self.config['indicators'])
                
                score, reasons = self._apply_strategy(stock_data_with_indicators)

                if score > 0:
                    results.append({
                        'code': stock_code,
                        'name': stock_name,
                        'score': score,
                        'reasons': reasons,
                        'price': stock_data.iloc[-1]['close'],
                        'market_cap': row.get('market_cap', 0)
                    })
                pbar.update(1)
        return results

    def _apply_strategy(self, data):
        """
        应用策略逻辑进行评分。这是一个抽象方法，子类必须实现。
        :param data: 包含指标的DataFrame
        :return: (score, reasons) 元组
        """
        raise NotImplementedError("子类必须实现 `_apply_strategy` 方法")

    def _filter_and_sort(self, scored_stocks):
        """根据得分排序并选取前N名"""
        sorted_stocks = sorted(scored_stocks, key=lambda x: x['score'], reverse=True)
        top_n = self.config.get('top_n', 10)
        return sorted_stocks[:top_n]

    def save_results(self, results, for_date=None):
        """将选股结果保存到JSON文件"""
        date_str = (for_date or datetime.now()).strftime('%Y-%m-%d')
        filename = os.path.join(self.results_dir, f'{self.strategy_name}_selection_{date_str}.json')
        
        # 为JSON序列化清理数据
        for stock in results:
            for key, value in stock.items():
                # 处理numpy数字类型
                if isinstance(value, (np.integer, np.int64)):
                    stock[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    # 检查是否为 NaN
                    if np.isnan(value):
                        stock[key] = None  # 将NaN替换为None
                    else:
                        stock[key] = float(value)
                # 检查其他可能的NaN值（例如在reasons列表中）
                elif isinstance(value, list):
                    stock[key] = [None if isinstance(v, float) and np.isnan(v) else v for v in value]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"\n选股结果已保存至: {filename}")

    def print_results(self, results, for_date=None):
        """在控制台打印选股结果"""
        date_str = (for_date or datetime.now()).strftime('%Y-%m-%d')
        if not results:
            print(f"\n在 {date_str} 未选出任何股票。")
            return
        
        print(f"\n📊 [{self.strategy_name}] 策略选股结果 - {date_str}")
        print("="*80)
        print(f"{'代码':<10}{'名称':<10}{'得分':<8}{'价格':<10}{'市值(亿)':<12}{'推荐理由'}")
        print("-"*80)
        for stock in results:
            market_cap_in_bil = stock.get('market_cap', 0) / 1e8
            print(f"{stock['code']:<10}{stock['name']:<10}{stock['score']:<8}"
                  f"{stock.get('price', 0):<10.2f}{market_cap_in_bil:<12.2f}{' | '.join(stock['reasons'])}")
        print("="*80)
        print("⚠️  风险提示: 本结果仅为量化分析，不构成投资建议。")

    def _rate_limit_delay(self):
        """简单的请求延迟，避免过于频繁地请求API"""
        time.sleep(self.fetcher.config.get('request_delay', 0.1)) 