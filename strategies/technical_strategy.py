from core.base_selector import BaseSelector
from core.config import config
from core.indicators import StockScorer

class TechnicalStrategy(BaseSelector):
    """
    纯技术分析选股策略。
    - 继承 BaseSelector。
    - 实现候选股的初筛逻辑。
    - 实现基于传统技术指标的评分逻辑。
    """
    def __init__(self):
        # 将策略名称和对应的配置传入基类
        strategy_config = config.TECHNICAL_STRATEGY_CONFIG
        super().__init__("Technical", strategy_config)
        
        # 初始化该策略专用的评分器
        self.scorer = StockScorer(weights=strategy_config.get('scorer_weights', {}))

    def _get_candidate_stocks(self):
        """
        根据市值、近期涨幅等基础条件进行初步筛选。
        这部分逻辑来自原 stock_selector.py。
        """
        print("🔎 正在执行[技术分析策略]的候选股初筛...")
        
        try:
            # 优化：一次性获取所有A股的列表
            all_stocks = self.fetcher.get_stock_list()
            if all_stocks.empty:
                print("❌ 无法获取A股列表，初筛失败。")
                return []
            
            print(f"✅ 获取到 {len(all_stocks)} 只A股。")
            
            # 从配置中获取筛选参数
            filter_cfg = self.config.get('filter', {})
            min_market_cap = filter_cfg.get('min_market_cap', 0)
            
            # 在DataFrame上进行高效筛选
            # 1. 筛选市值
            candidates = all_stocks[all_stocks['market_cap'] >= min_market_cap].copy()
            
            # 2. 过滤ST和退市股
            candidates = candidates[~candidates['name'].str.contains('ST|退')]
            
            print(f"初筛后剩余 {len(candidates)} 只股票，将进一步分析近期涨幅...")
            return candidates.to_dict('records') # 返回字典列表
            
        except Exception as e:
            print(f"❌ 在候选股初筛过程中发生错误: {e}")
            return []

    def _score_stocks(self, candidate_stocks):
        """
        为通过初筛的股票计算技术指标得分。
        """
        print("📊 正在为候选股计算技术指标得分...")
        scored_stocks = []
        
        filter_cfg = self.config.get('filter', {})
        max_recent_gain = filter_cfg.get('max_recent_gain', 100)
        min_score = filter_cfg.get('min_score', 0)
        analysis_period = filter_cfg.get('analysis_period', 60)

        for idx, stock in enumerate(candidate_stocks):
            print(f"  -> 正在分析 {stock['name']} ({stock['code']}) [{idx+1}/{len(candidate_stocks)}]")
            
            try:
                # 获取历史数据用于计算涨幅和技术指标
                hist_data = self.fetcher.get_stock_data(stock['code'], period=analysis_period + 30)
                if hist_data.empty or len(hist_data) < analysis_period:
                    print(f"     - 数据不足，跳过。")
                    continue

                # 检查近期涨幅是否超出限制
                recent_gain = (hist_data['close'].iloc[-1] / hist_data['close'].iloc[-30] - 1) * 100
                if recent_gain > max_recent_gain:
                    print(f"     - 近30日涨幅 {recent_gain:.1f}% 过高，跳过。")
                    continue

                # 计算技术得分
                score = self.scorer.calculate_score(hist_data)
                
                if score >= min_score:
                    stock_info = {
                        'code': stock['code'],
                        'name': stock['name'],
                        'score': round(score, 1),
                        'reasons': self.scorer.get_signal_reasons(),
                        'current_price': hist_data['close'].iloc[-1],
                        'market_cap': stock['market_cap'],
                        'recent_gain': round(recent_gain, 2)
                    }
                    scored_stocks.append(stock_info)
                    print(f"     - ✔️ 得分: {score:.1f}，符合要求。理由: {', '.join(stock_info['reasons'])}")
                else:
                    print(f"     - ✖️ 得分: {score:.1f}，不符合要求。")
                
                self._rate_limit_delay()

            except Exception as e:
                print(f"     - ❌ 分析 {stock['name']} 时出错: {e}")
                continue
        
        return scored_stocks 