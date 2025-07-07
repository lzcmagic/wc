import os
import json
from datetime import datetime
import time

from data_fetcher import StockDataFetcher
from core.config import config

class BaseSelector:
    """
    选股器基类，封装通用逻辑。
    - 初始化数据获取器和配置
    - 定义选股主流程框架
    - 提供通用的结果保存和打印方法
    """
    def __init__(self, strategy_name, strategy_config):
        self.strategy_name = strategy_name
        self.config = strategy_config
        self.fetcher = StockDataFetcher(config=config.DATA_FETCHER_CONFIG)
        self.results_dir = 'results'
        self.today_str = datetime.now().strftime('%Y-%m-%d')

        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def run_selection(self):
        """选股主流程模板"""
        print(f"🚀 开始执行 [{self.strategy_name}] 策略 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        try:
            # 1. 获取候选股票列表
            candidate_stocks = self._get_candidate_stocks()
            if not candidate_stocks:
                print("ℹ️ 没有获取到候选股票，任务结束。")
                return []

            # 2. 对候选股票进行评分
            scored_stocks = self._score_stocks(candidate_stocks)
            if not scored_stocks:
                print("ℹ️ 没有符合评分要求的股票，任务结束。")
                return []

            # 3. 按评分排序并筛选最终结果
            final_stocks = self._filter_and_sort(scored_stocks)
            
            # 4. 保存并打印结果
            self._save_results(final_stocks)
            self._print_results(final_stocks)

            print("=" * 60)
            print(f"✅ [{self.strategy_name}] 策略执行完成，推荐 {len(final_stocks)} 只股票。")
            
            return final_stocks

        except Exception as e:
            print(f"❌ 在执行策略 [{self.strategy_name}] 过程中发生严重错误: {e}")
            return []

    def _get_candidate_stocks(self):
        """
        获取候选股票列表。
        这是一个抽象方法，需要由子类根据具体策略实现。
        例如，可以实现基础的市值、名称筛选。
        """
        raise NotImplementedError("子类必须实现 `_get_candidate_stocks` 方法")

    def _score_stocks(self, candidate_stocks):
        """
        为候选股票列表打分。
        这是一个抽象方法，需要由子类根据具体策略实现。
        """
        raise NotImplementedError("子类必须实现 `_score_stocks` 方法")

    def _filter_and_sort(self, scored_stocks):
        """根据评分和配置对股票进行最终排序和筛选"""
        # 按分数从高到低排序
        sorted_stocks = sorted(scored_stocks, key=lambda x: x['score'], reverse=True)
        
        # 根据配置中的 max_stocks 截取最终列表
        max_stocks = self.config.get('filter', {}).get('max_stocks', 10)
        return sorted_stocks[:max_stocks]

    def _save_results(self, stocks):
        """将选股结果保存为JSON文件"""
        filename = f"{self.results_dir}/{self.strategy_name}_selection_{self.today_str}.json"
        
        result_data = {
            'strategy_name': self.strategy_name,
            'date': self.today_str,
            'timestamp': datetime.now().isoformat(),
            'config_used': self.config,
            'summary': {
                'total_recommended': len(stocks),
                'avg_score': round(sum(s['score'] for s in stocks) / len(stocks), 1) if stocks else 0,
            },
            'stocks': stocks,
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            print(f"\n💾 结果已保存至: {filename}")
        except Exception as e:
            print(f"❌ 保存结果文件失败: {e}")

    def _print_results(self, stocks):
        """在控制台打印选股结果"""
        if not stocks:
            print("\nℹ️ 今日无任何股票推荐。")
            return
        
        print(f"\n📊 [{self.strategy_name}] 策略选股结果 - {self.today_str}")
        print("-" * 60)
        
        for i, stock in enumerate(stocks, 1):
            medal = ""
            if i == 1: medal = "🥇"
            elif i == 2: medal = "🥈"
            elif i == 3: medal = "🥉"
            else: medal = f"#{i:<2}"

            details = [
                f"代码: {stock.get('code', 'N/A')}",
                f"价格: ¥{stock.get('current_price', 0):.2f}",
                f"市值: {stock.get('market_cap', 0) / 100000000:.1f}亿",
            ]
            
            print(f"\n{medal} {stock.get('name', '未知股票')} - 综合评分: {stock.get('score', 0):.1f}/100")
            print(f"   {' | '.join(details)}")
            if stock.get('reasons'):
                print(f"   推荐理由: {' + '.join(stock.get('reasons', []))}")

        print("\n" + "=" * 60)
        print("⚠️  风险提示: 本推荐仅为量化分析结果，不构成任何投资建议。")
        print("   股市有风险，投资需谨慎，请结合基本面和市场情况做出决策。")

    def _rate_limit_delay(self):
        """简单的请求延迟，避免过于频繁地请求API"""
        time.sleep(self.fetcher.config.get('request_delay', 0.1)) 