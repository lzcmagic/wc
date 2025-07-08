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

    def _filter_basic_criteria(self, stock_list):
        """
        执行基础的股票筛选，过滤掉不符合基本要求的股票。
        """
        print("--- [技术策略] 正在执行基础筛选 ---")
        filtered_stocks = []
        
        try:
            market_data = self.fetcher.get_stock_list()
            if market_data.empty:
                print("错误：无法获取股票列表进行筛选。")
                return []
            
            # 为避免API调用超限和提高效率，这里只取前100只股票做演示
            sample_stocks = market_data.head(self.config.get('sample_size', 100))
            
            for idx, (_, stock) in enumerate(sample_stocks.iterrows()):
                if (idx + 1) % 10 == 0:
                    print(f"  已处理 {idx + 1}/{len(sample_stocks)} 只股票...")
                
                stock_code = stock['code']
                stock_name = stock['name']
                
                if 'ST' in stock_name or '*ST' in stock_name or '退' in stock_name:
                    continue
                
                market_info = self.fetcher.get_market_cap(stock_code)
                if not market_info or market_info.get('circulation_market_cap', 0) < self.config['min_market_cap']:
                    continue
                
                recent_data = self.fetcher.get_stock_data(stock_code, self.config.get('recent_gain_days', 30))
                if recent_data.empty or len(recent_data) < 20:
                    continue
                
                recent_gain = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[0] - 1) * 100
                if recent_gain > self.config['max_recent_gain']:
                    continue
                
                filtered_stocks.append({
                    'code': stock_code,
                    'name': stock_name,
                    'market_cap': market_info['circulation_market_cap'],
                    'recent_gain': recent_gain
                })
                
                time.sleep(self.config.get('api_call_delay', 0.1)) # 避免API调用过于频繁

                if len(filtered_stocks) >= self.config.get('max_filtered_stocks', 50):
                    print("  已达到基础筛选的股票数量上限。")
                    break
            
            print(f"--- 基础筛选完成，{len(filtered_stocks)} 只股票进入技术分析 ---")
            return filtered_stocks
            
        except Exception as e:
            print(f"基础筛选过程中出现错误: {e}")
            return []

    def _calculate_stock_scores(self, stock_list):
        """
        对通过基础筛选的股票进行技术指标计算和评分。
        """
        print("--- [技术策略] 正在计算技术评分 ---")
        scored_stocks = []
        
        for idx, stock in enumerate(stock_list):
            print(f"  分析: {stock['name']} ({stock['code']}) [{idx + 1}/{len(stock_list)}]")
            
            try:
                stock_data = self.fetcher.get_stock_data(stock['code'], self.config['analysis_period'])
                if stock_data.empty or len(stock_data) < self.config.get('min_data_days', 30):
                    print(f"    数据量不足，跳过。")
                    continue
                
                score = self.scorer.calculate_score(stock_data)
                
                if score >= self.config['min_score']:
                    reasons = self.scorer.get_signal_reasons(stock_data)
                    current_price = stock_data['close'].iloc[-1]
                    
                    scored_stocks.append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'score': round(score, 1),
                        'current_price': round(current_price, 2),
                        'reasons': reasons,
                        'market_cap': stock['market_cap'],
                        'recent_gain': round(stock['recent_gain'], 2)
                    })
                    print(f"    => 评分: {score:.1f} (入选), 推荐理由: {', '.join(reasons)}")
                else:
                    print(f"    => 评分: {score:.1f} (低于阈值 {self.config['min_score']})")
                    
            except Exception as e:
                print(f"    分析出错: {e}")
                continue
            
            time.sleep(self.config.get('api_call_delay', 0.1))

        return scored_stocks

    def run_selection(self, all_stocks=None, for_date=None):
        """
        执行技术分析选股策略的主函数。
        - for_date: 如果提供，则为回测模式，在该日期点上运行策略。
        - all_stocks: 回测时提供，避免重复获取。
        """
        if for_date:
            print(f"\n--- [技术策略] 回测日期: {for_date.strftime('%Y-%m-%d')} ---")
        else:
            print(f"\n{'='*20} 开始执行技术分析选股策略 {'='*20}")
        
        start_time = datetime.now()
        
        # 1. 基础筛选
        # 在回测模式下，我们使用传入的股票池，否则实时获取
        stock_list = all_stocks if all_stocks is not None else self.fetcher.get_stock_list()
        filtered_list = self._filter_basic_criteria(stock_list)
        if not filtered_list:
            print("没有股票通过基础筛选，策略执行结束。")
            return []
            
        # 2. 技术评分
        scored_list = self._calculate_stock_scores(filtered_list)
        if not scored_list:
            print("没有股票达到技术评分标准，策略执行结束。")
            return []
            
        # 3. 排序并选取前N名
        top_stocks = sorted(
            scored_list, 
            key=lambda x: x['score'], 
            reverse=True
        )[:self.config['max_stocks']]
        
        # 4. 在非回测模式下，保存和打印结果
        if not for_date:
            self.save_results(top_stocks, self.config)
            self.print_results(top_stocks)
            
            end_time = datetime.now()
            print(f"策略执行完毕，总耗时: {end_time - start_time}")
            print(f"{'='*60}\n")
        
        return top_stocks 