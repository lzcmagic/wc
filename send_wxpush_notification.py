#!/usr/bin/env python3
"""
WxPusher微信推送通知发送脚本
用于在GitHub Action中发送选股结果微信推送
替换原有的邮件通知功能
"""

import os
import sys
import json
from datetime import datetime
from core.wxpusher_sender import WxPusherSender
from core.env_config import env_config

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python send_wxpush_notification.py <strategy_name> [results_file]")
        print("示例: python send_wxpush_notification.py comprehensive")
        print("示例: python send_wxpush_notification.py technical results/technical_selection_2025-07-08.json")
        sys.exit(1)
    
    strategy_name = sys.argv[1]
    
    # 如果没有指定结果文件，则自动查找
    if len(sys.argv) >= 3:
        results_file = sys.argv[2]
    else:
        # 自动查找当天的结果文件
        today = datetime.now().strftime('%Y-%m-%d')
        results_file = f"results/{strategy_name}_selection_{today}.json"
    
    print(f"📱 准备发送微信推送通知...")
    print(f"   策略: {strategy_name}")
    print(f"   结果文件: {results_file}")
    
    # 检查结果文件是否存在
    if not os.path.exists(results_file):
        print(f"❌ 结果文件不存在: {results_file}")
        sys.exit(1)
    
    # 读取选股结果
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            stocks = json.load(f)
        
        if not stocks:
            print("⚠️ 选股结果为空，跳过推送")
            sys.exit(0)
            
        print(f"📊 读取到 {len(stocks)} 只股票")
        
    except Exception as e:
        print(f"❌ 读取结果文件失败: {e}")
        sys.exit(1)
    
    # 初始化WxPusher发送器
    try:
        sender = WxPusherSender()
        
        if not sender.is_enabled():
            print("❌ WxPusher未启用或配置不完整")
            print("💡 请检查WxPusher配置:")
            print("   - 确保已设置正确的APP_TOKEN和TOPIC_ID")
            print("   - 或者配置极简推送SPT")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ WxPusher初始化失败: {e}")
        sys.exit(1)
    
    # 发送选股结果通知
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        success = sender.send_stock_selection_notification(
            stocks=stocks,
            strategy_name=strategy_name,
            date=today
        )
        
        if success:
            print("✅ 微信推送发送成功！")
            print("📱 请检查您的微信，查看选股结果推送")
            sys.exit(0)
        else:
            print("❌ 微信推送发送失败！")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 发送微信推送时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
