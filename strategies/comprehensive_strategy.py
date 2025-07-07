from core.base_selector import BaseSelector
from core.config import config
from core.indicators import (
    TechnicalIndicators,
    FundamentalAnalyzer,
    MarketSentimentAnalyzer,
    IndustryAnalyzer
)

class ComprehensiveStrategy(BaseSelector):
    """
    四维综合分析选股策略 (技术面、基本面、市场情绪、行业)。
    - 继承 BaseSelector。
    - 实现更严格的候选股初筛逻辑。
    - 实现多维度、更复杂的评分逻辑。
    """
    def __init__(self):
        strategy_config = config.COMPREHENSIVE_STRATEGY_CONFIG
        super().__init__("Comprehensive", strategy_config)
        
        # 初始化该策略所需的多个分析器
        self.tech_indicators = TechnicalIndicators()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        self.industry_analyzer = IndustryAnalyzer()

    def _get_candidate_stocks(self):
        """
        根据增强版配置进行更严格的初步筛选。
        """
        print("🔎 正在执行[四维综合策略]的候选股初筛...")
        
        try:
            all_stocks = self.fetcher.get_stock_list()
            if all_stocks.empty:
                return []
            
            print(f"✅ 获取到 {len(all_stocks)} 只A股。")
            
            filter_cfg = self.config.get('filter', {})
            min_market_cap = filter_cfg.get('min_market_cap', 0)
            
            candidates = all_stocks[all_stocks['market_cap'] >= min_market_cap].copy()
            candidates = candidates[~candidates['name'].str.contains('ST|退|N')]
            
            print(f"初筛后剩余 {len(candidates)} 只股票，将进入多维度评分环节...")
            return candidates.to_dict('records')
            
        except Exception as e:
            print(f"❌ 在[四维综合策略]初筛过程中发生错误: {e}")
            return []

    def _score_stocks(self, candidate_stocks):
        """
        为候选股计算四维综合得分。
        """
        print("📊 正在为候选股计算四维综合得分...")
        scored_stocks = []
        
        filter_cfg = self.config.get('filter', {})
        weights = self.config.get('scorer_weights', {})
        min_score_req = filter_cfg.get('min_score', 0)

        for idx, stock in enumerate(candidate_stocks):
            print(f"  -> 正在分析 {stock['name']} ({stock['code']}) [{idx+1}/{len(candidate_stocks)}]")
            
            try:
                hist_data = self.fetcher.get_stock_data(stock['code'], period=filter_cfg.get('analysis_period', 90))
                if hist_data.empty or len(hist_data) < 60:
                    continue

                # --- 1. 技术面评分 ---
                tech_score = self._calculate_technical_score(hist_data, weights)
                
                # --- 2. 基本面评分 ---
                fin_data = self.fundamental_analyzer.get_financial_data(stock['code'])
                # 基本面硬性筛选
                if fin_data.get('pe_ratio', 999) > filter_cfg.get('max_pe', 999) or \
                   fin_data.get('roe', -1) < filter_cfg.get('min_roe', -1):
                   print(f"     - ✖️ 基本面不达标 (PE或ROE)，跳过。")
                   continue
                fundamental_score, _ = self.fundamental_analyzer.score_fundamentals(fin_data)

                # --- 3. 市场情绪评分 ---
                sentiment_score = self._calculate_sentiment_score(hist_data)
                
                # --- 4. 行业评分 ---
                industry_score, _ = self.industry_analyzer.get_industry_strength(stock['code'])

                # --- 综合总分 ---
                total_score = (tech_score * weights.get('technical_total', 0.6) +
                               fundamental_score * weights.get('fundamental_total', 0.25) +
                               sentiment_score * weights.get('sentiment_total', 0.10) +
                               industry_score * weights.get('industry_total', 0.05))

                if total_score >= min_score_req:
                    stock_info = {
                        'code': stock['code'],
                        'name': stock['name'],
                        'score': round(total_score, 1),
                        'reasons': [f"技术分:{tech_score:.0f}", f"基本面分:{fundamental_score:.0f}", f"情绪分:{sentiment_score:.0f}", f"行业分:{industry_score:.0f}"],
                        'current_price': hist_data['close'].iloc[-1],
                        'market_cap': stock['market_cap'],
                    }
                    scored_stocks.append(stock_info)
                    print(f"     - ✔️ 综合得分: {total_score:.1f}，符合要求。")
                else:
                    print(f"     - ✖️ 综合得分: {total_score:.1f}，不符合要求。")
                
                self._rate_limit_delay()

            except Exception as e:
                print(f"     - ❌ 分析 {stock['name']} 时出错: {e}")
                continue
        
        return scored_stocks

    def _calculate_technical_score(self, data, weights):
        # 这是一个简化的例子，实际可以更复杂
        score = 0
        # ... 此处省略调用 self.tech_indicators 计算各项技术指标并加权求和的详细代码 ...
        # 假设我们简单地给予一个基于RSI和OBV的分数
        rsi = self.tech_indicators.calculate_rsi(data['close'])
        obv = self.tech_indicators.calculate_obv(data['close'], data['volume'])
        
        if not rsi.empty and rsi.iloc[-1] < 50:
            score += 40
        if not obv.empty and obv.iloc[-1] > obv.iloc[-10:].mean():
            score += 60
        return score

    def _calculate_sentiment_score(self, data):
        # 同样是简化例子
        price_mom = self.sentiment_analyzer.calculate_price_momentum(data['close'])
        vol_score = self.sentiment_analyzer.calculate_volatility_score(data['close'])
        
        score = 0
        if not price_mom.empty and price_mom.iloc[-1] > 0:
            score += 50
        if not vol_score.empty and vol_score.iloc[-1] > 60: # 波动率较低
            score += 50
        return score 