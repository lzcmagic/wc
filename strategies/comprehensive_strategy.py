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
            # 数据缺失时给予中性评分，避免过度惩罚
            return 50, ["基本面数据缺失，给予中性评分"]

        pe = f_data.get('pe_ttm', np.inf)
        roe = f_data.get('roe', -np.inf)
        pb = f_data.get('pb', np.inf)

        # 基础分数（数据可获取）
        base_score = 30
        score += base_score
        reasons.append("基本面数据可获取")

        # 1. PE估值评分 (最高20分)
        if 0 < pe <= filters['max_pe_ttm']:
            score += 20
            reasons.append(f"PE({pe:.1f})合理")
        elif pe > filters['max_pe_ttm']:
            score += 5  # 估值偏高但不为0
            reasons.append(f"PE({pe:.1f})偏高")
        else:
            score += 10  # 无效PE数据给予中性分
            reasons.append("PE数据无效")

        # 2. ROE盈利能力评分 (最高30分)
        if roe >= filters['min_roe']:
            if roe >= 15:
                score += 30  # 优秀ROE
                reasons.append(f"ROE({roe:.1f}%)优秀")
            else:
                score += 20  # 良好ROE
                reasons.append(f"ROE({roe:.1f}%)良好")
        elif roe >= 0:
            score += 10  # 正ROE但较低
            reasons.append(f"ROE({roe:.1f}%)偏低")
        else:
            score += 5   # 负ROE但不为0
            reasons.append(f"ROE({roe:.1f}%)较差")

        # 3. PB估值评分 (最高20分)
        if 0 < pb <= filters['max_pb']:
            if pb <= 2:
                score += 20  # 优秀PB
                reasons.append(f"PB({pb:.1f})优秀")
            else:
                score += 15  # 合理PB
                reasons.append(f"PB({pb:.1f})合理")
        elif pb > filters['max_pb']:
            score += 5   # 高PB但不为0
            reasons.append(f"PB({pb:.1f})偏高")
        else:
            score += 10  # 无效PB数据
            reasons.append("PB数据无效")
        
        # 确保评分在0-100范围内
        return min(100, max(0, score)), reasons

    def _calculate_sentiment_score(self, stock_code: str) -> (float, list):
        """(占位) 计算市场情绪评分"""
        # 此处未来可以接入舆情分析、投资者情绪指数等
        return 70, ["情绪稳定(占位)"]

    def _calculate_industry_score(self, stock_code: str) -> (float, list):
        """(占位) 计算行业评分"""
        # 此处未来可以接入行业轮动、赛道前景等分析
        return 75, ["行业中性(占位)"]

    def _apply_strategy(self, data):
        """
        应用综合策略对单只股票进行评分。
        此方法在 BaseSelector 中被并发调用。
        """
        stock_code = data.iloc[-1]['code_in_df'] # 从数据中获取股票代码

        # 1. 计算各维度分数
        tech_score, tech_reasons = self.scorer.calculate_score(data, self.config)
        funda_score, funda_reasons = self._calculate_fundamental_score(stock_code)
        senti_score, senti_reasons = self._calculate_sentiment_score(stock_code)
        ind_score, ind_reasons = self._calculate_industry_score(stock_code)

        # 2. 根据权重计算总分
        weights = self.weights
        total_score = (tech_score * weights.get('technical', 0) +
                       funda_score * weights.get('fundamental', 0) +
                       senti_score * weights.get('sentiment', 0) +
                       ind_score * weights.get('industry', 0))

        # 3. 组合推荐理由
        reasons = tech_reasons + funda_reasons

        # 4. 判断是否满足最低分
        if total_score >= self.config.get('min_score', 0):
            return total_score, reasons
        else:
            return 0, []

    def run_selection(self, all_stocks=None, for_date=None):
        """
        执行完整的四维综合选股策略
        复用 BaseSelector 的骨架，只关注策略实现本身。
        """
        # 在评分前，为每行数据添加股票代码，以便在_apply_strategy中可以获取
        if all_stocks is not None:
            all_stocks['code_in_df'] = all_stocks['code']
            
        return super().run_selection(all_stocks=all_stocks, for_date=for_date)

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
        code_to_market_cap = pd.Series(stock_list_df['market_cap'].values, index=stock_list_df['code']).to_dict()

        # 格式化为字典列表，包含 print_results 需要的所有字段
        top_stocks_with_scores = sorted_stocks[:num_to_select]
        top_stocks = []
        
        for code, score in top_stocks_with_scores:
            stock_data = {
                'code': code, 
                'name': code_to_name.get(code, ''), 
                'score': score,
                'reasons': ['综合评分优秀'],  # 添加推荐理由
                'price': 0.0,  # 占位价格
                'market_cap': code_to_market_cap.get(code, 0) / 100000000  # 转换为亿元
            }
            top_stocks.append(stock_data)
        
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