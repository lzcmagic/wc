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
from strategies.technical_strategy import TechnicalStrategy
from strategies.comprehensive_strategy import ComprehensiveStrategy

# 策略映射
STRATEGY_MAP = {
    'technical': TechnicalStrategy,
    'comprehensive': ComprehensiveStrategy,
}

def run_job(strategy_name):
    """根据策略名称运行选股任务"""
    if strategy_name not in STRATEGY_MAP:
        print(f"❌ 错误: 未知的策略 '{strategy_name}'。可用策略: {list(STRATEGY_MAP.keys())}")
        return

    print(f"🔷 准备执行策略: {strategy_name}")
    strategy_class = STRATEGY_MAP[strategy_name]
    selector = strategy_class()
    selector.run_selection()

def schedule_job(strategy_name, run_time_str):
    """根据配置定时执行任务"""
    if strategy_name not in STRATEGY_MAP:
        print(f"❌ 错误: 无法为未知策略 '{strategy_name}' 设置定时任务。")
        return

    print(f"⏰ 已设置定时任务，将在每日 {run_time_str} 使用 [{strategy_name}] 策略执行选股。")
    print("   (按 Ctrl+C 停止)")
    
    # 使用 schedule 库设置每日任务
    schedule.every().day.at(run_time_str).do(run_job, strategy_name=strategy_name)

    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="A股智能选股系统")
    
    parser.add_argument(
        'command', 
        choices=['run', 'schedule'], 
        help="要执行的命令: 'run' (立即执行一次) 或 'schedule' (启动定时任务)"
    )
    
    parser.add_argument(
        '--strategy', 
        type=str, 
        default='technical', 
        choices=STRATEGY_MAP.keys(),
        help=f"选择要使用的选股策略 (默认: 'technical')"
    )
    
    parser.add_argument(
        '--time', 
        type=str, 
        default='09:30', 
        help="定时任务的执行时间 (格式: HH:MM)，仅在 'schedule' 命令下有效 (默认: '09:30')"
    )
    
    args = parser.parse_args()

    print("=============================================")
    print(f"     A股智能选股系统 v3.0     ")
    print("=============================================")

    if args.command == 'run':
        run_job(args.strategy)
    elif args.command == 'schedule':
        try:
            schedule_job(args.strategy, args.time)
        except KeyboardInterrupt:
            print("\n👋 定时任务已停止。")

if __name__ == '__main__':
    main()