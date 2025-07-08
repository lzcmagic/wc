import pandas as pd
import numpy as np
import time
from datetime import datetime
import json

from core.base_selector import BaseSelector
from data_fetcher import StockDataFetcher
from core.indicators import StockScorer
from core.config import get_strategy_config
from strategies.technical_strategy import TechnicalStrategySelector

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
        self.weights = self.config.get('weights', {}) # 安全地获取权重

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
        """
        执行完整的四维选股策略
        """
        print(f"\n{'='*20} 开始执行四维综合分析策略 {'='*20}\n")
        start_time = time.time()

        # 1. 数据获取: 如果没有传入数据，则实时获取
        # 修复: 调用正确的数据获取方法
        stock_list_df = all_stocks if all_stocks is not None else self.fetcher.get_all_stocks_with_market_cap()
        if stock_list_df.empty:
            print("❌ 未能获取到股票列表，策略终止。")
            return pd.DataFrame()

        print(f"   - 获取到 {len(stock_list_df)} 只初始股票。")
        
        # 2. 基础筛选
        # (这里的筛选逻辑可以根据综合策略的需求定制，暂时从简)
        filtered_stocks = stock_list_df[~stock_list_df['name'].str.contains('ST|退|N')].copy()
        filtered_stocks = filtered_stocks[filtered_stocks['market_cap'] >= self.config['min_market_cap']]
        
        print(f"   - 基础筛选完成，剩余 {len(filtered_stocks)} 只股票，耗时: {time.time() - start_time:.2f} 秒")

        # 3. 四维分析
        technical_scores = self.analyze_technical(filtered_stocks, for_date)
        fundamental_scores = self.analyze_fundamental(filtered_stocks)
        market_scores = self.analyze_market_sentiment(filtered_stocks)
        industry_scores = self.analyze_industry_rotation(filtered_stocks)

        # 5. 结果综合与输出
        final_scores = self.calculate_final_score(
            technical_scores, fundamental_scores, market_scores, industry_scores
        )
        top_stocks = self.get_top_stocks(final_scores)

        # 6. 保存和打印结果
        self.save_results(top_stocks, for_date=for_date)

        if not for_date:
            self.print_results(top_stocks)

        end_time = time.time()
        print(f"\n{'='*20} 四维综合分析策略执行完毕 {'='*20}")
        print(f"   - 耗时: {end_time - start_time:.2f} 秒")
        print(f"{'='*58}\n")

        return top_stocks 

    def calculate_final_score(self, tech_scores, fund_scores, market_scores, industry_scores):
        """
        根据各维度得分和权重，计算最终总分
        """
        print("\n   - 正在计算最终得分...")
        final_scores = {}
        all_stocks = set(tech_scores.keys()) | set(fund_scores.keys())

        # 使用从 __init__ 加载的权重
        weights = self.weights
        if not weights:
            print("❌ 警告: 策略权重未配置，无法计算总分。")
            return {}
        
        for stock in all_stocks:
            tech_score = tech_scores.get(stock, 0)
            fund_score = fund_scores.get(stock, 0)
            market_score = market_scores.get(stock, 0) # 占位
            industry_score = industry_scores.get(stock, 0) # 占位

            total_score = (
                tech_score * weights.get('technical', 0) +
                fund_score * weights.get('fundamental', 0) +
                market_score * weights.get('market', 0) +
                industry_score * weights.get('industry', 0)
            )
            final_scores[stock] = total_score
        
        print(f"   - 完成最终分数计算。")
        return final_scores

    def get_top_stocks(self, final_scores):
        """
        从最终得分中筛选出排名靠前的股票
        """
        if not final_scores:
            return []
            
        # 按得分从高到低排序
        sorted_stocks = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
        
        # 获取配置中要选择的股票数量
        num_to_select = self.config.get('selection_count', 20)
        
        # 修复: 从原始的 stock_list_df 中获取名称，正确的列名是 'name'
        stock_list_df = self.fetcher.get_all_stocks_with_market_cap()
        code_to_name = pd.Series(stock_list_df['name'].values, index=stock_list_df['code']).to_dict()

        # 格式化为字典列表
        top_stocks_with_scores = sorted_stocks[:num_to_select]
        top_stocks = [
            {'code': code, 'name': code_to_name.get(code, ''), 'score': score}
            for code, score in top_stocks_with_scores
        ]
        
        return top_stocks

    def analyze_technical(self, stock_list, for_date=None):
        """
        进行技术分析
        复用 TechnicalStrategySelector 的逻辑来进行打分
        """
        print("\n   - 正在进行技术形态分析...")
        
        # 为了进行技术分析，我们需要一个技术策略的实例
        tech_selector = TechnicalStrategySelector('technical')
        
        # 调用其内部的评分方法
        scored_stocks_list = tech_selector._calculate_stock_scores(stock_list.to_dict('records'))
        
        # 将结果转换为 {code: score} 的字典格式
        scores = {stock['code']: stock.get('score', 0) for stock in scored_stocks_list}
        
        return scores

    def analyze_fundamental(self, stock_list):
        """
        分析股票的基本面数据并打分 (PE, PB, ROE)
        """
        s_time = time.time()
        print("\n   - 正在进行基本面分析...")
        scores = {}
        for index, stock in stock_list.iterrows():
            scores[stock['code']] = 50 # 占位分数
        print(f"   - 完成基本面分析，耗时: {time.time() - s_time:.2f} 秒")
        return scores

    def analyze_market_sentiment(self, stock_list):
        """
        分析市场情绪（占位符）
        """
        print("\n   - 正在进行市场情绪分析(占位)...")
        scores = {}
        for index, stock in stock_list.iterrows():
            scores[stock['code']] = 50
        return scores

    def analyze_industry_rotation(self, stock_list):
        """
        分析行业轮动（占位符）
        """
        print("\n   - 正在进行行业轮动分析(占位)...")
        scores = {}
        for index, stock in stock_list.iterrows():
            scores[stock['code']] = 50
        return scores

if __name__ == '__main__':
    # 测试代码
    # 需要确保在项目根目录下运行，并且有可用的 config
    from core.config import Config
    cfg = Config()
    
    # 仅 برای 测试，我们可能需要模拟一些数据
    selector = ComprehensiveStrategySelector(cfg)
    results = selector.run_selection()
    
    if results:
        print("\n综合策略选股结果:")
        for stock in results:
            print(f"  - 股票代码: {stock['code']}, 综合得分: {stock['score']:.2f}") 