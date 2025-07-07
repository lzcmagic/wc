import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import StockDataFetcher

class Portfolio:
    """
    投资组合管理器。
    - 跟踪现金、持股。
    - 计算每日市值。
    - 执行调仓指令。
    - 记录资产历史。
    """
    def __init__(self, initial_capital=1000000.0, commission_rate=0.0003):
        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.commission_rate = commission_rate
        self.holdings = {}  # {'code': {'shares': X, 'price': Y}}
        self.history = []

    def get_current_value(self, current_prices):
        """计算当前总资产净值"""
        stock_value = 0.0
        for code, position in self.holdings.items():
            current_price = current_prices.get(code)
            if current_price is not None:
                stock_value += position['shares'] * current_price
            else:
                # 如果某只股票当天没有价格（例如停牌），则按上一日成本价计算
                stock_value += position['shares'] * position['price']
        return self.cash + stock_value

    def rebalance(self, date, target_holdings, current_prices):
        """
        执行调仓操作。
        这是一个简化的实现：在每个调仓日，卖出所有现有持仓，然后将资金平均分配给新的目标持仓。
        """
        # 1. 卖出所有现有持仓
        for code, position in self.holdings.items():
            price = current_prices.get(code)
            if price is not None:
                trade_value = position['shares'] * price
                commission = trade_value * self.commission_rate
                self.cash += trade_value - commission
        self.holdings = {}

        # 2. 将资金平均买入新的目标股票
        if not target_holdings:
            return # 如果没有新的目标，则全仓持有现金

        investment_per_stock = self.cash / len(target_holdings)
        
        for stock in target_holdings:
            code = stock['code']
            price = current_prices.get(code)
            if price is not None and price > 0:
                shares_to_buy = investment_per_stock / price
                trade_value = shares_to_buy * price
                commission = trade_value * self.commission_rate
                
                if self.cash >= trade_value + commission:
                    self.cash -= (trade_value + commission)
                    self.holdings[code] = {'shares': shares_to_buy, 'price': price}
        
        # 记录当日资产
        self.record_history(date, current_prices)

    def record_history(self, date, current_prices):
        """记录当日的资产净值"""
        value = self.get_current_value(current_prices)
        self.history.append({'date': date, 'value': value})


class BacktestEngine:
    """
    回测引擎。
    - 模拟时间流逝。
    - 在每个交易日调用策略，获取交易信号。
    - 指挥 Portfolio 进行调仓。
    - 生成最终的业绩报告。
    """
    def __init__(self, strategy, start_date, end_date, initial_capital=1000000.0):
        self.strategy = strategy
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_capital = initial_capital
        self.portfolio = Portfolio(initial_capital)
        self.fetcher = StockDataFetcher()

    def run(self):
        """执行回测"""
        print("🚀 回测开始...")
        print(f"策略: {self.strategy.strategy_name} | 时间: {self.start_date.date()} to {self.end_date.date()} | 初始资金: ¥{self.initial_capital:,.2f}")
        
        all_trade_days = self.fetcher.get_trade_days(self.start_date, self.end_date)
        
        for current_date in all_trade_days:
            print(f"  -> 模拟交易日: {current_date.strftime('%Y-%m-%d')}")
            
            # 1. 调用策略，获取当日的持仓建议
            # (需要修改策略类以支持历史日期)
            target_stocks = self.strategy.run_selection(for_date=current_date)
            
            # 2. 获取当日所有A股的价格，用于计算市值和执行交易
            current_prices = self.fetcher.get_prices_for_date(target_stocks, current_date)
            
            # 3. 执行调仓
            self.portfolio.rebalance(current_date, target_stocks, current_prices)
            
            # 打印当日资产
            print(f"     当日资产净值: ¥{self.portfolio.history[-1]['value']:,.2f}")

        print("✅ 回测结束。")
        return self.generate_report()

    def generate_report(self):
        """计算关键业绩指标并生成报告"""
        if not self.portfolio.history:
            print("❌ 回测历史为空，无法生成报告。")
            return None

        report = {}
        df = pd.DataFrame(self.portfolio.history).set_index('date')
        
        # 1. 累计收益率
        report['cumulative_return'] = (df['value'].iloc[-1] / self.initial_capital) - 1
        
        # 2. 年化收益率
        days = (df.index[-1] - df.index[0]).days
        report['annualized_return'] = (1 + report['cumulative_return']) ** (365.0 / days) - 1
        
        # 3. 最大回撤
        rolling_max = df['value'].cummax()
        daily_drawdown = df['value'] / rolling_max - 1.0
        report['max_drawdown'] = daily_drawdown.min()
        
        # 4. 夏普比率 (简化版，假设无风险利率为0)
        daily_returns = df['value'].pct_change().dropna()
        report['sharpe_ratio'] = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252)
        
        self.print_report(report)
        return report

    def print_report(self, report):
        """打印回测报告"""
        print("\n" + "="*50)
        print("📊 回测业绩报告")
        print("="*50)
        print(f"  累计收益率: {report['cumulative_return']:>15.2%}")
        print(f"  年化收益率: {report['annualized_return']:>15.2%}")
        print(f"  最大回撤:   {report['max_drawdown']:>15.2%}")
        print(f"  夏普比率:   {report['sharpe_ratio']:>15.2f}")
        print("="*50) 