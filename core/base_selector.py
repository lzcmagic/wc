import os
import json
from datetime import datetime
import time
import pandas as pd
from tqdm import tqdm
import numpy as np
import concurrent.futures

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

        # 4. 获取实时数据并丰富结果
        final_selection = self._enrich_results_with_realtime_data(final_selection)

        print(f"✅ 成功选出 {len(final_selection)} 只股票。")
        self.save_results(final_selection, for_date)
        self.print_results(final_selection, for_date)
        return final_selection

    def _filter_by_market_cap(self, df):
        """根据配置中的市值要求过滤股票"""
        min_cap = self.config.get('min_market_cap')
        max_cap = self.config.get('max_market_cap')
        
        # 使用 'market_cap' (流通市值) 进行筛选
        # 注意: data_fetcher 中的预筛选使用的是 'total_market_cap' (总市值)
        if 'market_cap' not in df.columns:
            return df
            
        original_count = len(df)
        
        if min_cap is not None:
            df = df[df['market_cap'] >= min_cap]
        
        if max_cap is not None:
            df = df[df['market_cap'] <= max_cap]
            
        if len(df) < original_count:
            print(f"   - 应用策略专属市值过滤后剩余: {len(df)} 只")
            
        return df

    def _score_single_stock(self, stock_info, for_date=None):
        """
        为单只股票评分。此方法将被并发调用。
        :param stock_info: 包含 'code', 'name', 'market_cap' 的元组或字典
        :param for_date: 回测日期
        :return: 包含评分结果的字典，如果失败则返回 None
        """
        stock_code, stock_name, market_cap = stock_info['code'], stock_info['name'], stock_info.get('market_cap', 0)
        period = self.config.get('period', 120)

        stock_data = self.fetcher.get_stock_data(stock_code, period=period, end_date=for_date)

        if stock_data is None or stock_data.empty or len(stock_data) < period / 2:
            return None
        
        # 将股票代码添加到DataFrame中，以便后续步骤（如综合策略）可以使用
        stock_data['code_in_df'] = stock_code

        # --- 移除重复的指标计算 ---
        # 指标计算的责任完全交给具体的策略类中的 _apply_strategy 方法，
        # 这也解决了 comprehensive 策略因为缺少 'indicators' 键而导致的 KeyError。
        # stock_data_with_indicators = calculate_indicators(stock_data, self.config.get('indicators', []))
        
        score, reasons = self._apply_strategy(stock_data)

        if score > 0:
            return {
                'code': stock_code,
                'name': stock_name,
                'score': score,
                'reasons': reasons,
                'price': stock_data.iloc[-1]['close'],
                'change_pct': stock_data.iloc[-1].get('change_pct', 0.0),
                'market_cap': market_cap
            }
        return None

    def _score_stocks(self, candidate_stocks, for_date=None):
        """为候选股票评分 (并发版本)"""
        results = []
        total = len(candidate_stocks)
        # 从配置或默认值获取并发线程数
        max_workers = self.config.get('max_workers', 10)

        print(f"\n使用 {max_workers} 个线程，为 {total} 只候选股票进行并发评分...")
        
        # 将DataFrame转换为字典列表以便传递给并发任务
        tasks = [row for index, row in candidate_stocks.iterrows()]

        with tqdm(total=total, desc=f"{self.strategy_name} 评分进度") as pbar:
            # 使用ThreadPoolExecutor进行并发处理
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 使用 functools.partial 来固定 for_date 参数
                from functools import partial
                score_func = partial(self._score_single_stock, for_date=for_date)
                
                # executor.map 会按顺序返回结果
                for result in executor.map(score_func, tasks):
                    if result:
                        results.append(result)
                    pbar.update(1) # 每次完成一个任务（无论成功失败）都更新进度条

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
        """将选股结果打印到控制台"""
        if not results:
            return
            
        date_str = (for_date or datetime.now()).strftime('%Y-%m-%d')
        
        try:
            from rich.console import Console
            from rich.table import Table
        except ImportError:
            print("请安装 'rich' 库 (`pip install rich`) 以获得更好的表格输出效果。")
            self._print_results_fallback(results, date_str)
            return

        table = Table(title=f"策略选股结果 ({date_str})", show_header=True, header_style="bold magenta")
        table.add_column("序号", style="dim", width=4)
        table.add_column("代码", justify="left")
        table.add_column("名称", justify="left")
        table.add_column("得分", justify="right")
        table.add_column("价格", justify="right")
        table.add_column("涨跌幅", justify="right")
        table.add_column("市值(亿)", justify="right")
        table.add_column("推荐理由", justify="left", min_width=30)

        for i, stock in enumerate(results, 1):
            market_cap_in_bil = stock.get('market_cap', 0) / 1e8
            change_pct = stock.get('change_pct', 0)
            
            # 根据涨跌幅设置颜色
            if change_pct > 0:
                change_style = "bold red"
                change_str = f"+{change_pct:.2f}%"
            elif change_pct < 0:
                change_style = "bold green"
                change_str = f"{change_pct:.2f}%"
            else:
                change_style = ""
                change_str = "0.00%"

            table.add_row(
                str(i),
                stock['code'],
                stock['name'],
                f"{stock['score']:.2f}",
                f"{stock.get('price', 0):.2f}",
                f"[{change_style}]{change_str}[/{change_style}]",
                f"{market_cap_in_bil:.1f}",
                ' | '.join(stock['reasons'])
            )

        console = Console()
        console.print(table)
        console.print("⚠️  [bold yellow]风险提示[/bold yellow]: 本结果仅为量化分析，不构成投资建议。")

    def _print_results_fallback(self, results, date_str):
        """在没有 rich 库时的备用打印方法"""
        print(f"\n📊 [{self.strategy_name}] 策略选股结果 - {date_str}")
        print("="*100)
        print(f"{'序号':<4}{'代码':<10}{'名称':<10}{'得分':<8}{'价格':<10}{'涨跌幅':<10}{'市值(亿)':<12}{'推荐理由'}")
        print("-"*100)
        for i, stock in enumerate(results, 1):
            market_cap_in_bil = stock.get('market_cap', 0) / 1e8
            change_pct_str = f"{stock.get('change_pct', 0):+.2f}%"
            print(f"{i:<4}{stock['code']:<10}{stock['name']:<10}{stock['score']:<8.2f}"
                  f"{stock.get('price', 0):<10.2f}{change_pct_str:<10}{market_cap_in_bil:<12.1f}"
                  f"{' | '.join(stock['reasons'])}")
        print("="*100)
        print("⚠️  风险提示: 本结果仅为量化分析，不构成投资建议。")

    def _rate_limit_delay(self):
        """简单的请求延迟，避免过于频繁地请求API"""
        time.sleep(self.fetcher.config.get('request_delay', 0.1))

    def _enrich_results_with_realtime_data(self, final_selection):
        """使用实时行情数据丰富最终结果"""
        if not final_selection:
            return []
            
        print("\n enriching results with real time data...")
        stock_codes = [s['code'] for s in final_selection]
        realtime_quotes = self.fetcher.get_realtime_quotes(stock_codes)
        
        if not realtime_quotes:
            print("   - 实时行情获取失败，部分数据将使用旧数据。")
            return final_selection

        for stock in final_selection:
            quote = realtime_quotes.get(stock['code'])
            if quote:
                stock['price'] = quote.get('price', stock['price'])
                stock['change_pct'] = quote.get('change_pct', stock.get('change_pct', 0))
        
        return final_selection 