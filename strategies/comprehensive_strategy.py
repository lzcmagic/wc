import pandas as pd
import numpy as np
import time
from datetime import datetime

from core.base_selector import BaseSelector
from data_fetcher import StockDataFetcher
from core.indicators import StockScorer
from core.config import get_strategy_config

class ComprehensiveStrategySelector(BaseSelector):
    """
    四维综合选股策略
    - 结合技术面、基本面、市场情绪和行业分析，进行综合评分。
    - 旨在更全面地评估股票，平衡收益与风险。
    """
    def __init__(self, strategy_name='comprehensive'):
        super().__init__(strategy_name)
        self.fetcher = StockDataFetcher()
        self.scorer = StockScorer()
        self.config = get_strategy_config(strategy_name)
        self.weights = self.config['weights']

    def _calculate_fundamental_score(self, stock_code: str) -> (float, list):
        """计算单只股票的基本面评分"""
        score = 0
        reasons = []
        filters = self.config['fundamental_filters']
        
        f_data = self.fetcher.get_fundamental_data(stock_code)
        if not f_data:
            return 0, ["数据缺失"]

        pe = f_data.get('pe_ttm', np.inf)
        roe = f_data.get('roe', -np.inf)
        pb = f_data.get('pb', np.inf)

        # 1. PE估值评分
        if 0 < pe <= filters['max_pe_ttm']:
            score += 40
            reasons.append(f"PE({pe:.1f})合理")
        elif pe > filters['max_pe_ttm']:
             reasons.append(f"PE({pe:.1f})过高")


        # 2. ROE盈利能力评分
        if roe >= filters['min_roe']:
            score += 40
            reasons.append(f"ROE({roe:.1f}%)较高")
        else:
            reasons.append(f"ROE({roe:.1f}%)较低")

        # 3. PB估值评分
        if 0 < pb <= filters['max_pb']:
            score += 20
            reasons.append(f"PB({pb:.1f})合理")
        
        return score, reasons

    def _calculate_sentiment_score(self, stock_code: str) -> (float, list):
        """(占位) 计算市场情绪评分"""
        # 此处未来可以接入舆情分析、投资者情绪指数等
        return 70, ["情绪稳定(占位)"]

    def _calculate_industry_score(self, stock_code: str) -> (float, list):
        """(占位) 计算行业评分"""
        # 此处未来可以接入行业轮动、赛道前景等分析
        return 75, ["行业中性(占位)"]

    def _filter_and_score_stocks(self, stock_list, for_date=None):
        """对筛选后的股票进行四维评分"""
        final_results = []
        for idx, stock in enumerate(stock_list):
            print(f"  分析: {stock['name']} ({stock['code']}) [{idx + 1}/{len(stock_list)}]")
            stock_data = self.fetcher.get_stock_data(stock['code'], self.config['analysis_period'], end_date=for_date)
            if stock_data.empty:
                continue

            tech_score, tech_reasons = self.scorer.calculate_score(stock_data), self.scorer.get_signal_reasons(stock_data)
            funda_score, funda_reasons = self._calculate_fundamental_score(stock['code'])
            senti_score, senti_reasons = self._calculate_sentiment_score(stock['code'])
            ind_score, ind_reasons = self._calculate_industry_score(stock['code'])

            total_score = (tech_score * self.weights['technical'] +
                           funda_score * self.weights['fundamental'] +
                           senti_score * self.weights['sentiment'] +
                           ind_score * self.weights['industry'])
            
            if total_score >= self.config['min_score']:
                result = {
                    'code': stock['code'],
                    'name': stock['name'],
                    'score': round(total_score, 1),
                    'reasons': tech_reasons + funda_reasons,
                    'details': {
                        'tech_score': round(tech_score,1),
                        'funda_score': round(funda_score,1),
                        'senti_score': round(senti_score,1),
                        'ind_score': round(ind_score,1),
                    }
                }
                if not stock_data.empty:
                    result['current_price'] = round(stock_data['close'].iloc[-1], 2)

                final_results.append(result)
                print(f"    => 总分: {total_score:.1f} (入选)")
            else:
                print(f"    => 总分: {total_score:.1f} (低于阈值)")
            
            time.sleep(self.config.get('api_call_delay', 0.2))
        return final_results

    def run_selection(self, all_stocks=None, for_date=None):
        """执行四维综合选股策略"""
        if for_date:
            print(f"\n--- [综合策略] 回测日期: {for_date.strftime('%Y-%m-%d')} ---")
        else:
            print(f"\n{'='*20} 开始执行四维综合分析策略 {'='*20}")

        start_time = datetime.now()

        # 1. 获取股票池
        stock_list_df = all_stocks if all_stocks is not None else self.fetcher.get_stock_list()
        if stock_list_df.empty:
            print("错误：无法获取股票列表。")
            return []
        
        # 2. 基础筛选
        # (这里的筛选逻辑可以根据综合策略的需求定制，暂时从简)
        filtered_stocks = stock_list_df[~stock_list_df['name'].str.contains('ST|退|N')].copy()
        filtered_stocks = filtered_stocks[filtered_stocks['market_cap'] >= self.config['min_market_cap']]
        
        # 3. 评分
        final_results = self._filter_and_score_stocks(filtered_stocks.to_dict('records'), for_date=for_date)

        # 4. 排序和输出
        top_stocks = sorted(final_results, key=lambda x: x['score'], reverse=True)[:self.config['max_stocks']]
        
        if not for_date:
            self.save_results(top_stocks, self.config)
            self.print_results(top_stocks)
            end_time = datetime.now()
            print(f"策略执行完毕，总耗时: {end_time - start_time}")

        return top_stocks 