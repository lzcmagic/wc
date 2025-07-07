#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业绩跟踪系统 - 智能投资业绩分析
支持收益分析、策略回测、业绩归因、基准对比、风险调整收益
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Tuple, Optional
import json
import os
from dataclasses import dataclass, asdict
import sqlite3
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """业绩指标类"""
    period: str
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades_count: int
    benchmark_return: float
    alpha: float
    beta: float
    information_ratio: float
    tracking_error: float

@dataclass
class TradeRecord:
    """交易记录类"""
    date: str
    code: str
    name: str
    action: str  # BUY, SELL
    quantity: int
    price: float
    amount: float
    fee: float
    profit_loss: float
    holding_days: int
    strategy: str

@dataclass
class PortfolioSnapshot:
    """投资组合快照"""
    date: str
    total_value: float
    total_cost: float
    cash: float
    positions: Dict[str, Dict]
    daily_return: float
    cumulative_return: float

class PerformanceDatabase:
    """业绩数据库管理"""
    
    def __init__(self, db_path: str = "performance.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建每日净值表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_nav (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                nav REAL NOT NULL,
                total_value REAL NOT NULL,
                cash REAL DEFAULT 0,
                daily_return REAL DEFAULT 0,
                cumulative_return REAL DEFAULT 0,
                benchmark_nav REAL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                fee REAL DEFAULT 0,
                profit_loss REAL DEFAULT 0,
                holding_days INTEGER DEFAULT 0,
                strategy TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建策略回测表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                final_value REAL NOT NULL,
                total_return REAL NOT NULL,
                annualized_return REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                sharpe_ratio REAL NOT NULL,
                win_rate REAL NOT NULL,
                trades_count INTEGER NOT NULL,
                config TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_daily_nav(self, date: str, nav: float, total_value: float, 
                      cash: float = 0, daily_return: float = 0, 
                      cumulative_return: float = 0, benchmark_nav: float = 1):
        """保存每日净值"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO daily_nav 
                (date, nav, total_value, cash, daily_return, cumulative_return, benchmark_nav)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date, nav, total_value, cash, daily_return, cumulative_return, benchmark_nav))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存每日净值失败: {e}")
    
    def get_nav_history(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取净值历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if start_date and end_date:
                query = '''
                    SELECT * FROM daily_nav 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                '''
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            else:
                query = 'SELECT * FROM daily_nav ORDER BY date'
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
        except Exception as e:
            logger.error(f"获取净值历史失败: {e}")
            return pd.DataFrame()
    
    def save_trade_record(self, trade: TradeRecord):
        """保存交易记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trade_records 
                (date, code, name, action, quantity, price, amount, fee, 
                 profit_loss, holding_days, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trade.date, trade.code, trade.name, trade.action, 
                  trade.quantity, trade.price, trade.amount, trade.fee,
                  trade.profit_loss, trade.holding_days, trade.strategy))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存交易记录失败: {e}")

class BenchmarkManager:
    """基准管理器"""
    
    def __init__(self):
        self.benchmark_cache = {}
    
    def get_benchmark_data(self, benchmark: str = "000300", 
                          start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取基准指数数据"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            # 获取沪深300指数数据
            if benchmark == "000300":
                df = ak.stock_zh_index_daily(symbol="sh000300")
            elif benchmark == "000001":
                df = ak.stock_zh_index_daily(symbol="sh000001")  # 上证指数
            elif benchmark == "399001":
                df = ak.stock_zh_index_daily(symbol="sz399001")  # 深证成指
            else:
                df = ak.stock_zh_index_daily(symbol="sh000300")  # 默认沪深300
            
            if df.empty:
                return pd.DataFrame()
            
            # 标准化列名
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 筛选日期范围
            if start_date:
                start = pd.to_datetime(start_date)
                df = df[df['date'] >= start]
            
            if end_date:
                end = pd.to_datetime(end_date)
                df = df[df['date'] <= end]
            
            # 计算收益率
            df['return'] = df['close'].pct_change()
            df['cumulative_return'] = (1 + df['return']).cumprod() - 1
            
            return df
        
        except Exception as e:
            logger.error(f"获取基准数据失败: {e}")
            return pd.DataFrame()

class PerformanceAnalyzer:
    """业绩分析器"""
    
    def __init__(self):
        self.db = PerformanceDatabase()
        self.benchmark_manager = BenchmarkManager()
    
    def calculate_performance_metrics(self, returns: pd.Series, 
                                    benchmark_returns: pd.Series = None,
                                    risk_free_rate: float = 0.03) -> PerformanceMetrics:
        """计算业绩指标"""
        
        if len(returns) == 0:
            return PerformanceMetrics(
                period="N/A", total_return=0, annualized_return=0, volatility=0,
                sharpe_ratio=0, sortino_ratio=0, max_drawdown=0, calmar_ratio=0,
                win_rate=0, avg_win=0, avg_loss=0, profit_factor=0, trades_count=0,
                benchmark_return=0, alpha=0, beta=0, information_ratio=0, tracking_error=0
            )
        
        # 基本收益指标
        total_return = (1 + returns).prod() - 1
        periods_per_year = 252  # 交易日
        years = len(returns) / periods_per_year
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # 波动率
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        # 夏普比率
        excess_returns = returns - risk_free_rate / periods_per_year
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year) if excess_returns.std() > 0 else 0
        
        # 索提诺比率
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(periods_per_year)
        sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # 卡玛比率
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # 胜率和盈亏比
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0
        avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
        avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0
        profit_factor = (positive_returns.sum() / abs(negative_returns.sum())) if negative_returns.sum() != 0 else 0
        
        # 与基准对比指标
        benchmark_return = 0
        alpha = 0
        beta = 0
        information_ratio = 0
        tracking_error = 0
        
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            benchmark_return = (1 + benchmark_returns).prod() - 1
            
            # 计算Beta
            covariance = np.cov(returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            
            # 计算Alpha
            alpha = annualized_return - (risk_free_rate + beta * (benchmark_returns.mean() * periods_per_year - risk_free_rate))
            
            # 信息比率和跟踪误差
            active_returns = returns - benchmark_returns
            tracking_error = active_returns.std() * np.sqrt(periods_per_year)
            information_ratio = active_returns.mean() / active_returns.std() * np.sqrt(periods_per_year) if active_returns.std() > 0 else 0
        
        return PerformanceMetrics(
            period=f"{len(returns)}天",
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            trades_count=len(returns),
            benchmark_return=benchmark_return,
            alpha=alpha,
            beta=beta,
            information_ratio=information_ratio,
            tracking_error=tracking_error
        )
    
    def analyze_period_performance(self, period: str = "1Y") -> Dict[str, Any]:
        """分析特定期间业绩"""
        
        # 计算日期范围
        end_date = datetime.now()
        if period == "1M":
            start_date = end_date - timedelta(days=30)
        elif period == "3M":
            start_date = end_date - timedelta(days=90)
        elif period == "6M":
            start_date = end_date - timedelta(days=180)
        elif period == "1Y":
            start_date = end_date - timedelta(days=365)
        elif period == "2Y":
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=365)
        
        # 获取净值数据
        nav_df = self.db.get_nav_history(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if nav_df.empty:
            return {"error": "没有足够的历史数据"}
        
        # 计算收益率
        returns = nav_df['daily_return'].fillna(0)
        
        # 获取基准数据
        benchmark_df = self.benchmark_manager.get_benchmark_data(
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d')
        )
        
        benchmark_returns = None
        if not benchmark_df.empty:
            # 对齐日期
            benchmark_df['date_str'] = benchmark_df['date'].dt.strftime('%Y-%m-%d')
            nav_df['date_str'] = nav_df['date'].dt.strftime('%Y-%m-%d')
            
            merged = nav_df.merge(benchmark_df[['date_str', 'return']], 
                                on='date_str', how='inner', suffixes=('', '_bench'))
            
            if not merged.empty:
                benchmark_returns = merged['return'].fillna(0)
                returns = merged['daily_return'].fillna(0)
        
        # 计算业绩指标
        metrics = self.calculate_performance_metrics(returns, benchmark_returns)
        
        return {
            "period": period,
            "metrics": metrics,
            "nav_data": nav_df,
            "benchmark_data": benchmark_df
        }
    
    def generate_performance_report(self, periods: List[str] = None) -> str:
        """生成业绩报告"""
        
        if periods is None:
            periods = ["1M", "3M", "6M", "1Y"]
        
        report = f"""
📈 投资组合业绩分析报告
{'='*60}
📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        # 分析各个时间段
        period_results = {}
        for period in periods:
            result = self.analyze_period_performance(period)
            if "error" not in result:
                period_results[period] = result
        
        if not period_results:
            return report + "❌ 暂无足够的历史数据生成报告"
        
        # 业绩概览表格
        report += "📊 业绩概览:\n"
        report += f"{'期间':<8} {'总收益率':<10} {'年化收益':<10} {'最大回撤':<10} {'夏普比率':<10} {'基准收益':<10}\n"
        report += "-" * 70 + "\n"
        
        for period, result in period_results.items():
            metrics = result["metrics"]
            report += f"{period:<8} {metrics.total_return:>8.2%} {metrics.annualized_return:>8.2%} {metrics.max_drawdown:>8.2%} {metrics.sharpe_ratio:>8.2f} {metrics.benchmark_return:>8.2%}\n"
        
        # 详细分析 (以1年期为例)
        if "1Y" in period_results:
            metrics = period_results["1Y"]["metrics"]
            
            report += f"\n📋 详细分析 (近1年):\n"
            report += f"   • 总收益率: {metrics.total_return:.2%}\n"
            report += f"   • 年化收益率: {metrics.annualized_return:.2%}\n"
            report += f"   • 年化波动率: {metrics.volatility:.2%}\n"
            report += f"   • 最大回撤: {metrics.max_drawdown:.2%}\n"
            report += f"   • 夏普比率: {metrics.sharpe_ratio:.3f}\n"
            report += f"   • 索提诺比率: {metrics.sortino_ratio:.3f}\n"
            report += f"   • 卡玛比率: {metrics.calmar_ratio:.3f}\n"
            report += f"   • 胜率: {metrics.win_rate:.1%}\n"
            report += f"   • 盈亏比: {metrics.avg_win/metrics.avg_loss:.2f}" if metrics.avg_loss > 0 else f"   • 盈亏比: N/A\n"
            
            report += f"\n🎯 与基准对比 (沪深300):\n"
            report += f"   • 基准收益率: {metrics.benchmark_return:.2%}\n"
            report += f"   • 超额收益: {metrics.total_return - metrics.benchmark_return:.2%}\n"
            report += f"   • Alpha: {metrics.alpha:.2%}\n"
            report += f"   • Beta: {metrics.beta:.3f}\n"
            report += f"   • 信息比率: {metrics.information_ratio:.3f}\n"
            report += f"   • 跟踪误差: {metrics.tracking_error:.2%}\n"
        
        # 业绩评级
        if "1Y" in period_results:
            rating = self._calculate_performance_rating(period_results["1Y"]["metrics"])
            report += f"\n⭐ 业绩评级: {rating}\n"
        
        # 改进建议
        report += self._generate_improvement_suggestions(period_results)
        
        return report
    
    def _calculate_performance_rating(self, metrics: PerformanceMetrics) -> str:
        """计算业绩评级"""
        score = 0
        
        # 收益率评分 (40分)
        if metrics.annualized_return > 0.20:
            score += 40
        elif metrics.annualized_return > 0.15:
            score += 35
        elif metrics.annualized_return > 0.10:
            score += 30
        elif metrics.annualized_return > 0.05:
            score += 25
        elif metrics.annualized_return > 0:
            score += 20
        else:
            score += 10
        
        # 风险控制评分 (30分)
        if metrics.max_drawdown < 0.05:
            score += 30
        elif metrics.max_drawdown < 0.10:
            score += 25
        elif metrics.max_drawdown < 0.15:
            score += 20
        elif metrics.max_drawdown < 0.20:
            score += 15
        else:
            score += 10
        
        # 夏普比率评分 (20分)
        if metrics.sharpe_ratio > 2:
            score += 20
        elif metrics.sharpe_ratio > 1.5:
            score += 18
        elif metrics.sharpe_ratio > 1:
            score += 15
        elif metrics.sharpe_ratio > 0.5:
            score += 12
        else:
            score += 8
        
        # 相对基准评分 (10分)
        excess_return = metrics.total_return - metrics.benchmark_return
        if excess_return > 0.05:
            score += 10
        elif excess_return > 0:
            score += 8
        else:
            score += 5
        
        # 评级划分
        if score >= 90:
            return "🌟🌟🌟🌟🌟 卓越"
        elif score >= 80:
            return "🌟🌟🌟🌟 优秀"
        elif score >= 70:
            return "🌟🌟🌟 良好"
        elif score >= 60:
            return "🌟🌟 一般"
        else:
            return "🌟 需要改进"
    
    def _generate_improvement_suggestions(self, period_results: Dict) -> str:
        """生成改进建议"""
        
        suggestions = "\n💡 改进建议:\n"
        
        if "1Y" not in period_results:
            return suggestions + "   • 需要更多历史数据进行分析\n"
        
        metrics = period_results["1Y"]["metrics"]
        
        # 收益相关建议
        if metrics.annualized_return < 0.05:
            suggestions += "   • 收益率偏低，考虑调整投资策略或增加成长性资产配置\n"
        
        # 风险相关建议
        if metrics.max_drawdown > 0.15:
            suggestions += "   • 最大回撤较大，建议加强风险控制和仓位管理\n"
        
        if metrics.volatility > 0.25:
            suggestions += "   • 组合波动率较高，考虑增加低风险资产平衡\n"
        
        # 夏普比率建议
        if metrics.sharpe_ratio < 1:
            suggestions += "   • 夏普比率偏低，需要在保持收益的同时降低风险\n"
        
        # 胜率建议
        if metrics.win_rate < 0.5:
            suggestions += "   • 胜率偏低，建议提高选股质量和择时能力\n"
        
        # 相对基准建议
        if metrics.total_return < metrics.benchmark_return:
            suggestions += "   • 跑输基准，考虑是否应该采用指数化投资策略\n"
        
        if metrics.tracking_error > 0.15:
            suggestions += "   • 跟踪误差较大，投资风格与基准差异明显\n"
        
        # Beta相关建议
        if metrics.beta > 1.5:
            suggestions += "   • Beta值较高，组合系统性风险较大，建议适度降低\n"
        elif metrics.beta < 0.5:
            suggestions += "   • Beta值较低，可能错失市场上涨机会\n"
        
        return suggestions
    
    def export_performance_data(self, filename: str = None) -> str:
        """导出业绩数据"""
        
        if filename is None:
            filename = f"performance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 获取所有时间段的分析结果
        periods = ["1M", "3M", "6M", "1Y", "2Y"]
        export_data = {
            "export_time": datetime.now().isoformat(),
            "periods": {}
        }
        
        for period in periods:
            result = self.analyze_period_performance(period)
            if "error" not in result:
                # 转换为可序列化的格式
                metrics_dict = asdict(result["metrics"])
                export_data["periods"][period] = {
                    "metrics": metrics_dict,
                    "data_points": len(result["nav_data"])
                }
        
        # 获取净值历史
        nav_df = self.db.get_nav_history()
        if not nav_df.empty:
            export_data["nav_history"] = nav_df.to_dict('records')
        
        # 保存到文件
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"业绩数据已导出: {filename}")
            return filename
        except Exception as e:
            logger.error(f"导出业绩数据失败: {e}")
            return ""

def main():
    """主程序"""
    print("📈 投资组合业绩跟踪系统")
    print("="*50)
    
    analyzer = PerformanceAnalyzer()
    
    while True:
        print("\n请选择功能:")
        print("1. 📊 生成业绩报告")
        print("2. 📈 分析特定期间")
        print("3. 📋 查看净值历史")
        print("4. 💾 导出业绩数据")
        print("5. 🔄 更新净值数据")
        print("6. 📉 基准对比分析")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == "1":
            print("📊 正在生成业绩报告...")
            report = analyzer.generate_performance_report()
            print(report)
            
            # 询问是否保存
            save_choice = input("\n是否保存报告到文件? (y/n): ").lower()
            if save_choice == 'y':
                filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"✅ 报告已保存: {filename}")
        
        elif choice == "2":
            print("请选择分析期间:")
            print("1. 最近1个月")
            print("2. 最近3个月")
            print("3. 最近6个月")
            print("4. 最近1年")
            print("5. 最近2年")
            
            period_choice = input("请选择 (1-5): ").strip()
            period_map = {"1": "1M", "2": "3M", "3": "6M", "4": "1Y", "5": "2Y"}
            
            if period_choice in period_map:
                period = period_map[period_choice]
                print(f"📈 分析{period}期间业绩...")
                
                result = analyzer.analyze_period_performance(period)
                if "error" in result:
                    print(f"❌ {result['error']}")
                else:
                    metrics = result["metrics"]
                    print(f"\n📊 {period}期间业绩:")
                    print(f"   总收益率: {metrics.total_return:.2%}")
                    print(f"   年化收益: {metrics.annualized_return:.2%}")
                    print(f"   最大回撤: {metrics.max_drawdown:.2%}")
                    print(f"   夏普比率: {metrics.sharpe_ratio:.3f}")
                    print(f"   胜率: {metrics.win_rate:.1%}")
                    if metrics.benchmark_return != 0:
                        print(f"   基准收益: {metrics.benchmark_return:.2%}")
                        print(f"   超额收益: {metrics.total_return - metrics.benchmark_return:.2%}")
            else:
                print("❌ 无效选择")
        
        elif choice == "3":
            print("📋 查看净值历史...")
            nav_df = analyzer.db.get_nav_history()
            
            if nav_df.empty:
                print("暂无净值数据")
            else:
                print(f"\n净值数据 (最近10条):")
                recent_data = nav_df.tail(10)
                print(f"{'日期':<12} {'净值':<8} {'日收益率':<10} {'累计收益率':<12}")
                print("-" * 50)
                
                for _, row in recent_data.iterrows():
                    print(f"{row['date'].strftime('%Y-%m-%d'):<12} {row['nav']:<8.4f} {row['daily_return']:>8.2%} {row['cumulative_return']:>10.2%}")
                
                print(f"\n📊 统计信息:")
                print(f"   数据点数: {len(nav_df)}")
                print(f"   开始日期: {nav_df['date'].min().strftime('%Y-%m-%d')}")
                print(f"   结束日期: {nav_df['date'].max().strftime('%Y-%m-%d')}")
                print(f"   最新净值: {nav_df['nav'].iloc[-1]:.4f}")
        
        elif choice == "4":
            print("💾 导出业绩数据...")
            filename = analyzer.export_performance_data()
            if filename:
                print(f"✅ 数据已导出: {filename}")
            else:
                print("❌ 导出失败")
        
        elif choice == "5":
            print("🔄 更新净值数据功能需要连接实际交易系统")
            print("💡 提示: 在实际使用中，这里会自动从券商API获取最新的组合净值")
        
        elif choice == "6":
            print("📉 基准对比分析...")
            # 这里可以实现更详细的基准对比功能
            print("💡 功能开发中...")
        
        elif choice == "0":
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 