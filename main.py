#!/usr/bin/env python3
"""
个人A股选股系统 - 主程序入口
支持定时任务和命令行操作
"""

import argparse
import schedule
import time
from datetime import datetime

# 动态导入策略
from strategies.technical_strategy import TechnicalStrategySelector
from strategies.comprehensive_strategy import ComprehensiveStrategySelector

# 策略注册表
STRATEGY_MAP = {
    'technical': TechnicalStrategySelector,
    'comprehensive': ComprehensiveStrategySelector
}

def run_selection(strategy_name):
    if strategy_name not in STRATEGY_MAP:
        print(f"错误：未知的策略 '{strategy_name}'。可用策略: {list(STRATEGY_MAP.keys())}")
        return
    
    strategy_class = STRATEGY_MAP[strategy_name]
    selector = strategy_class()
    selector.run_selection()

def run_backtest(strategy_name, start_date, end_date):
    """运行回测"""
    from core.backtester import BacktestEngine # 延迟导入，因为不是每次都用

    if strategy_name not in STRATEGY_MAP:
        print(f"错误：未知的策略 '{strategy_name}'。可用策略: {list(STRATEGY_MAP.keys())}")
            return
        
    strategy_class = STRATEGY_MAP[strategy_name]
    strategy_instance = strategy_class()
    
    engine = BacktestEngine(
        strategy=strategy_instance,
        start_date=start_date,
        end_date=end_date
    )
    engine.run()

def schedule_job(strategy_name, run_time_str):
    """根据配置定时执行任务"""
    if strategy_name not in STRATEGY_MAP:
        print(f"❌ 错误: 无法为未知策略 '{strategy_name}' 设置定时任务。")
            return
        
    print(f"⏰ 已设置定时任务，将在每日 {run_time_str} 使用 [{strategy_name}] 策略执行选股。")
    print("   (按 Ctrl+C 停止)")
    
    # 使用 schedule 库设置每日任务
    schedule.every().day.at(run_time_str).do(run_selection, strategy_name=strategy_name)

            while True:
                schedule.run_pending()
        time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="A股智能选股工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    subparsers.required = True

    # 'select' 命令
    select_parser = subparsers.add_parser('select', help='执行选股')
    select_parser.add_argument(
        '--strategy',
        '-s',
        type=str,
        default='technical',
        choices=STRATEGY_MAP.keys(),
        help=f"选择要执行的选股策略 (默认: 'technical')"
    )

    # 'backtest' 命令
    backtest_parser = subparsers.add_parser('backtest', help='执行策略回测')
    backtest_parser.add_argument(
        '--strategy',
        '-s',
        type=str,
        required=True,
        choices=STRATEGY_MAP.keys(),
        help="选择要回测的选股策略"
    )
    backtest_parser.add_argument(
        '--start',
        required=True,
        help="回测开始日期 (格式: YYYY-MM-DD)"
    )
    backtest_parser.add_argument(
        '--end',
        required=True,
        help="回测结束日期 (格式: YYYY-MM-DD)"
    )

    args = parser.parse_args()
    
    print("=============================================")
    print(f"     A股智能选股系统 v3.0     ")
    print("=============================================")

    if args.command == 'select':
        run_selection(args.strategy)
    elif args.command == 'backtest':
        run_backtest(args.strategy, args.start, args.end)
    elif args.command == 'schedule':
        try:
            schedule_job(args.strategy, args.time)
        except KeyboardInterrupt:
            print("\n👋 定时任务已停止。")

if __name__ == '__main__':
    main() 